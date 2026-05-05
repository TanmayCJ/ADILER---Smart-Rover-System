"""Memory agent for rover experience consolidation."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from agents.shared.llm_client import get_llama_client

logger = logging.getLogger(__name__)


def _build_experience(state: Dict[str, Any]) -> Dict[str, Any]:
	cycle_number = int(state.get("cycle_count", 0))
	action_taken = str(state.get("current_action", "unknown"))
	outcome = "success"
	if action_taken in {"replan_required", "interrupted", "error"}:
		outcome = "partial"
	if action_taken == "waiting_for_goal":
		outcome = "partial"

	return {
		"rover_position": dict(state.get("rover_position", {})),
		"action_taken": action_taken,
		"outcome": outcome,
		"observations": {
			"environment_summary": state.get("environment_summary", ""),
			"hazard_map": state.get("hazard_map", {}),
			"current_goal": state.get("current_goal"),
		},
		"timestamp": datetime.now().isoformat(),
		"cycle_number": cycle_number,
	}


def _trim(items: List[Any], limit: int = 20) -> List[Any]:
	return items[-limit:]


def _derive_patterns(experiences: List[Dict[str, Any]]) -> Dict[str, List[str]]:
	success_patterns: List[str] = []
	failure_patterns: List[str] = []
	for experience in experiences[-10:]:
		observations = experience.get("observations", {})
		hazard_map = observations.get("hazard_map", {})
		risk_score = float(hazard_map.get("risk_score", 0.0)) if isinstance(hazard_map, dict) else 0.0
		action_taken = experience.get("action_taken", "")
		outcome = experience.get("outcome", "")

		if outcome == "success" and risk_score < 0.6:
			success_patterns.append(f"{action_taken} worked well in low-risk terrain")
		if outcome != "success" or risk_score >= 0.75:
			failure_patterns.append(f"{action_taken} became risky when hazard score reached {risk_score:.2f}")

	return {
		"success_patterns": success_patterns[-5:],
		"failure_patterns": failure_patterns[-5:],
	}


def memory_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
	"""Consolidate recent rover experience into short- and long-term memory."""
	experience = _build_experience(state)
	experience_buffer = list(state.get("experience_buffer", []))
	experience_buffer.append(experience)
	experience_buffer = _trim(experience_buffer, 100)

	hazard_memory = list(state.get("hazard_memory", []))
	hazard_map = state.get("hazard_map", {})
	if isinstance(hazard_map, dict) and hazard_map:
		hazard_memory.append(
			{
				"hazard_type": "environment",
				"severity": float(hazard_map.get("risk_score", 0.0)),
				"location": {
					"lat": state.get("rover_position", {}).get("latitude"),
					"lon": state.get("rover_position", {}).get("longitude"),
				},
				"recommendation": hazard_map.get("summary", ""),
			}
		)
	hazard_memory = _trim(hazard_memory, 50)

	patterns = _derive_patterns(experience_buffer)
	memory_context = {
		"recent_experiences": experience_buffer[-5:],
		"learned_hazards": hazard_memory[-10:],
		"success_patterns": patterns["success_patterns"],
		"failure_patterns": patterns["failure_patterns"],
	}

	llm_client = get_llama_client(model="llama3.1")
	memory_note: Optional[str] = None
	try:
		prompt = json.dumps(
			{
				"recent_experience": experience,
				"success_patterns": memory_context["success_patterns"],
				"failure_patterns": memory_context["failure_patterns"],
			},
			indent=2,
		)
		memory_note = llm_client.invoke(
			prompt=prompt,
			system_prompt=(
				"You are the rover memory agent. Summarize the most useful lesson from the latest cycle in one sentence."
			),
			temperature=0.2,
			max_tokens=100,
		)
	except Exception as exc:  # pragma: no cover - defensive logging path
		logger.warning("Memory synthesis failed: %s", exc)

	route_history = _trim(list(state.get("route_history", [])), 50)

	updates = {
		"experience_buffer": experience_buffer,
		"hazard_memory": hazard_memory,
		"memory_context": memory_context,
		"route_history": route_history,
		"timestamp": datetime.now().isoformat(),
	}

	if memory_note:
		updates["environment_summary"] = memory_note

	return updates
