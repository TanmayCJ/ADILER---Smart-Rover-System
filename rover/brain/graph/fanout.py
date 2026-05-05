"""Fan-out helpers for rover workflows."""

from __future__ import annotations

from typing import Any, Callable, Dict


NodeFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def build_node_map(
	environment_node: NodeFn,
	planner_node: NodeFn,
	navigation_node: NodeFn,
	memory_node: NodeFn,
) -> Dict[str, NodeFn]:
	"""Return a stable node map for the rover decision loop."""
	return {
		"environment": environment_node,
		"planner": planner_node,
		"navigation": navigation_node,
		"memory": memory_node,
	}
