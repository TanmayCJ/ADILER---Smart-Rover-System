"""Environment agent: compute risk from terrain, wind, and hazards."""

from __future__ import annotations

from typing import Dict


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
	return max(low, min(high, value))


def environment_node(state: Dict[str, object]) -> Dict[str, object]:
	"""Analyze environment and emit a simple risk score."""

	terrain = state.get("terrain_tile", {}).get("terrain", {})
	wind_series = state.get("wind_series", [])
	hazards = state.get("hazards", {})

	slope_avg = float(terrain.get("slope", {}).get("average", 0.0))
	roughness = float(terrain.get("roughness", 0.0))
	traversability = float(terrain.get("traversability_score", 1.0))
	wind_speed = 0.0
	dust_density = 0.0
	if wind_series:
		wind = wind_series[0].get("wind", {})
		wind_speed = float(wind.get("speed", 0.0))
		dust_density = float(wind.get("dust_density", 0.0))

	obstacle_count = len(hazards.get("obstacles", []))

	slope_risk = _clamp(slope_avg / 45.0)
	roughness_risk = _clamp(roughness)
	wind_risk = _clamp(wind_speed / 25.0)
	dust_risk = _clamp(dust_density)
	obstacle_risk = _clamp(obstacle_count / 15.0)
	traversability_risk = _clamp(1.0 - traversability)

	risk_score = _clamp(
		0.25 * slope_risk
		+ 0.2 * roughness_risk
		+ 0.2 * wind_risk
		+ 0.15 * dust_risk
		+ 0.1 * obstacle_risk
		+ 0.1 * traversability_risk
	)

	environment_state = {
		"risk_score": round(risk_score, 3),
		"slope_avg": round(slope_avg, 2),
		"roughness": round(roughness, 3),
		"traversability": round(traversability, 3),
		"wind_speed": round(wind_speed, 2),
		"dust_density": round(dust_density, 3),
		"obstacle_count": obstacle_count,
	}

	return {"environment_state": environment_state}

