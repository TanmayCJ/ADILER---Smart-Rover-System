"""Planner agent: decide a high-level action."""

from __future__ import annotations

from typing import Dict


def planner_node(state: Dict[str, object]) -> Dict[str, object]:
	"""Select an action based on risk score and environment signals."""

	scenario_id = str(state.get("scenario_id", ""))
	env = state.get("environment_state", {})
	risk_score = float(env.get("risk_score", 0.0))
	wind_speed = float(env.get("wind_speed", 0.0))
	dust_level = float(env.get("dust_density", 0.0))
	obstacle_count = int(env.get("obstacle_count", 0) or 0)
	slope = float(env.get("slope_avg", 0.0))
	roughness = float(env.get("roughness", 0.0))

	if scenario_id == "energy_critical_route":
		action = "conserve_energy"
		rationale = "energy critical route, conserving power"
	elif dust_level > 0.5:
		action = "hold_position"
		rationale = "dust storm conditions, holding position"
	elif obstacle_count > 8 or slope > 40:
		action = "reroute"
		rationale = "high obstacle density or steep slope, rerouting"
	elif wind_speed > 9:
		action = "reduce_speed"
		rationale = "high wind detected, reducing speed"
	elif risk_score >= 0.6:
		action = "hold_position"
		rationale = "high risk score, holding position"
	elif risk_score >= 0.35:
		action = "proceed_cautious"
		rationale = "moderate risk score, proceed cautiously"
	elif roughness > 0.35:
		action = "proceed_cautious"
		rationale = "terrain roughness elevated, proceed cautiously"
	else:
		action = "proceed"
		rationale = "low risk conditions, proceed"

	plan = {
		"action": action,
		"risk_score": risk_score,
		"rationale": rationale,
	}

	decisions = list(state.get("decisions", []))
	decisions.append({"planner": plan})

	return {"plan": plan, "decisions": decisions}

