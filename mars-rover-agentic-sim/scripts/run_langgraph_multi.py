"""Run LangGraph workflow across all synthetic scenarios."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import yaml
from jsonschema import Draft202012Validator


def _add_repo_root() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _load_json(path: Path) -> Dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _format_pos(pos: Dict[str, object]) -> str:
    if not pos:
        return "-"
    return f"({pos.get('x', 0.0):.2f}, {pos.get('y', 0.0):.2f})"


def _write_report(report_dir: Path, rows: List[Dict[str, object]], markdown: bool) -> Dict[str, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "langgraph_multi_report.json"
    json_path.write_text(json.dumps({"results": rows}, indent=2), encoding="utf-8")

    markdown_path = report_dir / "langgraph_multi_report.md"
    if markdown:
        lines = [
            "# LangGraph Multi-Scenario Report",
            "",
            "| Scenario | Risk | Action | Initial | Final | Memory | Status | Reason |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in rows:
            lines.append(
                "| {scenario} | {risk_score} | {planner_action} | {initial_pos} | {final_pos} | {memory_events} | {status} | {reason} |".format(
                    scenario=row["scenario"],
                    risk_score=row.get("risk_score", "-"),
                    planner_action=row.get("planner_action", "-"),
                    initial_pos=row.get("initial_pos", "-"),
                    final_pos=row.get("final_pos", "-"),
                    memory_events=row.get("memory_events", "-"),
                    status=row.get("status", "-"),
                    reason=row.get("reason", "-"),
                )
            )
        markdown_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path if markdown else None}


def _load_schema(schema_dir: Path, name: str) -> Dict[str, object]:
    return _load_json(schema_dir / name)


def _validate_schema(schema: Dict[str, object], payload: Dict[str, object]) -> List[str]:
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(payload)]


def _load_expectations(expectations_path: Path) -> Dict[str, object]:
    if not expectations_path.exists():
        return {}
    return yaml.safe_load(expectations_path.read_text(encoding="utf-8")) or {}


def _movement_distance(initial_pos: Dict[str, object], final_pos: Dict[str, object]) -> float:
    if not initial_pos or not final_pos:
        return 0.0
    dx = float(final_pos.get("x", 0.0)) - float(initial_pos.get("x", 0.0))
    dy = float(final_pos.get("y", 0.0)) - float(initial_pos.get("y", 0.0))
    return (dx ** 2 + dy ** 2) ** 0.5


def _evaluate_expectations(
    scenario_id: str,
    expectations: Dict[str, object],
    risk_score: float | None,
    planner_action: str | None,
    initial_pos: Dict[str, object],
    final_pos: Dict[str, object],
    memory_events: int,
) -> List[str]:
    rules = expectations.get(scenario_id) or {}
    reasons: List[str] = []

    if risk_score is None:
        reasons.append("missing risk score")
    else:
        risk_min = float(rules.get("risk_min", 0.0))
        risk_max = float(rules.get("risk_max", 1.0))
        if not (risk_min <= risk_score <= risk_max):
            reasons.append(f"risk {risk_score} outside [{risk_min}, {risk_max}]")

    allowed_actions = set(rules.get("allowed_actions", []))
    if allowed_actions and (planner_action not in allowed_actions):
        reasons.append(f"action {planner_action} not allowed")

    movement_expected = bool(rules.get("movement_expected", False))
    moved = _movement_distance(initial_pos, final_pos) > 0.01
    if movement_expected and not moved:
        reasons.append("movement expected but rover did not move")

    memory_required = bool(rules.get("memory_required", False))
    if memory_required and memory_events <= 0:
        reasons.append("memory event required but missing")

    return reasons


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LangGraph workflow for all scenarios")
    parser.add_argument("--data-dir", default="scripts/synthetic_data_full")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--expectations", default="config/scenario_expectations.yaml")
    args = parser.parse_args()

    repo_root = _add_repo_root()
    data_dir = (repo_root / args.data_dir).resolve()
    scenario_dir = data_dir / "scenarios"
    if not scenario_dir.exists():
        raise FileNotFoundError(f"Scenario directory not found: {scenario_dir}")

    from ai_brain.graph.langgraph_rover_graph import run_langgraph_workflow

    schema_dir = repo_root / "shared" / "schemas"
    schemas = {
        "scenario": _load_schema(schema_dir, "scenario.schema.json"),
        "terrain": _load_schema(schema_dir, "terrain.schema.json"),
        "wind": _load_schema(schema_dir, "wind.schema.json"),
        "hazard": _load_schema(schema_dir, "hazard.schema.json"),
        "mission": _load_schema(schema_dir, "mission.schema.json"),
        "rover_state": _load_schema(schema_dir, "rover_state.schema.json"),
        "workflow": _load_schema(schema_dir, "workflow_result.schema.json"),
    }
    expectations = _load_expectations(repo_root / args.expectations)

    scenario_paths = sorted(scenario_dir.glob("*.json"))
    rows: List[Dict[str, object]] = []

    for scenario_path in scenario_paths:
        scenario = _load_json(scenario_path)
        tile_id = scenario["tile_id"]
        mission_id = scenario["mission_id"]

        terrain_tile = _load_json(data_dir / "terrain" / "terrain_tiles" / f"{tile_id}.json")
        wind_payload = _load_json(data_dir / "weather" / "wind_fields" / f"{tile_id}.json")
        hazards = _load_json(data_dir / "hazards" / f"{tile_id}.json")
        mission = _load_json(data_dir / "missions" / f"{mission_id}.json")

        sim_state_path = data_dir / "generated" / "simulation_states" / f"{scenario['scenario_id']}.json"
        sim_states = _load_json(sim_state_path) if sim_state_path.exists() else {"states": []}
        first_state = sim_states.get("states", [{}])[0] if sim_states.get("states") else {}

        rover_state = first_state.get("rover_state", {"position": {"x": 0.0, "y": 0.0, "z": 0.0}})
        initial_pos = rover_state.get("position", {})

        initial_state = {
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

        result_row = {
            "scenario": scenario["scenario_id"],
            "risk_score": None,
            "planner_action": None,
            "initial_pos": _format_pos(initial_pos),
            "final_pos": None,
            "memory_events": 0,
            "status": "failed",
            "error": None,
            "reason": None,
        }

        try:
            schema_errors: List[str] = []
            schema_errors += _validate_schema(schemas["scenario"], scenario)
            schema_errors += _validate_schema(schemas["terrain"], terrain_tile)
            schema_errors += _validate_schema(schemas["wind"], wind_payload)
            schema_errors += _validate_schema(schemas["hazard"], hazards)
            schema_errors += _validate_schema(schemas["mission"], mission)
            schema_errors += _validate_schema(schemas["rover_state"], rover_state)
            if schema_errors:
                result_row["status"] = "failed"
                result_row["reason"] = "; ".join(schema_errors[:3])
                rows.append(result_row)
                continue

            final_state = run_langgraph_workflow(initial_state)
            env_state = final_state.get("environment_state", {})
            plan = final_state.get("plan", {})
            rover_state = final_state.get("rover_state", {})
            memory_events = final_state.get("memory", {}).get("events", [])

            result_row["risk_score"] = env_state.get("risk_score")
            result_row["planner_action"] = plan.get("action")
            result_row["final_pos"] = _format_pos(rover_state.get("position", {}))
            result_row["memory_events"] = len(memory_events)

            workflow_errors = _validate_schema(schemas["workflow"], final_state)
            if workflow_errors:
                result_row["status"] = "failed"
                result_row["reason"] = "; ".join(workflow_errors[:3])
                rows.append(result_row)
                continue

            expectation_reasons = _evaluate_expectations(
                scenario["scenario_id"],
                expectations,
                result_row["risk_score"],
                result_row["planner_action"],
                initial_pos,
                rover_state.get("position", {}),
                len(memory_events),
            )
            if expectation_reasons:
                result_row["status"] = "failed"
                result_row["reason"] = "; ".join(expectation_reasons)
            else:
                result_row["status"] = "passed"
                result_row["reason"] = "ok"
        except Exception as exc:
            result_row["status"] = "failed"
            result_row["error"] = str(exc)
            result_row["reason"] = str(exc)

        rows.append(result_row)

    header = f"{'Scenario':<22} {'Risk':<6} {'Action':<16} {'Initial':<16} {'Final':<16} {'Memory':<6} {'Status':<7} {'Reason'}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['scenario']:<22} "
            f"{str(row.get('risk_score') or '-'): <6} "
            f"{str(row.get('planner_action') or '-'): <16} "
            f"{row.get('initial_pos', '-'): <16} "
            f"{row.get('final_pos') or '-': <16} "
            f"{str(row.get('memory_events') or 0): <6} "
            f"{row.get('status', '-'): <7} "
            f"{row.get('reason', '-') or '-'}"
        )

    reports = _write_report(repo_root / "reports", rows, args.markdown)
    print(f"JSON report: {reports['json']}")
    if reports["markdown"]:
        print(f"Markdown report: {reports['markdown']}")


if __name__ == "__main__":
    main()
