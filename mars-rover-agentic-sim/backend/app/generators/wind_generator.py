"""Wind and atmosphere generation for Mars-like conditions."""

from __future__ import annotations

import json
import math
import os
import random
from typing import Dict, List


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def _seed_for(base_seed: int, key: str) -> int:
	acc = base_seed
	for ch in key:
		acc = (acc * 131 + ord(ch)) % 2_147_483_647
	return acc


def _smooth_series(
	count: int,
	rng: random.Random,
	base: float,
	variance: float,
	smooth: float,
) -> List[float]:
	values = []
	current = base
	for _ in range(count):
		target = base + rng.uniform(-variance, variance)
		current = current * (1 - smooth) + target * smooth
		values.append(current)
	return values


def generate_wind_series(
	tile: Dict[str, object],
	duration_sec: int,
	dt_sec: float,
	seed: int,
	intensity: float,
) -> List[Dict[str, object]]:
	rng = random.Random(_seed_for(seed, tile["tile_id"]))
	steps = max(1, int(duration_sec / dt_sec))
	lat = float(tile["coordinates"]["latitude"])
	lon = float(tile["coordinates"]["longitude"])

	base_speed = 6.0 + intensity * 8.0 + (abs(lat) / 90.0) * 2.0
	speed_series = _smooth_series(steps, rng, base_speed, 4.5, smooth=0.12)
	dir_series = _smooth_series(steps, rng, 120.0 + (lon % 20), 40.0, smooth=0.08)
	turbulence_series = _smooth_series(steps, rng, 0.35 + intensity * 0.2, 0.2, smooth=0.18)

	sol_day = 88775.0
	entries: List[Dict[str, object]] = []
	for idx in range(steps):
		timestamp = int(idx * dt_sec)
		diurnal_phase = (timestamp % sol_day) / sol_day
		temperature = -65 + 15 * math.sin(2 * math.pi * diurnal_phase)
		pressure = 610 + 10 * math.sin(2 * math.pi * diurnal_phase + 0.6)

		speed = max(0.1, speed_series[idx])
		turbulence = _clamp(turbulence_series[idx], 0.05, 0.95)
		gust_probability = _clamp(speed / 35.0 + turbulence * 0.35, 0.05, 0.85)
		dust_density = _clamp((speed / 25.0) * 0.5 + turbulence * 0.4 + intensity * 0.2, 0.05, 0.9)
		visibility = _clamp(1.0 - dust_density * 0.8 - speed / 50.0, 0.2, 1.0)

		entry = {
			"timestamp": timestamp,
			"location": {
				"latitude": round(lat, 4),
				"longitude": round(lon, 4),
			},
			"wind": {
				"speed": round(speed, 2),
				"direction": round(dir_series[idx] % 360, 1),
				"gust_probability": round(gust_probability, 3),
				"turbulence": round(turbulence, 3),
				"dust_density": round(dust_density, 3),
				"visibility": round(visibility, 3),
			},
			"atmosphere": {
				"pressure": round(pressure, 1),
				"temperature": round(temperature, 1),
			},
		}
		entries.append(entry)

	return entries


def summarize_wind(entries: List[Dict[str, object]]) -> Dict[str, float]:
	if not entries:
		return {"avg_speed": 0.0, "avg_dust": 0.0}
	speeds = [e["wind"]["speed"] for e in entries]
	dust = [e["wind"]["dust_density"] for e in entries]
	return {
		"avg_speed": round(sum(speeds) / len(speeds), 2),
		"avg_dust": round(sum(dust) / len(dust), 3),
	}


def validate_wind_series(entries: List[Dict[str, object]]) -> None:
	for entry in entries:
		wind = entry["wind"]
		if not (0 <= wind["speed"] <= 40):
			raise ValueError(f"Wind speed out of range: {wind['speed']}")
		if not (0 <= wind["gust_probability"] <= 1):
			raise ValueError("Gust probability out of range")
		if not (0 <= wind["turbulence"] <= 1):
			raise ValueError("Turbulence out of range")
		if not (0 <= wind["dust_density"] <= 1):
			raise ValueError("Dust density out of range")
		if not (0 <= wind["visibility"] <= 1):
			raise ValueError("Visibility out of range")
		atmosphere = entry["atmosphere"]
		if not (500 <= atmosphere["pressure"] <= 750):
			raise ValueError("Pressure out of range")
		if not (-100 <= atmosphere["temperature"] <= 10):
			raise ValueError("Temperature out of range")


def write_wind_series(tile_id: str, entries: List[Dict[str, object]], output_dir: str) -> str:
	wind_dir = os.path.join(output_dir, "weather", "wind_fields")
	os.makedirs(wind_dir, exist_ok=True)
	path = os.path.join(wind_dir, f"{tile_id}.json")
	with open(path, "w", encoding="utf-8") as handle:
		json.dump({"tile_id": tile_id, "series": entries}, handle, indent=2)
	return path


def write_atmosphere_profile(tile_id: str, entries: List[Dict[str, object]], output_dir: str) -> str:
	profile_dir = os.path.join(output_dir, "weather", "atmosphere_profiles")
	os.makedirs(profile_dir, exist_ok=True)
	profile = {
		"tile_id": tile_id,
		"pressure_mean": round(sum(e["atmosphere"]["pressure"] for e in entries) / len(entries), 1),
		"temperature_mean": round(sum(e["atmosphere"]["temperature"] for e in entries) / len(entries), 1),
	}
	path = os.path.join(profile_dir, f"{tile_id}.json")
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(profile, handle, indent=2)
	return path

