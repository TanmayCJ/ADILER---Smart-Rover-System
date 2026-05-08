"""Tests for the minimal agent workflow."""

from __future__ import annotations

import json
from pathlib import Path

from ai_brain.graph.rover_graph import run_agent_workflow


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_agent_workflow_runs():
    base = Path(__file__).resolve().parents[1] / "scripts" / "synthetic_data_full"
    scenario = _load_json(base / "scenarios" / "easy_navigation.json")
    tile_id = scenario["tile_id"]
    mission_id = scenario["mission_id"]

    terrain_tile = _load_json(base / "terrain" / "terrain_tiles" / f"{tile_id}.json")
    wind_payload = _load_json(base / "weather" / "wind_fields" / f"{tile_id}.json")
    hazards = _load_json(base / "hazards" / f"{tile_id}.json")
    mission = _load_json(base / "missions" / f"{mission_id}.json")
    sim_state = _load_json(base / "generated" / "simulation_states" / "easy_navigation.json")
    first_state = sim_state.get("states", [{}])[0] if sim_state.get("states") else {}

    initial_state = {
        "scenario_id": scenario["scenario_id"],
        "terrain_tile": terrain_tile,
        "wind_series": wind_payload.get("series", []),
        "hazards": hazards,
        "mission": mission,
        "rover_state": first_state.get("rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}}),
        "decisions": [],
        "memory": {"events": []},
    }

    result = run_agent_workflow(initial_state)
    assert result.get("environment_state")
    assert result.get("plan")
    assert result.get("rover_state")
    assert result.get("memory", {}).get("events")
