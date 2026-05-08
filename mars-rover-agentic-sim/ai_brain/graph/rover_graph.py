"""Minimal rover agent workflow graph runner."""

from __future__ import annotations

from typing import Dict

from ai_brain.graph.graph_router import route_next
from ai_brain.graph.node_registry import build_node_registry


def run_agent_workflow(state: Dict[str, object]) -> Dict[str, object]:
	"""Execute a single pass through the agent workflow."""

	node_registry = build_node_registry()
	current = "environment"
	while current != "end":
		node_fn = node_registry.get(current)
		if node_fn is None:
			break
		updates = node_fn(state)
		state.update(updates)
		current = route_next(state, current)
	return state

