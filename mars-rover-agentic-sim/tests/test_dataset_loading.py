"""Tests for synthetic dataset loading."""

from __future__ import annotations

import json
from pathlib import Path


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_scenario_files_exist():
    base = Path(__file__).resolve().parents[1] / "scripts" / "synthetic_data_full"
    scenario_path = base / "scenarios" / "easy_navigation.json"
    assert scenario_path.exists()

    scenario = _load_json(scenario_path)
    assert "tile_id" in scenario
    assert "mission_id" in scenario

    tile_path = base / "terrain" / "terrain_tiles" / f"{scenario['tile_id']}.json"
    mission_path = base / "missions" / f"{scenario['mission_id']}.json"
    wind_path = base / "weather" / "wind_fields" / f"{scenario['tile_id']}.json"
    hazard_path = base / "hazards" / f"{scenario['tile_id']}.json"

    assert tile_path.exists()
    assert mission_path.exists()
    assert wind_path.exists()
    assert hazard_path.exists()


def test_simulation_state_structure():
    base = Path(__file__).resolve().parents[1] / "scripts" / "synthetic_data_full"
    sim_path = base / "generated" / "simulation_states" / "easy_navigation.json"
    assert sim_path.exists()

    payload = _load_json(sim_path)
    assert "states" in payload
    assert isinstance(payload["states"], list)
    assert payload["states"]
    sample = payload["states"][0]
    assert "rover_state" in sample
    assert "environment_state" in sample
