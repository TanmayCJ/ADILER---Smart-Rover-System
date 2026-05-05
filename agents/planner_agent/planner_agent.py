"""Planner agent for rover route generation."""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.shared.llm_client import get_llama_client

logger = logging.getLogger(__name__)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
	return max(lower, min(upper, value))


def _strip_code_fences(text: str) -> str:
	cleaned = text.strip()
	if cleaned.startswith("```") and cleaned.endswith("```"):
		lines = cleaned.splitlines()
		if len(lines) >= 3:
			return "\n".join(lines[1:-1]).strip()
	return cleaned


def _extract_json_object(text: str) -> Optional[str]:
	start = text.find("{")
	end = text.rfind("}")
	if start == -1 or end == -1 or end <= start:
		return None
	return text[start : end + 1]


def _parse_planner_payload(
	llm_response: str,
	llm_client,
) -> Dict[str, Any]:
	"""Parse or repair the planner LLM response into a JSON payload."""
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
		"decision_type (straight|detour|stop), detour_bias (0.0-0.08), note. "
		"Return ONLY JSON.\n\n"
		f"Response: {cleaned}"
	)
	reformat_response = llm_client.invoke(
		prompt=reformat_prompt,
		system_prompt="Return only JSON. No code fences.",
		temperature=0.0,
		max_tokens=120,
	)
	cleaned_reformat = _strip_code_fences(reformat_response)
	try:
		return json.loads(cleaned_reformat)
	except json.JSONDecodeError as exc:
		logger.error("Planner LLM response not JSON after reformat. Raw: %s", cleaned)
		raise ValueError("Planner LLM response could not be parsed as JSON.") from exc


def _distance_m(start: Dict[str, Any], end: Dict[str, Any]) -> float:
	latitude_delta = float(end.get("latitude", 0.0)) - float(start.get("latitude", 0.0))
	longitude_delta = float(end.get("longitude", 0.0)) - float(start.get("longitude", 0.0))
	return math.sqrt(latitude_delta ** 2 + longitude_delta ** 2) * 111_000.0


def _interpolate_waypoint(
	start: Dict[str, Any],
	end: Dict[str, Any],
	fraction: float,
	action: str,
	priority: int,
) -> Dict[str, Any]:
	return {
		"latitude": float(start.get("latitude", 0.0)) + (float(end.get("latitude", 0.0)) - float(start.get("latitude", 0.0))) * fraction,
		"longitude": float(start.get("longitude", 0.0)) + (float(end.get("longitude", 0.0)) - float(start.get("longitude", 0.0))) * fraction,
		"action": action,
		"priority": priority,
	}


def _build_route(state: Dict[str, Any], detour_bias: float = 0.0) -> List[Dict[str, Any]]:
	rover_position = state.get("rover_position", {})
	goal = state.get("current_goal")
	hazard_map = state.get("hazard_map", {})
	risk_score = float(hazard_map.get("risk_score", 0.5))

	if not goal:
		return []

	start = {
		"latitude": float(rover_position.get("latitude", goal.get("latitude", 0.0))),
		"longitude": float(rover_position.get("longitude", goal.get("longitude", 0.0))),
	}
	end = {
		"latitude": float(goal.get("latitude", start["latitude"])),
		"longitude": float(goal.get("longitude", start["longitude"])),
	}

	detour = max(detour_bias, 0.0)
	if risk_score >= 0.65:
		detour = max(detour, 0.03 + (risk_score - 0.65) * 0.05)

	midpoint = _interpolate_waypoint(start, end, 0.5, "move", int(goal.get("priority", 5)))
	if detour:
		midpoint["latitude"] += detour
		midpoint["longitude"] += detour

	approach = _interpolate_waypoint(start, midpoint, 0.7, "move", int(goal.get("priority", 5)))
	goal_waypoint = {
		"latitude": end["latitude"],
		"longitude": end["longitude"],
		"action": "collect_sample",
		"priority": int(goal.get("priority", 5)),
	}

	return [approach, midpoint, goal_waypoint]


def planner_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
	"""Build or refresh a rover route toward the current goal."""
	goal = state.get("current_goal")
	hazard_map = state.get("hazard_map", {})

	if not goal:
		return {
			"planned_route": [],
			"current_waypoint_index": 0,
			"current_action": "waiting_for_goal",
			"timestamp": datetime.now().isoformat(),
		}

	planned_route = _build_route(state)
	route_distance = _distance_m(state.get("rover_position", {}), goal)
	risk_score = float(hazard_map.get("risk_score", 0.5))
	success_probability = _clamp(1.0 - (risk_score * 0.65) - min(route_distance / 100_000.0, 0.2))
	estimated_duration_s = max(route_distance / max(0.15, 0.5 - (risk_score * 0.3)), 1.0)

	planning_note: Optional[str] = None
	decision_type: Optional[str] = None
	llm_detour_bias = 0.0
	if os.environ.get("LLM_DECISIONS", "1") not in {"0", "false", "False"}:
		llm_client = get_llama_client(model="llama3.1")
		try:
			prompt = json.dumps(
				{
					"goal": goal,
					"risk_score": risk_score,
					"route_distance_m": route_distance,
					"planned_waypoints": planned_route,
					"hazard_summary": hazard_map.get("summary"),
				},
				indent=2,
			)
			llm_response = llm_client.invoke(
				prompt=prompt,
				system_prompt=(
					"You are the rover planner. Return a JSON object with keys: "
					"decision_type (straight|detour|stop), detour_bias (0.0-0.08), note. "
					"Return ONLY JSON, no extra text. Use detour when risk is elevated. "
					"Use stop when risk is critical."
				),
				temperature=0.0,
				max_tokens=160,
			)
			llm_payload = _parse_planner_payload(str(llm_response), llm_client)
			decision_type = str(llm_payload.get("decision_type") or "").lower()
			planning_note = str(llm_payload.get("note") or "").strip() or None
			llm_detour_bias = float(llm_payload.get("detour_bias") or 0.0)
		except Exception as exc:  # pragma: no cover - defensive logging path
			logger.warning("Planner summary generation failed: %s", exc)

	if decision_type == "stop":
		planned_route = []
		current_action = "replan_required"
	elif decision_type == "detour":
		if llm_detour_bias <= 0.0:
			llm_detour_bias = 0.02 + _clamp(risk_score, 0.0, 1.0) * 0.04
		planned_route = _build_route(state, detour_bias=llm_detour_bias)
		current_action = "moving" if planned_route else "replan_required"
	else:
		current_action = "moving" if planned_route else "replan_required"

	route = {
		"waypoints": planned_route,
		"estimated_duration_s": estimated_duration_s,
		"success_probability": success_probability,
		"created_at": datetime.now().isoformat(),
	}

	route_history = list(state.get("route_history", []))
	route_history.append(route)

	if risk_score >= 0.85:
		current_action = "replan_required"

	updates = {
		"planned_route": planned_route,
		"current_waypoint_index": 0,
		"current_action": current_action,
		"route_history": route_history[-50:],
		"timestamp": datetime.now().isoformat(),
	}

	if planning_note:
		updates["environment_summary"] = planning_note

	return updates
