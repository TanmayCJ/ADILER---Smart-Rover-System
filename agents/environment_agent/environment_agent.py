"""Environment agent for rover situational awareness."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List

from agents.shared.llm_client import get_llama_client
from agents.shared.mock_generators import get_mock_generator

logger = logging.getLogger(__name__)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
	return max(lower, min(upper, value))


def _obstacle_risk(obstacles: List[Dict[str, Any]]) -> float:
	if not obstacles:
		return 0.0

	severity = 0.0
	for obstacle in obstacles:
		distance_m = float(obstacle.get("distance_m", 50.0))
		size_m = float(obstacle.get("size_m", 1.0))
		proximity = _clamp((100.0 - distance_m) / 100.0)
		scale = _clamp(size_m / 10.0)
		severity += 0.45 * proximity + 0.55 * scale
	return _clamp(severity / len(obstacles))


def _terrain_risk(terrain_data: Dict[str, Any], wind_data: Dict[str, Any]) -> Dict[str, float]:
	slope_deg = float(terrain_data.get("slope_deg", 0.0))
	roughness = _clamp(float(terrain_data.get("roughness", 0.0)))
	wind_speed = float(wind_data.get("speed_mps", 0.0))
	gust_speed = float(wind_data.get("gust_speed_mps", wind_speed))
	obstacles = terrain_data.get("obstacles", [])

	slope_risk = _clamp(slope_deg / 30.0)
	wind_risk = _clamp(max(wind_speed - 2.0, 0.0) / 13.0)
	gust_risk = _clamp(max(gust_speed - 5.0, 0.0) / 15.0)
	obstacle_risk = _obstacle_risk(obstacles)

	risk_score = _clamp(
		0.32 * slope_risk
		+ 0.24 * roughness
		+ 0.22 * max(wind_risk, gust_risk)
		+ 0.22 * obstacle_risk
	)

	return {
		"risk_score": risk_score,
		"slope_risk": slope_risk,
		"roughness_risk": roughness,
		"wind_risk": max(wind_risk, gust_risk),
		"obstacle_risk": obstacle_risk,
	}


def _danger_recommendation(risk_score: float) -> str:
	if risk_score >= 0.8:
		return "Hold position and request replanning."
	if risk_score >= 0.55:
		return "Proceed cautiously with reduced speed and tighter monitoring."
	return "Traversal is currently acceptable."


def _build_safe_zones(state: Dict[str, Any], risk_score: float) -> List[Dict[str, Any]]:
	rover_position = state.get("rover_position", {})
	latitude = float(rover_position.get("latitude", 0.0))
	longitude = float(rover_position.get("longitude", 0.0))
	offset = 0.01 + (1.0 - risk_score) * 0.01

	return [
		{"lat": latitude + offset, "lon": longitude + offset, "safety_level": _clamp(1.0 - risk_score)},
		{"lat": latitude - offset, "lon": longitude + offset, "safety_level": _clamp(0.9 - risk_score / 2.0)},
	]


def _build_danger_zones(terrain_data: Dict[str, Any], risk_info: Dict[str, float]) -> List[Dict[str, Any]]:
	danger_zones: List[Dict[str, Any]] = []
	obstacles = terrain_data.get("obstacles", [])
	for obstacle in obstacles[:5]:
		danger_zones.append(
			{
				"hazard_type": "obstacle",
				"severity": _clamp((float(obstacle.get("size_m", 1.0)) / 10.0) + (1.0 - float(obstacle.get("distance_m", 50.0)) / 100.0)),
				"location": {
					"lat": terrain_data.get("center_latitude"),
					"lon": terrain_data.get("center_longitude"),
				},
				"recommendation": f"Avoid {obstacle.get('type', 'obstacle')} at {obstacle.get('distance_m', 0):.1f}m",
			}
		)

	if not danger_zones:
		danger_zones.append(
			{
				"hazard_type": "slope",
				"severity": risk_info["slope_risk"],
				"location": {"lat": terrain_data.get("center_latitude"), "lon": terrain_data.get("center_longitude")},
				"recommendation": "No discrete obstacles found; slope and wind are the primary concerns.",
			}
		)

	return danger_zones


def environment_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
	"""Analyze the current environment and produce a hazard map."""
	mock_generator = get_mock_generator()
	llama_client = get_llama_client(model="llama3.1")

	terrain_data = state.get("terrain_data") or mock_generator.generate_mock_terrain_data()
	wind_data = state.get("wind_data") or mock_generator.generate_mock_wind_data()

	risk_info = _terrain_risk(terrain_data, wind_data)
	risk_score = risk_info["risk_score"]

	llm_summary = None
	try:
		prompt = json.dumps(
			{
				"terrain": terrain_data,
				"wind": wind_data,
				"risk_score": risk_score,
				"recommendation": _danger_recommendation(risk_score),
			},
			indent=2,
		)
		llm_summary = llama_client.invoke(
			prompt=prompt,
			system_prompt=(
				"You are the rover environment analyst. Return a short operational summary "
				"focused on hazards, traversability, and what the next agent should do."
			),
			temperature=0.2,
			max_tokens=180,
		)
	except Exception as exc:  # pragma: no cover - defensive logging path
		logger.warning("Environment summary generation failed: %s", exc)

	summary_text = llm_summary or (
		f"Terrain {terrain_data.get('terrain_type', 'unknown')} with slope {float(terrain_data.get('slope_deg', 0.0)):.1f}° "
		f"and wind {float(wind_data.get('speed_mps', 0.0)):.1f} m/s. {_danger_recommendation(risk_score)}"
	)

	safe_zones = _build_safe_zones(state, risk_score)
	danger_zones = _build_danger_zones(terrain_data, risk_info)

	hazard_map = {
		"risk_score": risk_score,
		"safe_zones": safe_zones,
		"danger_zones": danger_zones,
		"summary": summary_text,
	}

	current_action = "replan_required" if risk_score >= 0.8 else "environment_analyzed"

	return {
		"terrain_data": terrain_data,
		"wind_data": wind_data,
		"hazard_map": hazard_map,
		"environment_summary": summary_text,
		"current_action": current_action,
		"llm_calls": int(state.get("llm_calls", 0)) + 1,
		"timestamp": datetime.now().isoformat(),
	}
