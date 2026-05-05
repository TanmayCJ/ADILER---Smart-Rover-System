"""Rover decision graph orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from agents.core.agent_state import get_rover_state_container
from agents.core.interrupt_handler import InterruptReason, get_interrupt_handler
from agents.environment_agent.environment_agent import environment_agent_node
from agents.memory_agent.memory_agent import memory_agent_node
from agents.navigation_agent.navigation_agent import navigation_agent_node
from agents.planner_agent.planner_agent import planner_agent_node

from .edges import (
	route_after_environment,
	route_after_memory,
	route_after_navigation,
	route_after_planning,
)
from .fanout import build_node_map

logger = logging.getLogger(__name__)

try:  # Optional dependency; the fallback runner below keeps the workflow usable without it.
	from langgraph.graph import END, StateGraph
except Exception:  # pragma: no cover - optional dependency path
	END = "__end__"
	StateGraph = None


@dataclass
class RoverWorkflowResult:
	"""Outcome of a rover workflow execution."""

	state: Dict[str, Any]
	iterations: int
	interrupted: bool
	reason: Optional[str]


class RoverDecisionGraph:
	"""Compiled LangGraph workflow with a deterministic fallback runner."""

	def __init__(self) -> None:
		self._node_map = build_node_map(
			environment_agent_node,
			planner_agent_node,
			navigation_agent_node,
			memory_agent_node,
		)
		self._compiled_graph = self._build_langgraph() if StateGraph is not None else None

	def _build_langgraph(self):
		graph = StateGraph(dict)
		graph.add_node("environment", self._node_map["environment"])
		graph.add_node("planner", self._node_map["planner"])
		graph.add_node("navigation", self._node_map["navigation"])
		graph.add_node("memory", self._node_map["memory"])

		graph.set_entry_point("environment")
		graph.add_edge("environment", "planner")
		graph.add_edge("planner", "navigation")
		graph.add_edge("navigation", "memory")

		graph.add_conditional_edges("environment", route_after_environment, {"planner": "planner"})
		graph.add_conditional_edges("planner", route_after_planning, {"navigation": "navigation", "memory": "memory"})
		graph.add_conditional_edges("navigation", route_after_navigation, {"planner": "planner", "memory": "memory"})
		graph.add_conditional_edges(
			"memory",
			route_after_memory,
			{"environment": "environment", "stop": END},
		)

		return graph.compile()

	def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
		if self._compiled_graph is not None:
			return self._compiled_graph.invoke(state)
		return self._run_fallback(state).state

	def _run_fallback(self, state: Dict[str, Any], max_iterations: Optional[int] = None) -> RoverWorkflowResult:
		interrupt_handler = get_interrupt_handler()
		state_container = get_rover_state_container(state)
		current_state = state_container.get_state()
		iterations = 0
		max_cycles = int(max_iterations or current_state.get("max_cycles", 1) or 1)

		while iterations < max_cycles:
			if interrupt_handler.check_interrupt():
				reason = interrupt_handler.get_interrupt_reason()
				current_state["loop_interrupted"] = True
				current_state["interrupt_reason"] = reason.value
				state_container.update(current_state)
				return RoverWorkflowResult(current_state, iterations, True, reason.value)

			current_state["cycle_count"] = int(current_state.get("cycle_count", 0)) + 1
			current_state["timestamp"] = datetime.now().isoformat()

			current_state.update(self._node_map["environment"](current_state))
			current_state.update(self._node_map["planner"](current_state))
			current_state.update(self._node_map["navigation"](current_state))
			current_state.update(self._node_map["memory"](current_state))

			iterations += 1
			state_container.set_state(current_state)

			if current_state.get("current_action") == "reached_goal":
				break
			if current_state.get("loop_interrupted"):
				break

		return RoverWorkflowResult(
			state=current_state,
			iterations=iterations,
			interrupted=bool(current_state.get("loop_interrupted")),
			reason=current_state.get("interrupt_reason"),
		)


def build_rover_graph() -> RoverDecisionGraph:
	"""Build the rover decision graph."""
	return RoverDecisionGraph()


def run_rover_decision_loop(initial_state: Optional[Dict[str, Any]] = None, max_iterations: Optional[int] = None) -> RoverWorkflowResult:
	"""Execute the rover decision loop using the compiled graph or fallback runner."""
	graph = build_rover_graph()
	state = initial_state or get_rover_state_container().get_state()
	if graph._compiled_graph is not None:
		final_state = graph._compiled_graph.invoke(state)
		return RoverWorkflowResult(
			state=final_state,
			iterations=int(final_state.get("cycle_count", 0)),
			interrupted=bool(final_state.get("loop_interrupted")),
			reason=final_state.get("interrupt_reason"),
		)
	return graph._run_fallback(state, max_iterations=max_iterations)
