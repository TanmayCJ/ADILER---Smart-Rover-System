"""Rover telemetry generation aligned with terrain and wind conditions."""

from __future__ import annotations

import math
import random
from typing import Dict, List


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def _seed_for(base_seed: int, key: str) -> int:
	acc = base_seed
	for ch in key:
		acc = (acc * 131 + ord(ch)) % 2_147_483_647
	return acc


def _terrain_traction(terrain_type: str) -> float:
	mapping = {
		"plains": 0.78,
		"sand": 0.42,
		"rocky": 0.7,
		"crater": 0.58,
		"slope": 0.55,
	}
	return mapping.get(terrain_type, 0.65)


def generate_rover_states(
	mission: Dict[str, object],
	terrain: Dict[str, object],
	wind_series: List[Dict[str, object]],
	duration_sec: int,
	dt_sec: float,
	seed: int,
) -> List[Dict[str, object]]:
	rng = random.Random(_seed_for(seed, mission["mission"]["mission_id"]))
	steps = max(1, int(duration_sec / dt_sec))
	start_x, start_y = mission["mission"]["start_position"]
	goal_x, goal_y = mission["mission"]["goal_position"]

	dx = goal_x - start_x
	dy = goal_y - start_y
	total_dist = max(1.0, math.sqrt(dx * dx + dy * dy))
	direction = math.atan2(dy, dx)

	terrain_type = terrain["terrain"]["terrain_type"]
	slope_avg = float(terrain["terrain"]["slope"]["average"])
	roughness = float(terrain["terrain"]["roughness"])
	sand_density = float(terrain["terrain"]["sand_density"])
	elevation_mean = float(terrain["terrain"]["elevation"]["mean"])

	base_speed = 0.9 - slope_avg / 60.0
	traction_base = _terrain_traction(terrain_type)
	battery = rng.uniform(70, 95)
	wheel_health = 0.98

	states: List[Dict[str, object]] = []
	distance_travelled = 0.0
	previous_speed = base_speed
	previous_x = start_x
	previous_y = start_y

	for idx in range(steps):
		wind = wind_series[min(idx, len(wind_series) - 1)]["wind"]
		wind_speed = float(wind["speed"])

		slope_variation = rng.uniform(-3.0, 3.0)
		local_slope = _clamp(slope_avg + slope_variation, 0.0, 30.0)
		traction = _clamp(traction_base - sand_density * 0.2 - local_slope / 40.0, 0.2, 0.95)
		slippage = _clamp(1.0 - traction + sand_density * 0.2 + local_slope / 45.0, 0.05, 0.9)

		speed_factor = (battery / 100.0) * 0.4 + 0.6
		wind_penalty = 1.0 - wind_speed / 50.0
		speed = _clamp(base_speed * speed_factor * wind_penalty * (1.0 - slippage * 0.35), 0.2, 1.6)
		acceleration = _clamp((speed - previous_speed) / dt_sec, -0.6, 0.6)
		previous_speed = speed

		travel = min(speed * dt_sec, total_dist - distance_travelled)
		distance_travelled += travel
		position_x = start_x + math.cos(direction) * distance_travelled
		position_y = start_y + math.sin(direction) * distance_travelled
		heading = math.degrees(math.atan2(position_y - previous_y, position_x - previous_x)) % 360
		previous_x = position_x
		previous_y = position_y

		motor_load = _clamp(0.35 + local_slope / 40.0 + wind_speed / 60.0, 0.2, 0.95)
		consumption_rate = 0.06 + motor_load * 0.08 + local_slope / 300.0
		battery = _clamp(battery - consumption_rate * dt_sec, 5.0, 100.0)
		motor_temp = 30.0 + motor_load * 20.0 + (1.0 - traction) * 5.0

		wheel_health = _clamp(wheel_health - slippage * 0.0004, 0.7, 1.0)

		rover_state = {
			"position": {
				"x": round(position_x, 2),
				"y": round(position_y, 2),
				"z": round(elevation_mean + local_slope * 0.6, 2),
			},
			"heading": round(heading, 1),
			"velocity": round(speed, 2),
			"acceleration": round(acceleration, 2),
			"battery": {
				"percentage": round(battery, 2),
				"consumption_rate": round(consumption_rate, 3),
				"temperature": round(28 + consumption_rate * 50, 1),
			},
			"motors": {
				"left_motor_load": round(_clamp(motor_load + rng.uniform(-0.03, 0.03), 0.1, 1.0), 3),
				"right_motor_load": round(_clamp(motor_load + rng.uniform(-0.03, 0.03), 0.1, 1.0), 3),
				"motor_temperature": round(motor_temp, 1),
			},
			"wheels": {
				"traction": round(traction, 3),
				"slippage": round(slippage, 3),
				"wheel_health": round(wheel_health, 3),
			},
		}

		states.append({"timestamp": int(idx * dt_sec), "rover_state": rover_state})
		if distance_travelled >= total_dist:
			# Stay parked for the remaining steps.
			start_x = position_x
			start_y = position_y
			total_dist = distance_travelled

	return states


def validate_rover_states(states: List[Dict[str, object]]) -> None:
	for entry in states:
		rover = entry["rover_state"]
		battery = rover["battery"]["percentage"]
		if not (0 <= battery <= 100):
			raise ValueError(f"Battery out of range: {battery}")
		traction = rover["wheels"]["traction"]
		if not (0 <= traction <= 1):
			raise ValueError("Traction out of range")

