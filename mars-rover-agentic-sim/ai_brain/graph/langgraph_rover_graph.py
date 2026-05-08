"""LangGraph workflow wrapper for rover agents."""

from __future__ import annotations

from typing import Dict

from ai_brain.agents.environment_agent.node import environment_node
from ai_brain.agents.memory_agent.node import memory_node
from ai_brain.agents.navigation_agent.node import navigation_node
from ai_brain.agents.planner_agent.node import planner_node


def _wrap(node_fn):
    """Merge node updates into the incoming state."""

    def _merged(state: Dict[str, object]) -> Dict[str, object]:
        updates = node_fn(state)
        merged = dict(state)
        merged.update(updates)
        return merged

    return _merged


def build_langgraph():
    """Build and compile the LangGraph workflow."""

    from langgraph.graph import END, StateGraph

    graph = StateGraph(dict)
    graph.add_node("environment", _wrap(environment_node))
    graph.add_node("planner", _wrap(planner_node))
    graph.add_node("navigation", _wrap(navigation_node))
    graph.add_node("memory", _wrap(memory_node))

    graph.set_entry_point("environment")
    graph.add_edge("environment", "planner")
    graph.add_edge("planner", "navigation")
    graph.add_edge("navigation", "memory")
    graph.add_edge("memory", END)

    return graph.compile()


def run_langgraph_workflow(state: Dict[str, object]) -> Dict[str, object]:
    """Execute the LangGraph workflow and return the final state."""

    workflow = build_langgraph()
    return workflow.invoke(state)
