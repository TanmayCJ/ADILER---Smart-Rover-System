"""JSON schemas for agentic rover scenario tests."""

from __future__ import annotations

SCENARIO_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "RoverAgentScenario",
    "type": "object",
    "required": [
        "scenario_id",
        "description",
        "initial_state",
        "environment_inputs",
        "expected_behavior",
        "validation_rules",
    ],
    "properties": {
        "scenario_id": {"type": "string"},
        "description": {"type": "string"},
        "initial_state": {
            "type": "object",
            "required": ["rover_position", "heading", "goal_position"],
            "properties": {
                "rover_position": {
                    "type": "object",
                    "required": ["latitude", "longitude", "elevation_m"],
                    "properties": {
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                        "elevation_m": {"type": "number"},
                    },
                },
                "heading": {"type": "number", "minimum": 0, "maximum": 360},
                "goal_position": {
                    "type": "object",
                    "required": ["latitude", "longitude", "name", "priority"],
                    "properties": {
                        "latitude": {"type": "number", "minimum": -90, "maximum": 90},
                        "longitude": {"type": "number", "minimum": -180, "maximum": 180},
                        "name": {"type": "string"},
                        "priority": {"type": "integer", "minimum": 0, "maximum": 10},
                    },
                },
                "hazard_memory": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["hazard_type", "severity", "location", "recommendation"],
                        "properties": {
                            "hazard_type": {"type": "string"},
                            "severity": {"type": "number", "minimum": 0, "maximum": 1},
                            "location": {
                                "type": "object",
                                "required": ["lat", "lon"],
                                "properties": {
                                    "lat": {"type": "number", "minimum": -90, "maximum": 90},
                                    "lon": {"type": "number", "minimum": -180, "maximum": 180},
                                },
                            },
                            "recommendation": {"type": "string"},
                        },
                    },
                },
            },
        },
        "environment_inputs": {
            "type": "object",
            "required": ["terrain_query", "wind_query"],
            "properties": {
                "terrain_query": {
                    "type": "object",
                    "required": ["endpoint", "request"],
                    "properties": {
                        "endpoint": {"type": "string"},
                        "request": {
                            "type": "object",
                            "required": ["latitude", "longitude"],
                            "properties": {
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"},
                                "dataset_id": {"type": ["string", "null"]},
                            },
                        },
                    },
                },
                "wind_query": {
                    "type": "object",
                    "required": ["endpoint", "request"],
                    "properties": {
                        "endpoint": {"type": "string"},
                        "request": {
                            "type": "object",
                            "required": ["latitude", "longitude"],
                            "properties": {
                                "latitude": {"type": "number"},
                                "longitude": {"type": "number"},
                                "sol": {"type": ["integer", "null"]},
                                "timestamp_utc": {"type": ["string", "null"]},
                                "dataset_id": {"type": ["string", "null"]},
                            },
                        },
                    },
                },
                "terrain_enrichment": {
                    "type": "object",
                    "required": ["source", "fallback", "payload"],
                    "properties": {
                        "source": {"type": "string", "enum": ["derived", "fallback"]},
                        "fallback": {"type": "boolean"},
                        "method": {"type": "string"},
                        "payload": {
                            "type": "object",
                            "properties": {
                                "slope_deg": {"type": "number"},
                                "terrain_type": {"type": "string"},
                                "roughness": {"type": "number", "minimum": 0, "maximum": 1},
                                "obstacles": {"type": "array"},
                            },
                        },
                    },
                },
            },
        },
        "expected_behavior": {
            "type": "object",
            "required": ["expected_risk_level", "expected_decision_type", "expected_action"],
            "properties": {
                "expected_risk_level": {"type": "string"},
                "expected_decision_type": {"type": "string"},
                "expected_action": {"type": "string"},
            },
        },
        "validation_rules": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "description", "when", "assert"],
                "properties": {
                    "id": {"type": "string"},
                    "description": {"type": "string"},
                    "when": {
                        "type": "object",
                        "required": ["field", "op", "value"],
                        "properties": {
                            "field": {"type": "string"},
                            "op": {"type": "string", "enum": [">", ">=", "<", "<=", "==", "!="]},
                            "value": {},
                        },
                    },
                    "assert": {
                        "type": "object",
                        "required": ["field", "op", "value"],
                        "properties": {
                            "field": {"type": "string"},
                            "op": {"type": "string", "enum": [">", ">=", "<", "<=", "==", "!=", "in", "not_in"]},
                            "value": {},
                        },
                    },
                },
            },
        },
    },
}

OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "RoverAgentScenarioOutput",
    "type": "object",
    "required": ["scenario_id", "workflow_result", "agent_outputs", "execution_trace"],
    "properties": {
        "scenario_id": {"type": "string"},
        "workflow_result": {
            "type": "object",
            "required": ["state", "iterations", "interrupted", "reason"],
            "properties": {
                "state": {"type": "object"},
                "iterations": {"type": "integer"},
                "interrupted": {"type": "boolean"},
                "reason": {"type": ["string", "null"]},
            },
        },
        "agent_outputs": {
            "type": "object",
            "required": ["environment_analysis", "planner_output", "navigation_output", "memory_output"],
            "properties": {
                "environment_analysis": {
                    "type": "object",
                    "required": ["hazard_map", "terrain_data", "wind_data"],
                    "properties": {
                        "hazard_map": {"type": "object"},
                        "terrain_data": {"type": "object"},
                        "wind_data": {"type": "object"},
                    },
                },
                "planner_output": {
                    "type": "object",
                    "required": ["planned_route", "current_action"],
                    "properties": {
                        "planned_route": {"type": "array"},
                        "current_action": {"type": "string"},
                        "route_history": {"type": "array"},
                    },
                },
                "navigation_output": {
                    "type": "object",
                    "required": ["current_action", "rover_position"],
                    "properties": {
                        "current_action": {"type": "string"},
                        "rover_position": {"type": "object"},
                        "rover_velocity": {"type": "number"},
                    },
                },
                "memory_output": {
                    "type": "object",
                    "required": ["memory_context", "hazard_memory", "experience_buffer"],
                    "properties": {
                        "memory_context": {"type": "object"},
                        "hazard_memory": {"type": "array"},
                        "experience_buffer": {"type": "array"},
                    },
                },
            },
        },
        "execution_trace": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["agent", "input_summary", "output_summary"],
                "properties": {
                    "agent": {"type": "string"},
                    "input_summary": {"type": "object"},
                    "output_summary": {"type": "object"},
                },
            },
        },
    },
}
