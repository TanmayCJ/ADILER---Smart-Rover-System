"""Risk validator for environment analysis outputs."""

from __future__ import annotations

from typing import Any, Dict, List


def _get_value(data: Dict[str, Any], path: str) -> Any:
    current: Any = data
    for key in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def validate_risk(scenario: Dict[str, Any], output: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    expected_risk = scenario["expected_behavior"]["expected_risk_level"]
    risk_score = _get_value(output, "agent_outputs.environment_analysis.hazard_map.risk_score")

    if risk_score is None:
        errors.append("Missing hazard_map.risk_score in output.")
        return errors

    if expected_risk == "low" and risk_score >= 0.4:
        errors.append(f"Risk score {risk_score:.2f} too high for low-risk scenario.")
    elif expected_risk == "medium" and not (0.4 <= risk_score < 0.7):
        errors.append(f"Risk score {risk_score:.2f} outside expected medium range.")
    elif expected_risk in {"high", "critical"} and risk_score < 0.7:
        errors.append(f"Risk score {risk_score:.2f} too low for high/critical scenario.")

    return errors
