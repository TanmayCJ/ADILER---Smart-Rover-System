"""Run a minimal agent workflow against synthetic datasets."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict


def _add_repo_root() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal agent workflow")
    parser.add_argument("--data-dir", default="scripts/synthetic_data_full")
    parser.add_argument("--scenario", default="easy_navigation")
    args = parser.parse_args()

    repo_root = _add_repo_root()
    data_dir = (repo_root / args.data_dir).resolve()

    scenario_path = data_dir / "scenarios" / f"{args.scenario}.json"
    if not scenario_path.exists():
        raise FileNotFoundError(f"Scenario not found: {scenario_path}")

    scenario = _load_json(scenario_path)
    tile_id = scenario["tile_id"]
    mission_id = scenario["mission_id"]

    terrain_tile = _load_json(data_dir / "terrain" / "terrain_tiles" / f"{tile_id}.json")
    wind_payload = _load_json(data_dir / "weather" / "wind_fields" / f"{tile_id}.json")
    hazards = _load_json(data_dir / "hazards" / f"{tile_id}.json")
    mission = _load_json(data_dir / "missions" / f"{mission_id}.json")

    sim_state_path = data_dir / "generated" / "simulation_states" / f"{args.scenario}.json"
    sim_states = _load_json(sim_state_path) if sim_state_path.exists() else {"states": []}
    first_state = sim_states.get("states", [{}])[0] if sim_states.get("states") else {}

    initial_state = {
        "scenario_id": scenario["scenario_id"],
        "terrain_tile": terrain_tile,
        "wind_series": wind_payload.get("series", []),
        "hazards": hazards,
        "mission": mission,
        "rover_state": first_state.get("rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}}),
        "environment_state": first_state.get("environment_state", {}),
        "decisions": [],
        "memory": {"events": []},
    }

    from ai_brain.graph.rover_graph import run_agent_workflow

    final_state = run_agent_workflow(initial_state)

    rover_position = final_state.get("rover_state", {}).get("position", {})
    print("Scenario:", final_state.get("scenario_id"))
    print("Risk score:", final_state.get("environment_state", {}).get("risk_score"))
    print("Planner action:", final_state.get("plan", {}).get("action"))
    print("Rover position:", rover_position)
    print("Memory events:", len(final_state.get("memory", {}).get("events", [])))


if __name__ == "__main__":
    main()
