"""Navigation agent: apply a simple movement step."""

from __future__ import annotations

import math
from typing import Dict, Tuple


def _step_toward(start: Tuple[float, float], goal: Tuple[float, float], step_m: float) -> Tuple[float, float]:
	dx = goal[0] - start[0]
	dy = goal[1] - start[1]
	distance = math.sqrt(dx * dx + dy * dy)
	if distance <= 0.001:
		return start
	ratio = min(step_m / distance, 1.0)
	return (start[0] + dx * ratio, start[1] + dy * ratio)


def navigation_node(state: Dict[str, object]) -> Dict[str, object]:
	"""Update rover position based on the planner action."""

	plan = state.get("plan", {})
	action = plan.get("action", "hold")
	rover_state = dict(state.get("rover_state", {}))
	mission = state.get("mission", {})
	goal_pos = mission.get("mission", {}).get("goal_position", [0.0, 0.0])

	position = rover_state.get("position", {})
	current = (float(position.get("x", 0.0)), float(position.get("y", 0.0)))
	goal = (float(goal_pos[0]), float(goal_pos[1]))

	step_m = 0.0
	if action == "proceed":
		step_m = 1.0
	elif action == "proceed_cautious":
		step_m = 0.4

	new_x, new_y = _step_toward(current, goal, step_m)
	rover_state["position"] = {
		"x": round(new_x, 2),
		"y": round(new_y, 2),
		"z": float(position.get("z", 0.0)),
	}
	rover_state["velocity"] = round(step_m, 2)

	decisions = list(state.get("decisions", []))
	decisions.append({"navigation": {"action": action, "step_m": step_m}})

	return {"rover_state": rover_state, "decisions": decisions}

