"""Registry for agent node callables."""

from __future__ import annotations

from typing import Callable, Dict

from ai_brain.agents.environment_agent.node import environment_node
from ai_brain.agents.memory_agent.node import memory_node
from ai_brain.agents.navigation_agent.node import navigation_node
from ai_brain.agents.planner_agent.node import planner_node

NodeFn = Callable[[Dict[str, object]], Dict[str, object]]


def build_node_registry() -> Dict[str, NodeFn]:
	"""Return the default node registry."""

	return {
		"environment": environment_node,
		"planner": planner_node,
		"navigation": navigation_node,
		"memory": memory_node,
	}

