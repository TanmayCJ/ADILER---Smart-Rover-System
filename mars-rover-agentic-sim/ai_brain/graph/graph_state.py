"""Shared workflow state for the ai_brain agents."""

from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class RoverWorkflowState(TypedDict, total=False):
	"""Minimal state container passed between agents."""

	scenario_id: str
	terrain_tile: Dict[str, Any]
	wind_series: List[Dict[str, Any]]
	hazards: Dict[str, Any]
	mission: Dict[str, Any]
	rover_state: Dict[str, Any]
	environment_state: Dict[str, Any]
	decisions: List[Dict[str, Any]]
	memory: Dict[str, Any]

