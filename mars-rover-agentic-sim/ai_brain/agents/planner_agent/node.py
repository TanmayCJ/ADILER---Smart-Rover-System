"""Planner agent: decide a high-level action."""

from __future__ import annotations

from typing import Dict


def planner_node(state: Dict[str, object]) -> Dict[str, object]:
	"""Select a simple action based on risk score."""

	env = state.get("environment_state", {})
	risk_score = float(env.get("risk_score", 0.0))

	if risk_score >= 0.7:
		action = "hold"
	elif risk_score >= 0.45:
		action = "proceed_cautious"
	else:
		action = "proceed"

	plan = {
		"action": action,
		"risk_score": risk_score,
	}

	decisions = list(state.get("decisions", []))
	decisions.append({"planner": plan})

	return {"plan": plan, "decisions": decisions}

