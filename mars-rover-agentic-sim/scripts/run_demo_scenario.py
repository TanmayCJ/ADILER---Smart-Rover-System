"""Run a single scenario with step-by-step, presentation-friendly output."""

from __future__ import annotations

import argparse
import json
import math
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


def _merge_state(state: Dict[str, object], updates: Dict[str, object]) -> Dict[str, object]:
    merged = dict(state)
    merged.update(updates)
    return merged


def _format_pos(pos: Dict[str, object]) -> str:
    if not pos:
        return "-"
    return f"({pos.get('x', 0.0):.2f}, {pos.get('y', 0.0):.2f})"


def _distance(a: Dict[str, object], b: Dict[str, object]) -> float:
    dx = float(b.get("x", 0.0)) - float(a.get("x", 0.0))
    dy = float(b.get("y", 0.0)) - float(a.get("y", 0.0))
    return math.sqrt(dx * dx + dy * dy)


def _print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a demo scenario step-by-step")
    parser.add_argument("--data-dir", default="scripts/synthetic_data_full")
    parser.add_argument("--scenario", default="easy_navigation")
    args = parser.parse_args()

    repo_root = _add_repo_root()
    from ai_brain.agents.environment_agent.node import environment_node
    from ai_brain.agents.memory_agent.node import memory_node
    from ai_brain.agents.navigation_agent.node import navigation_node
    from ai_brain.agents.planner_agent.node import planner_node
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

    rover_state = first_state.get("rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}})

    state: Dict[str, object] = {
        "scenario_id": scenario["scenario_id"],
        "terrain_tile": terrain_tile,
        "wind_series": wind_payload.get("series", []),
        "hazards": hazards,
        "mission": mission,
        "rover_state": rover_state,
        "environment_state": first_state.get("environment_state", {}),
        "decisions": [],
        "memory": {"events": []},
    }

    _print_section("1) Scenario loaded")
    start_pos = mission.get("mission", {}).get("start_position", [0.0, 0.0])
    goal_pos = mission.get("mission", {}).get("goal_position", [0.0, 0.0])
    print(f"Scenario: {scenario.get('scenario_id')}")
    print(f"Tile: {tile_id}")
    print(f"Mission: {mission_id}")
    print(f"Start: ({start_pos[0]:.2f}, {start_pos[1]:.2f})")
    print(f"Goal: ({goal_pos[0]:.2f}, {goal_pos[1]:.2f})")

    _print_section("2) Environment analysis")
    state = _merge_state(state, environment_node(state))
    env = state.get("environment_state", {})
    print(f"Risk score: {env.get('risk_score')}")
    print(
        "Signals: slope={slope_avg}, roughness={roughness}, wind={wind_speed}, "
        "dust={dust_density}, obstacles={obstacle_count}".format(
            slope_avg=env.get("slope_avg"),
            roughness=env.get("roughness"),
            wind_speed=env.get("wind_speed"),
            dust_density=env.get("dust_density"),
            obstacle_count=env.get("obstacle_count"),
        )
    )

    _print_section("3) Planner decision")
    state = _merge_state(state, planner_node(state))
    plan = state.get("plan", {})
    risk_score = float(plan.get("risk_score", 0.0))
    if risk_score >= 0.7:
        rationale = "high risk, holding position"
    elif risk_score >= 0.45:
        rationale = "moderate risk, proceed cautiously"
    else:
        rationale = "low risk, proceed"
    print(f"Action: {plan.get('action')}")
    print(f"Rationale: {rationale}")

    _print_section("4) Navigation result")
    before_pos = state.get("rover_state", {}).get("position", {})
    state = _merge_state(state, navigation_node(state))
    after_pos = state.get("rover_state", {}).get("position", {})
    step_m = state.get("rover_state", {}).get("velocity", 0.0)
    print(f"From: {_format_pos(before_pos)}")
    print(f"To:   {_format_pos(after_pos)}")
    print(f"Step: {step_m} meters")

    _print_section("5) Memory update")
    state = _merge_state(state, memory_node(state))
    memory_events = state.get("memory", {}).get("events", [])
    print(f"Total events: {len(memory_events)}")
    if memory_events:
        print(f"Latest event: {memory_events[-1]}")

    _print_section("6) Final verdict")
    remaining = _distance(after_pos, {"x": goal_pos[0], "y": goal_pos[1]})
    action = plan.get("action")
    if action == "hold":
        verdict = "Hold position due to elevated risk."
    elif action == "proceed_cautious":
        verdict = "Proceed cautiously toward the goal."
    else:
        verdict = "Proceed toward the goal."
    print(verdict)
    print(f"Distance to goal: {remaining:.2f} meters")


if __name__ == "__main__":
    main()
