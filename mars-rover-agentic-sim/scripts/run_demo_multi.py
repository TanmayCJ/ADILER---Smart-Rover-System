"""Run multiple scenarios with step-by-step, presentation-friendly output."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple


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


def _risk_level(risk_score: float) -> str:
    if risk_score >= 0.7:
        return "high"
    if risk_score >= 0.45:
        return "moderate"
    return "low"


def _print_section(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _apply_scenario_overrides(
    scenario: Dict[str, object],
    wind_payload: Dict[str, object],
    hazards: Dict[str, object],
) -> Tuple[Dict[str, object], Dict[str, object]]:
    params = scenario.get("parameters", {})
    wind_intensity = float(params.get("wind_intensity", 1.0))
    hazard_density = _clamp(float(params.get("hazard_density", 1.0)))

    adjusted_wind_series = []
    for entry in wind_payload.get("series", []):
        wind = dict(entry.get("wind", {}))
        if "speed" in wind:
            wind["speed"] = round(float(wind.get("speed", 0.0)) * wind_intensity, 2)
        if "dust_density" in wind:
            wind["dust_density"] = round(
                _clamp(float(wind.get("dust_density", 0.0)) * wind_intensity), 3
            )
        adjusted_entry = dict(entry)
        adjusted_entry["wind"] = wind
        adjusted_wind_series.append(adjusted_entry)

    adjusted_wind_payload = dict(wind_payload)
    adjusted_wind_payload["series"] = adjusted_wind_series

    obstacles = list(hazards.get("obstacles", []))
    target_count = int(round(len(obstacles) * hazard_density))
    if hazard_density > 0.0 and target_count == 0:
        target_count = 1
    adjusted_hazards = dict(hazards)
    adjusted_hazards["obstacles"] = obstacles[:target_count]

    return adjusted_wind_payload, adjusted_hazards


def _scenario_header(scenario_id: str) -> None:
    print("\n" + ("=" * 72))
    print(f"SCENARIO: {scenario_id}")
    print("=" * 72)


def _write_reports(report_dir: Path, results: List[Dict[str, object]]) -> Dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "demo_agent_run.json"
    json_path.write_text(json.dumps({"scenarios": results}, indent=2), encoding="utf-8")

    markdown_path = report_dir / "demo_agent_run.md"
    lines = ["# Mars Rover LangGraph Demo Run", ""]
    for result in results:
        lines.append(f"## Scenario: {result['scenario_id']}")
        if result.get("status") != "passed":
            lines.append(f"Status: FAILED - {result.get('failure_reason')}")
            lines.append("")
            continue
        lines.extend(
            [
                "1. Scenario Loaded",
                f"Mission: {result['scenario_loaded']['mission_id']}",
                f"Start: {result['scenario_loaded']['start']}",
                f"Goal: {result['scenario_loaded']['goal']}",
                f"Terrain Tile: {result['scenario_loaded']['terrain_tile']}",
                "",
                "2. Environment Agent Output",
                f"Risk Score: {result['environment']['risk_score']}",
                f"Slope: {result['environment']['slope']}",
                f"Roughness: {result['environment']['roughness']}",
                f"Wind Speed: {result['environment']['wind_speed']}",
                f"Dust Level: {result['environment']['dust_level']}",
                f"Obstacle Count: {result['environment']['obstacle_count']}",
                f"Risk Level: {result['environment']['risk_level']}",
                "",
                "3. Planner/Aggregator Agent Output",
                f"Selected Action: {result['planner']['action']}",
                f"Rationale: {result['planner']['rationale']}",
                "",
                "4. Navigation Agent Output",
                f"Initial Position: {result['navigation']['initial_position']}",
                f"Final Position: {result['navigation']['final_position']}",
                f"Movement Step: {result['navigation']['movement_step']}",
                f"Navigation Status: {result['navigation']['status']}",
                "",
                "5. Memory Agent Output",
                f"Memory Events Written: {result['memory']['events_written']}",
                f"Latest Memory Event: {result['memory']['latest_event']}",
                "",
                "6. Final Verdict",
                result["final_verdict"],
                "",
            ]
        )

    lines.append("## Scenario Comparison")
    lines.append("")
    lines.append("| Scenario | Risk Score | Wind | Dust | Obstacles | Action | Status |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- |")
    for result in results:
        environment = result.get("environment", {})
        planner = result.get("planner", {})
        lines.append(
            "| {scenario} | {risk_score} | {wind} | {dust} | {obstacles} | {action} | {status} |".format(
                scenario=result.get("scenario_id"),
                risk_score=environment.get("risk_score", "-"),
                wind=environment.get("wind_speed", "-"),
                dust=environment.get("dust_level", "-"),
                obstacles=environment.get("obstacle_count", "-"),
                action=planner.get("action", "-"),
                status=result.get("status", "-"),
            )
        )

    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a demo for multiple scenarios")
    parser.add_argument("--data-dir", default="scripts/synthetic_data_full")
    parser.add_argument("--scenario", action="append")
    args = parser.parse_args()

    scenarios = args.scenario or [
        "easy_navigation",
        "high_wind_navigation",
        "dust_storm_escape",
        "rocky_terrain",
        "energy_critical_route",
    ]

    repo_root = _add_repo_root()
    from ai_brain.agents.environment_agent.node import environment_node
    from ai_brain.agents.memory_agent.node import memory_node
    from ai_brain.agents.navigation_agent.node import navigation_node
    from ai_brain.agents.planner_agent.node import planner_node

    data_dir = (repo_root / args.data_dir).resolve()
    report_dir = repo_root / "reports"

    results: List[Dict[str, object]] = []
    failed: List[str] = []

    for scenario_id in scenarios:
        _scenario_header(scenario_id)
        result: Dict[str, object] = {"scenario_id": scenario_id, "status": "failed"}
        try:
            scenario_path = data_dir / "scenarios" / f"{scenario_id}.json"
            if not scenario_path.exists():
                raise FileNotFoundError(f"Scenario not found: {scenario_path}")

            scenario = _load_json(scenario_path)
            tile_id = scenario["tile_id"]
            mission_id = scenario["mission_id"]

            terrain_tile = _load_json(data_dir / "terrain" / "terrain_tiles" / f"{tile_id}.json")
            wind_payload = _load_json(data_dir / "weather" / "wind_fields" / f"{tile_id}.json")
            hazards = _load_json(data_dir / "hazards" / f"{tile_id}.json")
            mission = _load_json(data_dir / "missions" / f"{mission_id}.json")

            sim_state_path = data_dir / "generated" / "simulation_states" / f"{scenario_id}.json"
            sim_states = _load_json(sim_state_path) if sim_state_path.exists() else {"states": []}
            first_state = sim_states.get("states", [{}])[0] if sim_states.get("states") else {}

            wind_payload, hazards = _apply_scenario_overrides(scenario, wind_payload, hazards)

            rover_state = first_state.get(
                "rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}}
            )

            state: Dict[str, object] = {
                "scenario_id": scenario_id,
                "terrain_tile": terrain_tile,
                "wind_series": wind_payload.get("series", []),
                "hazards": hazards,
                "mission": mission,
                "rover_state": rover_state,
                "environment_state": first_state.get("environment_state", {}),
                "decisions": [],
                "memory": {"events": []},
            }

            _print_section("1. Scenario Loaded")
            start_pos = mission.get("mission", {}).get("start_position", [0.0, 0.0])
            goal_pos = mission.get("mission", {}).get("goal_position", [0.0, 0.0])
            print(f"Mission: {mission_id}")
            print(f"Start: ({start_pos[0]:.2f}, {start_pos[1]:.2f})")
            print(f"Goal: ({goal_pos[0]:.2f}, {goal_pos[1]:.2f})")
            print(f"Terrain Tile: {tile_id}")

            _print_section("2. Environment Agent Output")
            state = _merge_state(state, environment_node(state))
            env = state.get("environment_state", {})
            risk_score = float(env.get("risk_score", 0.0))
            risk_level = _risk_level(risk_score)
            print(f"Risk Score: {risk_score}")
            print(f"Slope: {env.get('slope_avg')}")
            print(f"Roughness: {env.get('roughness')}")
            print(f"Wind Speed: {env.get('wind_speed')}")
            print(f"Dust Level: {env.get('dust_density')}")
            print(f"Obstacle Count: {env.get('obstacle_count')}")
            print(f"Risk Level: {risk_level}")

            _print_section("3. Planner/Aggregator Agent Output")
            state = _merge_state(state, planner_node(state))
            plan = state.get("plan", {})
            if risk_score >= 0.7:
                rationale = "high risk, holding position"
            elif risk_score >= 0.45:
                rationale = "moderate risk, proceed cautiously"
            else:
                rationale = "low risk, proceed"
            print(f"Selected Action: {plan.get('action')}")
            print(f"Rationale: {rationale}")

            _print_section("4. Navigation Agent Output")
            before_pos = state.get("rover_state", {}).get("position", {})
            state = _merge_state(state, navigation_node(state))
            after_pos = state.get("rover_state", {}).get("position", {})
            step_m = state.get("rover_state", {}).get("velocity", 0.0)
            nav_status = "moved" if step_m and step_m > 0.0 else "held"
            print(f"Initial Position: {_format_pos(before_pos)}")
            print(f"Final Position: {_format_pos(after_pos)}")
            print(f"Movement Step: {step_m} meters")
            print(f"Navigation Status: {nav_status}")

            _print_section("5. Memory Agent Output")
            state = _merge_state(state, memory_node(state))
            memory_events = state.get("memory", {}).get("events", [])
            latest_event = memory_events[-1] if memory_events else None
            print(f"Memory Events Written: {len(memory_events)}")
            print(f"Latest Memory Event: {latest_event}")

            _print_section("6. Final Verdict")
            remaining = _distance(after_pos, {"x": goal_pos[0], "y": goal_pos[1]})
            action = plan.get("action")
            if action == "hold":
                verdict = "Hold position due to elevated risk."
            elif action == "proceed_cautious":
                verdict = "Proceed cautiously toward the goal."
            else:
                verdict = "Proceed toward the goal."
            print(verdict)

            result.update(
                {
                    "status": "passed",
                    "scenario_loaded": {
                        "mission_id": mission_id,
                        "start": f"({start_pos[0]:.2f}, {start_pos[1]:.2f})",
                        "goal": f"({goal_pos[0]:.2f}, {goal_pos[1]:.2f})",
                        "terrain_tile": tile_id,
                    },
                    "environment": {
                        "risk_score": risk_score,
                        "slope": env.get("slope_avg"),
                        "roughness": env.get("roughness"),
                        "wind_speed": env.get("wind_speed"),
                        "dust_level": env.get("dust_density"),
                        "obstacle_count": env.get("obstacle_count"),
                        "risk_level": risk_level,
                    },
                    "planner": {"action": plan.get("action"), "rationale": rationale},
                    "navigation": {
                        "initial_position": _format_pos(before_pos),
                        "final_position": _format_pos(after_pos),
                        "movement_step": f"{step_m} meters",
                        "status": nav_status,
                    },
                    "memory": {
                        "events_written": len(memory_events),
                        "latest_event": latest_event,
                    },
                    "final_verdict": verdict,
                    "distance_to_goal": round(remaining, 2),
                }
            )
        except Exception as exc:
            result["status"] = "failed"
            result["failure_reason"] = str(exc)
            failed.append(scenario_id)
            print(f"FAILED: {exc}")

        results.append(result)

    report_paths = _write_reports(report_dir, results)

    print("\n" + ("=" * 72))
    print("Demo Summary")
    print("=" * 72)
    print(f"Scenarios executed: {', '.join(scenarios)}")
    print(
        f"Reports generated: {report_paths['markdown']} , {report_paths['json']}"
    )
    if failed:
        print(f"Failed scenarios: {', '.join(failed)}")
    else:
        print("Failed scenarios: none")

    rerun_args = " ".join(f"--scenario {scenario}" for scenario in scenarios)
    print(
        "Command to rerun: python scripts/run_demo_multi.py "
        f"{rerun_args}".strip()
    )


if __name__ == "__main__":
    main()
