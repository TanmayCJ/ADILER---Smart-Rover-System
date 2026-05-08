"""Synthetic dataset builder for Mars rover simulation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from generators.hazard_generator import generate_hazards, validate_hazards, write_hazards
from generators.mission_generator import generate_missions
from generators.rover_state_generator import generate_rover_states, validate_rover_states
from generators.terrain_generator import generate_terrain_tiles, write_terrain_assets
from generators.wind_generator import generate_wind_series, summarize_wind, validate_wind_series, write_atmosphere_profile, write_wind_series


@dataclass
class DatasetConfig:
	output_dir: str
	seed: int = 42
	tile_rows: int = 2
	tile_cols: int = 2
	heightmap_size: int = 64
	meters_per_pixel: float = 2.0
	tile_size_m: float = 128.0
	terrain_complexity: float = 0.6
	hazard_density: float = 0.4
	wind_intensity: float = 0.6
	sim_duration_sec: int = 600
	dt_sec: float = 0.5
	missions_per_tile: int = 1
	scenario_names: List[str] = field(
		default_factory=lambda: [
			"easy_navigation",
			"rocky_terrain",
			"high_wind_navigation",
			"dust_storm_escape",
			"energy_critical_route",
		]
	)


def _ensure_dirs(output_dir: str) -> None:
	for subdir in (
		"terrain/terrain_tiles",
		"terrain/heightmaps",
		"terrain/traversability_maps",
		"weather/wind_fields",
		"weather/dust_events",
		"weather/atmosphere_profiles",
		"hazards",
		"rover/battery_profiles",
		"rover/motor_profiles",
		"rover/wheel_profiles",
		"missions",
		"scenarios",
		"generated/simulation_states",
		"generated/telemetry_logs",
		"generated/event_streams",
	):
		os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)


def _write_json(path: str, payload: Dict[str, object]) -> None:
	with open(path, "w", encoding="utf-8") as handle:
		json.dump(payload, handle, indent=2)


def _load_json(path: str) -> Dict[str, object]:
	with open(path, "r", encoding="utf-8") as handle:
		return json.load(handle)


def _index_by_id(items: List[Dict[str, object]], key: str) -> Dict[str, Dict[str, object]]:
	return {item[key]: item for item in items}


def build_terrain_assets(config: DatasetConfig) -> Tuple[List[Dict[str, object]], Dict[str, List[List[float]]], Dict[str, List[List[float]]]]:
	terrain_config = {
		"heightmap_size": config.heightmap_size,
		"meters_per_pixel": config.meters_per_pixel,
		"tile_size_m": config.tile_size_m,
		"terrain_complexity": config.terrain_complexity,
	}
	return generate_terrain_tiles(config.tile_rows, config.tile_cols, terrain_config, config.seed)


def build_weather_assets(
	config: DatasetConfig,
	tiles: List[Dict[str, object]],
) -> Dict[str, List[Dict[str, object]]]:
	wind_index: Dict[str, List[Dict[str, object]]] = {}
	for tile in tiles:
		series = generate_wind_series(
			tile=tile,
			duration_sec=config.sim_duration_sec,
			dt_sec=config.dt_sec,
			seed=config.seed,
			intensity=config.wind_intensity,
		)
		validate_wind_series(series)
		wind_index[tile["tile_id"]] = series
	return wind_index


def build_hazard_assets(
	config: DatasetConfig,
	tiles: List[Dict[str, object]],
) -> Tuple[Dict[str, Dict[str, object]], Dict[str, Dict[str, float]]]:
	hazard_index: Dict[str, Dict[str, object]] = {}
	hazard_summary: Dict[str, Dict[str, float]] = {}
	for tile in tiles:
		hazards, summary = generate_hazards(tile, config.seed, config.hazard_density)
		validate_hazards(hazards)
		hazard_index[tile["tile_id"]] = hazards
		hazard_summary[tile["tile_id"]] = summary
	return hazard_index, hazard_summary


def build_mission_assets(
	config: DatasetConfig,
	tiles: List[Dict[str, object]],
	hazard_summary: Dict[str, Dict[str, float]],
) -> List[Dict[str, object]]:
	per_tile = max(1, config.missions_per_tile)
	summary_density = {tile_id: data["hazard_density"] for tile_id, data in hazard_summary.items()}
	return generate_missions(tiles, summary_density, config.seed, missions_per_tile=per_tile)


def build_scenarios(
	config: DatasetConfig,
	tiles: List[Dict[str, object]],
	missions: List[Dict[str, object]],
	hazard_summary: Dict[str, Dict[str, float]],
	wind_index: Dict[str, List[Dict[str, object]]],
) -> List[Dict[str, object]]:
	tiles_by_id = _index_by_id(tiles, "tile_id")
	missions_by_id = {mission["mission"]["mission_id"]: mission for mission in missions}

	def pick_tile(predicate):
		for tile in tiles:
			if predicate(tile):
				return tile
		return tiles[0]

	scenarios = []
	for name in config.scenario_names:
		if name == "easy_navigation":
			tile = pick_tile(lambda t: t["terrain"]["traversability_score"] > 0.7)
			wind_scale = 0.3
			hazard_scale = 0.25
		elif name == "rocky_terrain":
			tile = pick_tile(lambda t: t["terrain"]["terrain_type"] == "rocky")
			wind_scale = 0.5
			hazard_scale = 0.7
		elif name == "high_wind_navigation":
			tile = pick_tile(lambda t: t["terrain"]["traversability_score"] > 0.5)
			wind_scale = 0.9
			hazard_scale = 0.4
		elif name == "dust_storm_escape":
			tile = pick_tile(lambda t: t["terrain"]["terrain_type"] in {"sand", "crater"})
			wind_scale = 1.0
			hazard_scale = 0.5
		else:  # energy_critical_route
			tile = pick_tile(lambda t: t["terrain"]["traversability_score"] < 0.7)
			wind_scale = 0.6
			hazard_scale = 0.5

		mission = next(m for m in missions if m["tile_id"] == tile["tile_id"])
		hazard_info = hazard_summary[tile["tile_id"]]
		wind_summary = summarize_wind(wind_index[tile["tile_id"]])

		scenario = {
			"scenario_id": name,
			"description": f"Scenario {name.replace('_', ' ')}",
			"tile_id": tile["tile_id"],
			"mission_id": mission["mission"]["mission_id"],
			"parameters": {
				"hazard_density": round(hazard_scale, 3),
				"wind_intensity": round(wind_scale, 3),
				"duration_sec": config.sim_duration_sec,
				"dt_sec": config.dt_sec,
			},
			"preload": {
				"wind": wind_summary,
				"hazards": hazard_info,
				"terrain_type": tile["terrain"]["terrain_type"],
			},
		}
		scenarios.append(scenario)

	return scenarios


def _environment_snapshot(
	tile: Dict[str, object],
	wind_entry: Dict[str, object],
	hazard_summary: Dict[str, float],
) -> Dict[str, object]:
	terrain = tile["terrain"]
	wind = wind_entry["wind"]
	max_risk = "low"
	if hazard_summary["sand_trap_count"] > 5 or hazard_summary["slope_count"] > 1:
		max_risk = "medium"
	if hazard_summary["sand_trap_count"] > 8 or hazard_summary["slope_count"] > 2:
		max_risk = "high"

	return {
		"terrain": {
			"tile_id": tile["tile_id"],
			"terrain_type": terrain["terrain_type"],
			"slope_avg": terrain["slope"]["average"],
			"roughness": terrain["roughness"],
			"traversability_score": terrain["traversability_score"],
		},
		"wind": wind,
		"hazards": {
			"rock_count": hazard_summary["rock_count"],
			"sand_trap_count": hazard_summary["sand_trap_count"],
			"slope_count": hazard_summary["slope_count"],
			"risk_level": max_risk,
		},
		"atmosphere": wind_entry["atmosphere"],
	}


def generate_simulation_states(
	config: DatasetConfig,
	scenarios: List[Dict[str, object]],
	tiles: List[Dict[str, object]],
	missions: List[Dict[str, object]],
	wind_index: Dict[str, List[Dict[str, object]]],
	hazard_summary: Dict[str, Dict[str, float]],
) -> None:
	tiles_by_id = _index_by_id(tiles, "tile_id")
	missions_by_id = {mission["mission"]["mission_id"]: mission for mission in missions}

	for scenario in scenarios:
		tile = tiles_by_id[scenario["tile_id"]]
		mission = missions_by_id[scenario["mission_id"]]
		wind_series = wind_index[tile["tile_id"]]
		rover_states = generate_rover_states(
			mission=mission,
			terrain=tile,
			wind_series=wind_series,
			duration_sec=config.sim_duration_sec,
			dt_sec=config.dt_sec,
			seed=config.seed,
		)
		validate_rover_states(rover_states)

		states: List[Dict[str, object]] = []
		telemetry: List[Dict[str, object]] = []
		events: List[Dict[str, object]] = []
		total_steps = len(rover_states)
		for idx, rover_entry in enumerate(rover_states):
			wind_entry = wind_series[min(idx, len(wind_series) - 1)]
			env_state = _environment_snapshot(tile, wind_entry, hazard_summary[tile["tile_id"]])
			mission_state = {
				"mission_id": mission["mission"]["mission_id"],
				"goal_position": mission["mission"]["goal_position"],
				"progress": round(min(1.0, idx / max(1, total_steps - 1)), 3),
			}
			state = {
				"timestamp": rover_entry["timestamp"],
				"rover_state": rover_entry["rover_state"],
				"environment_state": env_state,
				"mission_state": mission_state,
			}
			states.append(state)

			telemetry.append(
				{
					"timestamp": rover_entry["timestamp"],
					"battery": rover_entry["rover_state"]["battery"]["percentage"],
					"velocity": rover_entry["rover_state"]["velocity"],
					"traction": rover_entry["rover_state"]["wheels"]["traction"],
					"slippage": rover_entry["rover_state"]["wheels"]["slippage"],
					"wind_speed": wind_entry["wind"]["speed"],
				}
			)

			# Event stream: concise alerts for agent memory or visualization.
			if idx % int(60 / max(config.dt_sec, 0.1)) == 0:
				events.append({"timestamp": rover_entry["timestamp"], "type": "memory_snapshot"})
			if rover_entry["rover_state"]["wheels"]["slippage"] > 0.55:
				events.append({"timestamp": rover_entry["timestamp"], "type": "traction_drop"})
			if wind_entry["wind"]["speed"] > 18:
				events.append({"timestamp": rover_entry["timestamp"], "type": "wind_gust"})
			if rover_entry["rover_state"]["battery"]["percentage"] < 30:
				events.append({"timestamp": rover_entry["timestamp"], "type": "battery_warning"})

		sim_path = os.path.join(config.output_dir, "generated", "simulation_states", f"{scenario['scenario_id']}.json")
		telemetry_path = os.path.join(config.output_dir, "generated", "telemetry_logs", f"{scenario['scenario_id']}.json")
		events_path = os.path.join(config.output_dir, "generated", "event_streams", f"{scenario['scenario_id']}.json")
		_write_json(sim_path, {"scenario_id": scenario["scenario_id"], "states": states})
		_write_json(telemetry_path, {"scenario_id": scenario["scenario_id"], "telemetry": telemetry})
		_write_json(events_path, {"scenario_id": scenario["scenario_id"], "events": events})


def build_full_dataset(config: DatasetConfig) -> Dict[str, object]:
	_ensure_dirs(config.output_dir)
	tiles, heightmaps, traversability_maps = build_terrain_assets(config)
	write_terrain_assets(tiles, heightmaps, traversability_maps, config.output_dir)

	wind_index = build_weather_assets(config, tiles)
	for tile_id, series in wind_index.items():
		write_wind_series(tile_id, series, config.output_dir)
		write_atmosphere_profile(tile_id, series, config.output_dir)

	hazard_index, hazard_summary = build_hazard_assets(config, tiles)
	for tile_id, hazards in hazard_index.items():
		write_hazards(tile_id, hazards, config.output_dir)

	missions = build_mission_assets(config, tiles, hazard_summary)
	for mission in missions:
		path = os.path.join(config.output_dir, "missions", f"{mission['mission']['mission_id']}.json")
		_write_json(path, mission)

	scenarios = build_scenarios(config, tiles, missions, hazard_summary, wind_index)
	for scenario in scenarios:
		path = os.path.join(config.output_dir, "scenarios", f"{scenario['scenario_id']}.json")
		_write_json(path, scenario)

	generate_simulation_states(config, scenarios, tiles, missions, wind_index, hazard_summary)

	return {
		"tiles": len(tiles),
		"missions": len(missions),
		"scenarios": len(scenarios),
	}


def generate_simulation_states_from_files(config: DatasetConfig) -> None:
	scenarios_dir = os.path.join(config.output_dir, "scenarios")
	scenarios = []
	for name in os.listdir(scenarios_dir):
		if name.endswith(".json"):
			scenarios.append(_load_json(os.path.join(scenarios_dir, name)))

	tiles_dir = os.path.join(config.output_dir, "terrain", "terrain_tiles")
	tiles = [_load_json(os.path.join(tiles_dir, name)) for name in os.listdir(tiles_dir) if name.endswith(".json")]

	missions_dir = os.path.join(config.output_dir, "missions")
	missions = [_load_json(os.path.join(missions_dir, name)) for name in os.listdir(missions_dir) if name.endswith(".json")]

	wind_dir = os.path.join(config.output_dir, "weather", "wind_fields")
	wind_index = {}
	for name in os.listdir(wind_dir):
		if name.endswith(".json"):
			payload = _load_json(os.path.join(wind_dir, name))
			wind_index[payload["tile_id"]] = payload["series"]

	hazards_dir = os.path.join(config.output_dir, "hazards")
	hazard_summary = {}
	for name in os.listdir(hazards_dir):
		if name.endswith(".json"):
			hazard = _load_json(os.path.join(hazards_dir, name))
			counts = {"rock_count": 0, "sand_trap_count": 0, "slope_count": 0, "hazard_density": config.hazard_density}
			for obstacle in hazard.get("obstacles", []):
				if obstacle["type"] == "rock":
					counts["rock_count"] += 1
				elif obstacle["type"] == "sand_trap":
					counts["sand_trap_count"] += 1
				elif obstacle["type"] == "slope":
					counts["slope_count"] += 1
			hazard_summary[hazard["tile_id"]] = counts

	generate_simulation_states(config, scenarios, tiles, missions, wind_index, hazard_summary)

