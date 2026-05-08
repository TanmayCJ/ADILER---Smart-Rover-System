"""Deterministic router for the minimal agent workflow."""

from __future__ import annotations

from typing import Dict


def route_next(state: Dict[str, object], current: str) -> str:
	"""Return the next node name for the workflow."""

	order = ["environment", "planner", "navigation", "memory", "end"]
	if current not in order:
		return "end"
	idx = order.index(current)
	return order[min(idx + 1, len(order) - 1)]

