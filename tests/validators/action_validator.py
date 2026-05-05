"""Action validator for navigation outputs."""

from __future__ import annotations

from typing import Any, Dict, List


def _get_value(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def validate_action(scenario: Dict[str, Any], output: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    expected_action = scenario["expected_behavior"]["expected_action"]
    current_action = _get_value(output, "workflow_result.state.current_action")

    if expected_action and current_action != expected_action:
        errors.append(f"Expected action '{expected_action}', got '{current_action}'.")

    return errors
