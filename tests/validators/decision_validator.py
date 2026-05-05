"""Decision validator for planner outputs."""

from __future__ import annotations

from typing import Any, Dict, List


def _get_value(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def validate_decision(scenario: Dict[str, Any], output: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    expected = scenario["expected_behavior"]["expected_decision_type"]
    planned_route = _get_value(output, "agent_outputs.planner_output.planned_route") or []

    if expected == "straight" and len(planned_route) > 0:
        # Straight path expects the midpoint to be near linear; we only check for route existence.
        return errors

    if expected in {"detour", "reroute"} and not planned_route:
        errors.append("Planner did not produce a route for a detour scenario.")

    if expected == "stop" and output["workflow_result"]["state"].get("current_action") not in {"replan_required", "stopped"}:
        errors.append("Planner decision expected stop/replan but current_action did not reflect it.")

    return errors
