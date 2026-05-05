"""Scenario runner design for the rover agentic system.

This is a lightweight skeleton meant for manual execution and extension.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("OLLAMA_FORCE_CPU", "1")

from agents.shared.llm_client import get_llama_client

from agents.workflows import execute_rover_decision_loop

from tests.schemas import OUTPUT_SCHEMA, SCENARIO_SCHEMA
from tests.validators.action_validator import validate_action
from tests.validators.decision_validator import validate_decision
from tests.validators.risk_validator import validate_risk


SCENARIO_DIR = Path(__file__).parent / "scenarios"
BASE_URL = os.environ.get("ROVER_BACKEND_URL", "http://localhost:8000")
REPORT_DIR = Path(__file__).parent / "reports"
REPORT_PATH = REPORT_DIR / "scenario_report.md"
SCENARIO_LIMIT = int(os.environ.get("SCENARIO_LIMIT", "10"))
THRESHOLD_ONLY = os.environ.get("THRESHOLD_ONLY", "0") == "1"
REPORT_PATH = REPORT_DIR / ("scenario_report_threshold.md" if THRESHOLD_ONLY else "scenario_report.md")


def load_scenarios() -> List[Dict[str, Any]]:
    scenarios = []
    for scenario_path in sorted(SCENARIO_DIR.glob("*.json")):
        scenarios.append(json.loads(scenario_path.read_text(encoding="utf-8")))

    filter_ids = os.environ.get("SCENARIO_IDS", "").strip()
    if not filter_ids:
        return scenarios[:SCENARIO_LIMIT]

    allowed = {item.strip() for item in filter_ids.split(",") if item.strip()}
    return [scenario for scenario in scenarios if scenario.get("scenario_id") in allowed][:SCENARIO_LIMIT]


def call_backend_terrain(terrain_query: Dict[str, Any]) -> Dict[str, Any]:
    """Call /api/v1/terrain/elevation with the scenario payload.
    """
    endpoint = terrain_query["endpoint"]
    payload = terrain_query["request"]
    url = f"{BASE_URL}{endpoint}"

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def call_backend_wind(wind_query: Dict[str, Any]) -> Dict[str, Any]:
    """Call /api/v1/wind/query with the scenario payload.
    """
    endpoint = wind_query["endpoint"]
    payload = wind_query["request"]
    url = f"{BASE_URL}{endpoint}"

    request = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def build_initial_state(scenario: Dict[str, Any], terrain_response: Dict[str, Any], wind_response: Dict[str, Any]) -> Dict[str, Any]:
    """Construct RoverState-compatible initial state from scenario + backend responses."""
    initial_state = scenario["initial_state"]
    terrain_payload = scenario["environment_inputs"].get("terrain_enrichment", {})
    enrichment = terrain_payload.get("payload", {})

    rover_position = {
        "latitude": initial_state["rover_position"]["latitude"],
        "longitude": initial_state["rover_position"]["longitude"],
        "elevation_m": initial_state["rover_position"]["elevation_m"],
    }

    return {
        "rover_position": rover_position,
        "rover_heading": initial_state["heading"],
        "rover_velocity": 0.2,
        "current_goal": {
            "latitude": initial_state["goal_position"]["latitude"],
            "longitude": initial_state["goal_position"]["longitude"],
            "name": initial_state["goal_position"]["name"],
            "priority": initial_state["goal_position"]["priority"],
        },
        "planned_route": [],
        "current_waypoint_index": 0,
        "current_action": "init",
        "terrain_data": {
            "slope_deg": enrichment.get("slope_deg", 0.0),
            "terrain_type": enrichment.get("terrain_type", "unknown"),
            "roughness": enrichment.get("roughness", 0.0),
            "obstacles": enrichment.get("obstacles", []),
            "center_latitude": initial_state["rover_position"]["latitude"],
            "center_longitude": initial_state["rover_position"]["longitude"],
        },
        "wind_data": {
            "speed_mps": wind_response["point"]["wind_speed_mps"],
            "direction_deg": wind_response["point"].get("wind_direction_deg", 0.0),
            "gust_speed_mps": wind_response["point"].get("gust_speed_mps", wind_response["point"]["wind_speed_mps"]),
        },
        "hazard_map": {},
        "environment_summary": "",
        "memory_context": {
            "recent_experiences": [],
            "learned_hazards": [],
            "success_patterns": [],
            "failure_patterns": [],
        },
        "hazard_memory": initial_state.get("hazard_memory", []),
        "route_history": [],
        "experience_buffer": [],
        "cycle_count": 0,
        "timestamp": "",
        "loop_interrupted": False,
        "interrupt_reason": None,
        "max_cycles": 1,
        "llm_calls": 0,
        "error_log": [],
    }


def validate_scenario(scenario: Dict[str, Any], output: Dict[str, Any]) -> List[str]:
    """Run all validators and collect error messages."""
    errors: List[str] = []
    errors += validate_risk(scenario, output)
    errors += validate_decision(scenario, output)
    errors += validate_action(scenario, output)
    return errors


def summarize_output(output: Dict[str, Any]) -> Dict[str, Any]:
    state = output["workflow_result"]["state"]
    hazard_map = output["agent_outputs"]["environment_analysis"].get("hazard_map", {})
    return {
        "risk_score": hazard_map.get("risk_score"),
        "current_action": state.get("current_action"),
        "planned_route_length": len(state.get("planned_route", [])),
        "waypoint_index": state.get("current_waypoint_index"),
        "loop_interrupted": state.get("loop_interrupted"),
        "interrupt_reason": state.get("interrupt_reason"),
    }


def _strip_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```") and cleaned.endswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return cleaned


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def get_threshold_reasoning(
    scenario: Dict[str, Any],
    output: Dict[str, Any],
    errors: List[str],
) -> str:
    summary = summarize_output(output)
    status = "PASS" if not errors else "FAIL"
    risk_score = summary.get("risk_score")
    current_action = summary.get("current_action")
    expected = scenario["expected_behavior"]

    if status == "PASS":
        return (
            f"PASS: risk_score={risk_score} and current_action={current_action} "
            f"match expected_risk_level={expected['expected_risk_level']} and expected_action={expected['expected_action']}."
        )

    return (
        f"FAIL: risk_score={risk_score} and current_action={current_action} "
        f"did not meet expected_risk_level={expected['expected_risk_level']} or expected_action={expected['expected_action']}."
    )


def get_next_plan_llm(scenario: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, Any]:
    llm_client = get_llama_client(model="llama3.1")
    state = output["workflow_result"]["state"]
    prompt = json.dumps(
        {
            "scenario_id": scenario["scenario_id"],
            "risk_score": state.get("hazard_map", {}).get("risk_score"),
            "current_action": state.get("current_action"),
            "terrain": state.get("terrain_data"),
            "wind": state.get("wind_data"),
            "planned_route": state.get("planned_route"),
        },
        indent=2,
    )
    llm_response = llm_client.invoke(
        prompt=prompt,
        system_prompt=(
            "Return JSON with keys: next_action (move|rotate|stop|hold|detour), "
            "confidence (0.0-1.0), adjustments {speed_factor, heading_offset_deg}, "
            "risk_mitigation (array of short strings). Return ONLY JSON."
        ),
        temperature=0.1,
        max_tokens=120,
    )

    cleaned = _strip_code_fences(str(llm_response))
    for candidate in (cleaned, _extract_json_object(cleaned)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    return {"next_action": "hold", "confidence": 0.0, "adjustments": {}, "risk_mitigation": []}


def run_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    terrain_response = call_backend_terrain(scenario["environment_inputs"]["terrain_query"])
    wind_response = call_backend_wind(scenario["environment_inputs"]["wind_query"])

    state = build_initial_state(scenario, terrain_response, wind_response)
    result = execute_rover_decision_loop(initial_state=state, max_iterations=1)

    output = {
        "scenario_id": scenario["scenario_id"],
        "workflow_result": {
            "state": result.state,
            "iterations": result.iterations,
            "interrupted": result.interrupted,
            "reason": result.reason,
        },
        "agent_outputs": {
            "environment_analysis": {
                "hazard_map": result.state.get("hazard_map", {}),
                "terrain_data": result.state.get("terrain_data", {}),
                "wind_data": result.state.get("wind_data", {}),
            },
            "planner_output": {
                "planned_route": result.state.get("planned_route", []),
                "current_action": result.state.get("current_action", ""),
                "route_history": result.state.get("route_history", []),
            },
            "navigation_output": {
                "current_action": result.state.get("current_action", ""),
                "rover_position": result.state.get("rover_position", {}),
                "rover_velocity": result.state.get("rover_velocity", 0.0),
            },
            "memory_output": {
                "memory_context": result.state.get("memory_context", {}),
                "hazard_memory": result.state.get("hazard_memory", []),
                "experience_buffer": result.state.get("experience_buffer", []),
            },
        },
        "execution_trace": [],
    }

    return output


def write_report(rows: List[Tuple[str, str, List[str], str, Dict[str, Any]]]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    lines = ["# Scenario Test Report", ""]
    for scenario_id, status, errors, reasoning, next_plan in rows:
        lines.append(f"## {scenario_id}")
        lines.append(f"Status: {status}")
        lines.append("Errors:")
        if errors:
            for error in errors:
                lines.append(f"- {error}")
        else:
            lines.append("- None")
        lines.append("Threshold Reasoning:")
        lines.append(reasoning.strip() or "(No response)")
        lines.append("Next Plan (LLM):")
        lines.append(json.dumps(next_plan, indent=2))
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    scenarios = load_scenarios()
    report_rows: List[Tuple[str, str, List[str], str, Dict[str, Any]]] = []
    for scenario in scenarios:
        output = run_scenario(scenario)
        errors = validate_scenario(scenario, output)
        name = scenario["scenario_id"]
        if errors:
            print(f"[Scenario: {name}] FAIL")
            for error in errors:
                print(f"- {error}")
            status = "FAIL"
        else:
            print(f"[Scenario: {name}] PASS")
            status = "PASS"

        reasoning = get_threshold_reasoning(scenario, output, errors)
        next_plan = {}
        if status == "FAIL" and not THRESHOLD_ONLY:
            next_plan = get_next_plan_llm(scenario, output)
        report_rows.append((name, status, errors, reasoning, next_plan))

    write_report(report_rows)
    print(f"Report saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
