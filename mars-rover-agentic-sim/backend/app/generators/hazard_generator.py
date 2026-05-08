"""Hazard generation based on terrain properties."""

from __future__ import annotations

import json
import os
import random
from typing import Dict, List, Tuple


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def _seed_for(base_seed: int, key: str) -> int:
	acc = base_seed
	for ch in key:
		acc = (acc * 131 + ord(ch)) % 2_147_483_647
	return acc


def _risk_level(score: float) -> str:
	if score > 0.7:
		return "high"
	if score > 0.4:
		return "medium"
	return "low"


def generate_hazards(
	tile: Dict[str, object],
	seed: int,
	hazard_density: float,
) -> Tuple[Dict[str, object], Dict[str, float]]:
	terrain = tile["terrain"]
	tile_size_m = float(tile.get("tile_size_m", 256.0))
	rng = random.Random(_seed_for(seed, tile["tile_id"]))

	rock_density = float(terrain["rock_density"])
	sand_density = float(terrain["sand_density"])
	slope_max = float(terrain["slope"]["max"])
	terrain_type = terrain["terrain_type"]

	rock_count = int((rock_density + hazard_density * 0.4) * 18)
	sand_count = int((sand_density + hazard_density * 0.3) * 12)
	slope_count = 0
	if slope_max > 25:
		slope_count = int(_clamp((slope_max - 20) / 10, 1, 3))
	if terrain_type == "rocky":
		rock_count += 4
	if terrain_type == "sand":
		sand_count += 3

	obstacles: List[Dict[str, object]] = []
	for _ in range(rock_count):
		size = rng.uniform(0.5, 2.5)
		risk = _risk_level(_clamp(size / 2.5 + rock_density * 0.4, 0, 1))
		obstacles.append(
			{
				"type": "rock",
				"position": {
					"x": round(rng.uniform(0, tile_size_m), 2),
					"y": round(rng.uniform(0, tile_size_m), 2),
				},
				"size": round(size, 2),
				"risk_level": risk,
			}
		)

	for _ in range(sand_count):
		radius = rng.uniform(2.0, 6.0)
		risk = _risk_level(_clamp(radius / 6.0 + sand_density * 0.5, 0, 1))
		obstacles.append(
			{
				"type": "sand_trap",
				"position": {
					"x": round(rng.uniform(0, tile_size_m), 2),
					"y": round(rng.uniform(0, tile_size_m), 2),
				},
				"radius": round(radius, 2),
				"risk_level": risk,
			}
		)

	for _ in range(slope_count):
		width = rng.uniform(6.0, 14.0)
		obstacles.append(
			{
				"type": "slope",
				"position": {
					"x": round(rng.uniform(0, tile_size_m), 2),
					"y": round(rng.uniform(0, tile_size_m), 2),
				},
				"radius": round(width, 2),
				"risk_level": "high",
			}
		)

	hazard_data = {
		"region_id": f"{tile['tile_id']}_region",
		"tile_id": tile["tile_id"],
		"obstacles": obstacles,
	}

	summary = {
		"rock_count": rock_count,
		"sand_trap_count": sand_count,
		"slope_count": slope_count,
		"hazard_density": round(hazard_density, 3),
	}

	return hazard_data, summary


def validate_hazards(hazards: Dict[str, object]) -> None:
	for obstacle in hazards.get("obstacles", []):
		if obstacle["type"] not in {"rock", "sand_trap", "slope"}:
			raise ValueError(f"Unknown obstacle type {obstacle['type']}")


def write_hazards(tile_id: str, hazards: Dict[str, object], output_dir: str) -> str:
	hazards_dir = os.path.join(output_dir, "hazards")
	os.makedirs(hazards_dir, exist_ok=True)
	path = os.path.join(hazards_dir, f"{tile_id}.json")
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(hazards, handle, indent=2)
	return path

