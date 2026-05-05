"""Routing helpers for the rover decision graph."""

from __future__ import annotations

from typing import Any, Dict


def route_after_environment(state: Dict[str, Any]) -> str:
	"""Route from environment analysis to the planner."""
	return "planner"


def route_after_planning(state: Dict[str, Any]) -> str:
	"""Route after planning; navigation only proceeds when a route exists."""
	if state.get("planned_route"):
		return "navigation"
	return "memory"


def route_after_navigation(state: Dict[str, Any]) -> str:
	"""Route after navigation based on current action."""
	if state.get("current_action") == "reached_goal":
		return "memory"
	if state.get("current_action") == "replan_required":
		return "planner"
	return "memory"


def route_after_memory(state: Dict[str, Any]) -> str:
	"""Route after memory consolidation to continue or stop the loop."""
	if state.get("loop_interrupted"):
		return "stop"
	if int(state.get("cycle_count", 0)) >= int(state.get("max_cycles", 0) or 0):
		return "stop"
	if state.get("current_action") == "reached_goal":
		return "stop"
	return "environment"


def route_on_interrupt(state: Dict[str, Any]) -> str:
	"""Route immediately to stop when an interrupt is detected."""
	return "stop"
