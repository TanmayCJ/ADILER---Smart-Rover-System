"""Tests for multi-scenario LangGraph execution."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


pytest.importorskip("langgraph")

from ai_brain.graph.langgraph_rover_graph import run_langgraph_workflow
from scripts.run_langgraph_multi import _evaluate_expectations, _validate_schema


ALLOWED_ACTIONS = {"proceed", "proceed_cautious", "hold"}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_state(base: Path, scenario_name: str):
    scenario = _load_json(base / "scenarios" / f"{scenario_name}.json")
    tile_id = scenario["tile_id"]
    mission_id = scenario["mission_id"]

    terrain_tile = _load_json(base / "terrain" / "terrain_tiles" / f"{tile_id}.json")
    wind_payload = _load_json(base / "weather" / "wind_fields" / f"{tile_id}.json")
    hazards = _load_json(base / "hazards" / f"{tile_id}.json")
    mission = _load_json(base / "missions" / f"{mission_id}.json")
    sim_state = _load_json(base / "generated" / "simulation_states" / f"{scenario_name}.json")
    first_state = sim_state.get("states", [{}])[0] if sim_state.get("states") else {}

    return {
        "scenario_id": scenario["scenario_id"],
        "terrain_tile": terrain_tile,
        "wind_series": wind_payload.get("series", []),
        "hazards": hazards,
        "mission": mission,
        "rover_state": first_state.get("rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}}),
        "decisions": [],
        "memory": {"events": []},
    }


def test_multi_scenario_execution():
    base = Path(__file__).resolve().parents[1] / "scripts" / "synthetic_data_full"
    scenarios = sorted(p.stem for p in (base / "scenarios").glob("*.json"))
    assert scenarios

    for scenario_name in scenarios:
        state = _build_state(base, scenario_name)
        result = run_langgraph_workflow(state)
        assert result.get("environment_state")
        assert result.get("plan")
        assert result.get("rover_state")
        assert result.get("memory", {}).get("events")
        action = result.get("plan", {}).get("action")
        assert action in ALLOWED_ACTIONS


def test_memory_event_growth():
    base = Path(__file__).resolve().parents[1] / "scripts" / "synthetic_data_full"
    state = _build_state(base, "easy_navigation")
    result = run_langgraph_workflow(state)
    assert len(result.get("memory", {}).get("events", [])) == 1


def test_missing_optional_fields():
    minimal_state = {
        "scenario_id": "minimal",
        "mission": {"mission": {"goal_position": [1.0, 1.0]}},
        "rover_state": {"position": {"x": 0.0, "y": 0.0, "z": 0.0}},
        "decisions": [],
        "memory": {"events": []},
    }
    result = run_langgraph_workflow(minimal_state)
    assert result.get("environment_state")
    assert result.get("plan")
    assert result.get("memory", {}).get("events")


def test_validate_schema_success():
    schema = {
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    }
    errors = _validate_schema(schema, {"id": "scenario_1"})
    assert errors == []


def test_validate_schema_failure():
    schema = {
        "type": "object",
        "required": ["id"],
        "properties": {"id": {"type": "string"}},
    }
    errors = _validate_schema(schema, {"name": "missing"})
    assert errors


def test_expectations_failure_reason():
    expectations = {
        "scenario_a": {
            "risk_min": 0.2,
            "risk_max": 0.4,
            "allowed_actions": ["hold"],
            "movement_expected": True,
            "memory_required": True,
        }
    }
    reasons = _evaluate_expectations(
        "scenario_a",
        expectations,
        risk_score=0.9,
        planner_action="proceed",
        initial_pos={"x": 0.0, "y": 0.0},
        final_pos={"x": 0.0, "y": 0.0},
        memory_events=0,
    )
    assert reasons
    assert any("risk" in reason for reason in reasons)
    assert any("action" in reason for reason in reasons)
    assert any("movement expected" in reason for reason in reasons)
    assert any("memory" in reason for reason in reasons)
