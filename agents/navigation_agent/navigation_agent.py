"""Navigation agent for rover motion control."""

from __future__ import annotations

import json
import logging
import os
import math
from datetime import datetime
from typing import Any, Dict, List

from agents.shared.llm_client import get_llama_client
from agents.shared.mock_generators import get_mock_generator

logger = logging.getLogger(__name__)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
	return max(lower, min(upper, value))


def _distance_m(start: Dict[str, Any], end: Dict[str, Any]) -> float:
	latitude_delta = float(end.get("latitude", 0.0)) - float(start.get("latitude", 0.0))
	longitude_delta = float(end.get("longitude", 0.0)) - float(start.get("longitude", 0.0))
	return math.sqrt(latitude_delta ** 2 + longitude_delta ** 2) * 111_000.0


def _heading_deg(start: Dict[str, Any], end: Dict[str, Any]) -> float:
	latitude_delta = float(end.get("latitude", 0.0)) - float(start.get("latitude", 0.0))
	longitude_delta = float(end.get("longitude", 0.0)) - float(start.get("longitude", 0.0))
	if latitude_delta == 0 and longitude_delta == 0:
		return float(start.get("rover_heading", 0.0))
	heading = math.degrees(math.atan2(longitude_delta, latitude_delta))
	return heading % 360.0


def _speed_limit_from_conditions(state: Dict[str, Any]) -> float:
	terrain = state.get("terrain_data", {})
	wind = state.get("wind_data", {})
	slope_deg = float(terrain.get("slope_deg", 0.0))
	roughness = _clamp(float(terrain.get("roughness", 0.0)))
	wind_speed = float(wind.get("speed_mps", 0.0))
	base_speed = 0.5
	slope_factor = _clamp(1.0 - slope_deg / 40.0, 0.3, 1.0)
	roughness_factor = _clamp(1.0 - roughness * 0.45, 0.5, 1.0)
	wind_factor = _clamp(1.0 - max(wind_speed - 5.0, 0.0) / 20.0, 0.45, 1.0)
	return base_speed * slope_factor * roughness_factor * wind_factor


def _strip_code_fences(text: str) -> str:
	cleaned = text.strip()
	if cleaned.startswith("```") and cleaned.endswith("```"):
		lines = cleaned.splitlines()
		if len(lines) >= 3:
			return "\n".join(lines[1:-1]).strip()
	return cleaned


def _extract_json_object(text: str) -> str | None:
	start = text.find("{")
	end = text.rfind("}")
	if start == -1 or end == -1 or end <= start:
		return None
	return text[start : end + 1]


def _parse_navigation_payload(llm_response: str, llm_client) -> Dict[str, Any]:
	cleaned = _strip_code_fences(llm_response)
	for candidate in (cleaned, _extract_json_object(cleaned)):
		if not candidate:
			continue
		try:
			return json.loads(candidate)
		except json.JSONDecodeError:
			pass

	reformat_prompt = (
		"Convert the response below into a JSON object with keys: "
		"action (move|rotate|stop|hold), speed_factor (0.0-1.2), "
		"heading_offset_deg (-20 to 20), note. Return ONLY JSON.\n\n"
		f"Response: {cleaned}"
	)
	reformat_response = llm_client.invoke(
		prompt=reformat_prompt,
		system_prompt="Return only JSON. No code fences.",
		temperature=0.0,
		max_tokens=140,
	)
	cleaned_reformat = _strip_code_fences(reformat_response)
	try:
		return json.loads(cleaned_reformat)
	except json.JSONDecodeError as exc:
		logger.warning("Navigation LLM response not JSON: %s", cleaned)
		raise ValueError("Navigation LLM response could not be parsed as JSON.") from exc


def navigation_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
	"""Execute one navigation step against the current planned route."""
	if state.get("loop_interrupted"):
		return {
			"current_action": "interrupted",
			"timestamp": datetime.now().isoformat(),
		}

	planned_route: List[Dict[str, Any]] = list(state.get("planned_route", []))
	waypoint_index = int(state.get("current_waypoint_index", 0))
	rover_position = dict(state.get("rover_position", {}))

	if not planned_route:
		return {
			"current_action": "replan_required",
			"timestamp": datetime.now().isoformat(),
		}

	if waypoint_index >= len(planned_route):
		return {
			"current_action": "reached_goal",
			"rover_velocity": 0.0,
			"timestamp": datetime.now().isoformat(),
		}

	target_waypoint = planned_route[waypoint_index]
	distance_to_target = _distance_m(rover_position, target_waypoint)
	speed_limit = _speed_limit_from_conditions(state)
	travel_speed = min(speed_limit, max(0.05, float(state.get("rover_velocity", 0.0)) or speed_limit))

	if distance_to_target <= 5.0:
		waypoint_index += 1
		if waypoint_index >= len(planned_route):
			rover_position["latitude"] = float(target_waypoint.get("latitude", rover_position.get("latitude", 0.0)))
			rover_position["longitude"] = float(target_waypoint.get("longitude", rover_position.get("longitude", 0.0)))
			return {
				"rover_position": rover_position,
				"current_waypoint_index": waypoint_index,
				"current_action": "reached_goal",
				"rover_velocity": 0.0,
				"timestamp": datetime.now().isoformat(),
			}
		target_waypoint = planned_route[waypoint_index]
		distance_to_target = _distance_m(rover_position, target_waypoint)

	heading = _heading_deg(rover_position, target_waypoint)

	if os.environ.get("LLM_DECISIONS", "1") not in {"0", "false", "False"}:
		llm_client = get_llama_client(model="llama3.1")
		try:
			prompt = json.dumps(
				{
					"current_action": state.get("current_action"),
					"risk_score": state.get("hazard_map", {}).get("risk_score"),
					"terrain": state.get("terrain_data", {}),
					"wind": state.get("wind_data", {}),
					"distance_to_target_m": distance_to_target,
					"speed_limit": speed_limit,
					"heading_deg": heading,
				},
				indent=2,
			)
			llm_response = llm_client.invoke(
				prompt=prompt,
				system_prompt=(
					"You are the rover navigation controller. Return a JSON object with keys: "
					"action (move|rotate|stop|hold), speed_factor (0.0-1.2), "
					"heading_offset_deg (-20 to 20), note. Return ONLY JSON."
				),
				temperature=0.1,
				max_tokens=160,
			)
			navigation_payload = _parse_navigation_payload(str(llm_response), llm_client)
			action = str(navigation_payload.get("action") or "move").lower()
			speed_factor = float(navigation_payload.get("speed_factor") or 1.0)
			speed_factor = _clamp(speed_factor, 0.0, 1.2)
			heading_offset = float(navigation_payload.get("heading_offset_deg") or 0.0)
			heading_offset = max(-20.0, min(20.0, heading_offset))
			heading = (heading + heading_offset) % 360.0

			if action in {"stop", "hold"}:
				return {
					"rover_position": rover_position,
					"rover_heading": heading,
					"rover_velocity": 0.0,
					"current_action": "stopped",
					"timestamp": datetime.now().isoformat(),
				}
			if action == "rotate":
				return {
					"rover_position": rover_position,
					"rover_heading": heading,
					"rover_velocity": 0.0,
					"current_action": "rotating",
					"timestamp": datetime.now().isoformat(),
				}
			travel_speed = max(0.05, min(speed_limit, travel_speed * speed_factor))
			current_action = "moving"
		except Exception as exc:
			logger.warning("Navigation LLM reasoning failed: %s", exc)
			current_action = "moving"
	movement_fraction = _clamp((travel_speed * 1.0 * 1_000.0) / max(distance_to_target, 1.0), 0.0, 0.35)

	rover_position["latitude"] = float(rover_position.get("latitude", 0.0)) + (
		float(target_waypoint.get("latitude", 0.0)) - float(rover_position.get("latitude", 0.0))
	) * movement_fraction
	rover_position["longitude"] = float(rover_position.get("longitude", 0.0)) + (
		float(target_waypoint.get("longitude", 0.0)) - float(rover_position.get("longitude", 0.0))
	) * movement_fraction

	mock_generator = get_mock_generator()
	updated_state = mock_generator.simulate_rover_movement(
		{
			"rover_position": rover_position,
			"rover_heading": float(state.get("rover_heading", 0.0)),
			"rover_velocity": float(state.get("rover_velocity", 0.0)),
		},
		speed=travel_speed,
		heading=heading,
		time_delta_s=1.0,
	)

	rover_position = updated_state["rover_position"]
	rover_position["latitude"] = float(rover_position.get("latitude", 0.0))
	rover_position["longitude"] = float(rover_position.get("longitude", 0.0))

	current_action = current_action if waypoint_index < len(planned_route) else "reached_goal"

	return {
		"rover_position": rover_position,
		"rover_heading": heading,
		"rover_velocity": travel_speed,
		"current_waypoint_index": waypoint_index,
		"current_action": current_action,
		"timestamp": datetime.now().isoformat(),
	}
