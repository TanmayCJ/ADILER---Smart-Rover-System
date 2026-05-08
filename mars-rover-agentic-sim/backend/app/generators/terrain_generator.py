"""Procedural terrain generation for Mars-like tiles."""

from __future__ import annotations

import json
import math
import os
import random
from typing import Dict, List, Tuple


def _clamp(value: float, low: float, high: float) -> float:
	return max(low, min(high, value))


def _lerp(a: float, b: float, t: float) -> float:
	return a + (b - a) * t


def _bilerp(v00: float, v10: float, v01: float, v11: float, tx: float, ty: float) -> float:
	return _lerp(_lerp(v00, v10, tx), _lerp(v01, v11, tx), ty)


def _seed_for(base_seed: int, key: str) -> int:
	# Deterministic per-tile seed without external deps.
	acc = base_seed
	for ch in key:
		acc = (acc * 131 + ord(ch)) % 2_147_483_647
	return acc


def _value_noise(size: int, grid_size: int, rng: random.Random) -> List[List[float]]:
	grid = [[rng.uniform(-1.0, 1.0) for _ in range(grid_size + 1)] for _ in range(grid_size + 1)]
	scale = size / grid_size
	noise = [[0.0 for _ in range(size)] for _ in range(size)]

	for y in range(size):
		gy = min(grid_size - 1, int(y / scale))
		ty = (y / scale) - gy
		for x in range(size):
			gx = min(grid_size - 1, int(x / scale))
			tx = (x / scale) - gx
			v00 = grid[gy][gx]
			v10 = grid[gy][gx + 1]
			v01 = grid[gy + 1][gx]
			v11 = grid[gy + 1][gx + 1]
			noise[y][x] = _bilerp(v00, v10, v01, v11, tx, ty)
	return noise


def _apply_blur(heightmap: List[List[float]], passes: int = 1) -> List[List[float]]:
	size = len(heightmap)
	result = heightmap
	for _ in range(passes):
		blurred = [[0.0 for _ in range(size)] for _ in range(size)]
		for y in range(size):
			for x in range(size):
				total = 0.0
				count = 0
				for dy in (-1, 0, 1):
					for dx in (-1, 0, 1):
						ny = y + dy
						nx = x + dx
						if 0 <= ny < size and 0 <= nx < size:
							total += result[ny][nx]
							count += 1
				blurred[y][x] = total / max(1, count)
		result = blurred
	return result


def _apply_crater(heightmap: List[List[float]], depth: float) -> None:
	size = len(heightmap)
	cx = size / 2.0
	cy = size / 2.0
	radius = size * 0.35
	for y in range(size):
		for x in range(size):
			dx = x - cx
			dy = y - cy
			dist = math.sqrt(dx * dx + dy * dy)
			if dist < radius:
				falloff = (1 - dist / radius) ** 2
				heightmap[y][x] -= depth * falloff


def _apply_slope(heightmap: List[List[float]], slope_strength: float) -> None:
	size = len(heightmap)
	for y in range(size):
		for x in range(size):
			heightmap[y][x] += slope_strength * (x / max(1, size - 1))


def _compute_slope_map(heightmap: List[List[float]], meters_per_pixel: float) -> List[List[float]]:
	size = len(heightmap)
	slope_map = [[0.0 for _ in range(size)] for _ in range(size)]
	for y in range(size):
		for x in range(size):
			left = heightmap[y][x - 1] if x > 0 else heightmap[y][x]
			right = heightmap[y][x + 1] if x < size - 1 else heightmap[y][x]
			down = heightmap[y - 1][x] if y > 0 else heightmap[y][x]
			up = heightmap[y + 1][x] if y < size - 1 else heightmap[y][x]
			dx = (right - left) / (2 * meters_per_pixel)
			dy = (up - down) / (2 * meters_per_pixel)
			slope_rad = math.atan(math.sqrt(dx * dx + dy * dy))
			slope_map[y][x] = math.degrees(slope_rad)
	return slope_map


def _terrain_profiles() -> Dict[str, Dict[str, Tuple[float, float]]]:
	return {
		"plains": {
			"roughness": (0.2, 0.35),
			"friction": (0.6, 0.8),
			"rock_density": (0.1, 0.3),
			"sand_density": (0.1, 0.3),
			"elevation": (1500, 1600),
			"amplitude": (4, 8),
		},
		"sand": {
			"roughness": (0.3, 0.5),
			"friction": (0.3, 0.5),
			"rock_density": (0.05, 0.2),
			"sand_density": (0.45, 0.8),
			"elevation": (1480, 1580),
			"amplitude": (6, 12),
		},
		"rocky": {
			"roughness": (0.55, 0.85),
			"friction": (0.65, 0.85),
			"rock_density": (0.5, 0.8),
			"sand_density": (0.05, 0.2),
			"elevation": (1520, 1650),
			"amplitude": (10, 18),
		},
		"crater": {
			"roughness": (0.4, 0.7),
			"friction": (0.5, 0.7),
			"rock_density": (0.2, 0.5),
			"sand_density": (0.2, 0.4),
			"elevation": (1400, 1520),
			"amplitude": (12, 20),
		},
		"slope": {
			"roughness": (0.45, 0.75),
			"friction": (0.55, 0.75),
			"rock_density": (0.3, 0.6),
			"sand_density": (0.1, 0.3),
			"elevation": (1550, 1700),
			"amplitude": (14, 24),
		},
	}


def _choose_terrain_type(rng: random.Random, complexity: float) -> str:
	weights = [
		("plains", 0.25 - complexity * 0.05),
		("sand", 0.22 + complexity * 0.05),
		("rocky", 0.25 + complexity * 0.1),
		("crater", 0.16 + complexity * 0.03),
		("slope", 0.12 + complexity * 0.07),
	]
	total = sum(w for _, w in weights)
	pick = rng.uniform(0, total)
	cumulative = 0.0
	for terrain_type, weight in weights:
		cumulative += weight
		if pick <= cumulative:
			return terrain_type
	return "plains"


def generate_heightmap(
	size: int,
	seed: int,
	roughness: float,
	terrain_type: str,
	base_elevation: float,
	amplitude: float,
	meters_per_pixel: float,
) -> List[List[float]]:
	rng = random.Random(seed)
	heightmap = [[0.0 for _ in range(size)] for _ in range(size)]
	octaves = 4 if terrain_type in {"rocky", "crater", "slope"} else 3
	for octave in range(octaves):
		grid_size = max(2, size // (2 ** (octave + 2)))
		noise = _value_noise(size, grid_size, rng)
		amp = amplitude / (2 ** octave)
		for y in range(size):
			for x in range(size):
				heightmap[y][x] += noise[y][x] * amp

	if terrain_type == "crater":
		_apply_crater(heightmap, depth=amplitude * 1.2)
	if terrain_type == "slope":
		_apply_slope(heightmap, slope_strength=amplitude * 0.8)

	# Smooth sand and plains to reduce roughness.
	if terrain_type in {"sand", "plains"}:
		passes = 2 if terrain_type == "sand" else 1
		heightmap = _apply_blur(heightmap, passes=passes)

	# Center around base elevation.
	for y in range(size):
		for x in range(size):
			heightmap[y][x] = base_elevation + heightmap[y][x]

	return heightmap


def _roughness_from_heightmap(heightmap: List[List[float]]) -> float:
	size = len(heightmap)
	flat = [heightmap[y][x] for y in range(size) for x in range(size)]
	mean = sum(flat) / max(1, len(flat))
	variance = sum((h - mean) ** 2 for h in flat) / max(1, len(flat))
	std_dev = math.sqrt(variance)
	# Normalize roughness to a 0-1 scale using a soft cap.
	return _clamp(std_dev / 20.0, 0.0, 1.0)


def _compute_traversability(
	slope_avg: float,
	roughness: float,
	rock_density: float,
	sand_density: float,
	terrain_type: str,
) -> float:
	score = 1.0
	score -= (slope_avg / 35.0) * 0.35
	score -= roughness * 0.25
	score -= rock_density * 0.2
	score -= sand_density * 0.2
	if terrain_type == "sand" and slope_avg > 12:
		score -= 0.08
	if terrain_type == "slope" and slope_avg > 18:
		score -= 0.1
	return _clamp(score, 0.05, 0.98)


def generate_traversability_map(
	slope_map: List[List[float]],
	roughness: float,
	rock_density: float,
	sand_density: float,
	size: int = 16,
) -> List[List[float]]:
	height_size = len(slope_map)
	step = max(1, height_size // size)
	output = [[0.0 for _ in range(size)] for _ in range(size)]
	for y in range(size):
		for x in range(size):
			total = 0.0
			count = 0
			for sy in range(y * step, min(height_size, (y + 1) * step)):
				for sx in range(x * step, min(height_size, (x + 1) * step)):
					total += slope_map[sy][sx]
					count += 1
			slope_avg = total / max(1, count)
			score = _compute_traversability(slope_avg, roughness, rock_density, sand_density, "")
			output[y][x] = round(score, 3)
	return output


def generate_terrain_tile(
	tile_id: str,
	latitude: float,
	longitude: float,
	config: Dict[str, float],
	seed: int,
) -> Tuple[Dict[str, object], List[List[float]], List[List[float]]]:
	rng = random.Random(seed)
	complexity = float(config.get("terrain_complexity", 0.6))
	meters_per_pixel = float(config.get("meters_per_pixel", 2.0))
	heightmap_size = int(config.get("heightmap_size", 64))
	tile_size_m = float(config.get("tile_size_m", heightmap_size * meters_per_pixel))

	terrain_type = _choose_terrain_type(rng, complexity)
	profiles = _terrain_profiles()[terrain_type]

	roughness = rng.uniform(*profiles["roughness"])
	friction = rng.uniform(*profiles["friction"])
	rock_density = rng.uniform(*profiles["rock_density"])
	sand_density = rng.uniform(*profiles["sand_density"])
	elevation_base = rng.uniform(*profiles["elevation"])
	amplitude = rng.uniform(*profiles["amplitude"]) * _clamp(0.8 + complexity * 0.6, 0.7, 1.4)

	heightmap = generate_heightmap(
		size=heightmap_size,
		seed=seed,
		roughness=roughness,
		terrain_type=terrain_type,
		base_elevation=elevation_base,
		amplitude=amplitude,
		meters_per_pixel=meters_per_pixel,
	)
	slope_map = _compute_slope_map(heightmap, meters_per_pixel)

	slope_values = [slope_map[y][x] for y in range(heightmap_size) for x in range(heightmap_size)]
	slope_avg = sum(slope_values) / max(1, len(slope_values))
	slope_max = max(slope_values) if slope_values else 0.0
	roughness_norm = _roughness_from_heightmap(heightmap)
	traversability = _compute_traversability(slope_avg, roughness_norm, rock_density, sand_density, terrain_type)

	soil_map = {
		"plains": "fine_regolith",
		"sand": "fine_regolith",
		"rocky": "coarse_regolith",
		"crater": "mixed_regolith",
		"slope": "coarse_regolith",
	}

	traversability_map = generate_traversability_map(
		slope_map=slope_map,
		roughness=roughness_norm,
		rock_density=rock_density,
		sand_density=sand_density,
	)

	tile = {
		"tile_id": tile_id,
		"coordinates": {
			"latitude": round(latitude, 4),
			"longitude": round(longitude, 4),
		},
		"terrain": {
			"terrain_type": terrain_type,
			"elevation": {
				"mean": round(elevation_base, 2),
				"variance": round((roughness_norm * 20) ** 2, 2),
			},
			"slope": {
				"average": round(slope_avg, 2),
				"max": round(slope_max, 2),
			},
			"roughness": round(roughness_norm, 3),
			"surface_friction": round(friction, 3),
			"traversability_score": round(traversability, 3),
			"soil_type": soil_map[terrain_type],
			"rock_density": round(rock_density, 3),
			"sand_density": round(sand_density, 3),
		},
		"tile_size_m": round(tile_size_m, 2),
		"heightmap_size": heightmap_size,
		"meters_per_pixel": meters_per_pixel,
	}

	return tile, heightmap, traversability_map


def validate_terrain_tile(tile: Dict[str, object]) -> None:
	terrain = tile["terrain"]
	for key in ("roughness", "surface_friction", "traversability_score", "rock_density", "sand_density"):
		value = float(terrain[key])
		if not (0.0 <= value <= 1.0):
			raise ValueError(f"{tile['tile_id']} invalid {key}: {value}")
	slope_avg = float(terrain["slope"]["average"])
	slope_max = float(terrain["slope"]["max"])
	if slope_avg < 0 or slope_max < 0:
		raise ValueError(f"{tile['tile_id']} invalid slope values")


def write_heightmap(heightmap: List[List[float]], path: str, meters_per_pixel: float) -> None:
	payload = {
		"meters_per_pixel": meters_per_pixel,
		"size": len(heightmap),
		"heights": [[round(value, 2) for value in row] for row in heightmap],
	}
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2)


def write_traversability_map(traversability_map: List[List[float]], path: str) -> None:
	payload = {
		"size": len(traversability_map),
		"map": traversability_map,
	}
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2)


def write_tile(tile: Dict[str, object], path: str) -> None:
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(tile, handle, indent=2)


def generate_terrain_tiles(
	rows: int,
	cols: int,
	config: Dict[str, float],
	seed: int,
	base_lat: float = -4.5,
	base_lon: float = 137.4,
) -> Tuple[List[Dict[str, object]], Dict[str, List[List[float]]], Dict[str, List[List[float]]]]:
	tiles: List[Dict[str, object]] = []
	heightmaps: Dict[str, List[List[float]]] = {}
	traversability_maps: Dict[str, List[List[float]]] = {}
	lat_step = float(config.get("lat_step", 0.02))
	lon_step = float(config.get("lon_step", 0.02))

	for row in range(rows):
		for col in range(cols):
			tile_id = f"mars_tile_r{row:02d}_c{col:02d}"
			tile_seed = _seed_for(seed, tile_id)
			latitude = base_lat + row * lat_step
			longitude = base_lon + col * lon_step
			tile, heightmap, traversability = generate_terrain_tile(
				tile_id=tile_id,
				latitude=latitude,
				longitude=longitude,
				config=config,
				seed=tile_seed,
			)
			validate_terrain_tile(tile)
			tiles.append(tile)
			heightmaps[tile_id] = heightmap
			traversability_maps[tile_id] = traversability

	return tiles, heightmaps, traversability_maps


def write_terrain_assets(
	tiles: List[Dict[str, object]],
	heightmaps: Dict[str, List[List[float]]],
	traversability_maps: Dict[str, List[List[float]]],
	output_dir: str,
) -> None:
	tiles_dir = os.path.join(output_dir, "terrain", "terrain_tiles")
	heightmaps_dir = os.path.join(output_dir, "terrain", "heightmaps")
	traversability_dir = os.path.join(output_dir, "terrain", "traversability_maps")
	os.makedirs(tiles_dir, exist_ok=True)
	os.makedirs(heightmaps_dir, exist_ok=True)
	os.makedirs(traversability_dir, exist_ok=True)

	for tile in tiles:
		tile_id = tile["tile_id"]
		heightmap_path = os.path.join(heightmaps_dir, f"{tile_id}.json")
		traversability_path = os.path.join(traversability_dir, f"{tile_id}.json")
		write_heightmap(heightmaps[tile_id], heightmap_path, tile["meters_per_pixel"])
		write_traversability_map(traversability_maps[tile_id], traversability_path)

		tile["heightmap_file"] = os.path.relpath(heightmap_path, output_dir)
		tile["traversability_file"] = os.path.relpath(traversability_path, output_dir)
		tile_path = os.path.join(tiles_dir, f"{tile_id}.json")
		write_tile(tile, tile_path)

