"""Top-level rover decision loop workflow entry point."""

from __future__ import annotations

from typing import Any, Dict, Optional

from rover.brain.graph.rover_graph import RoverDecisionGraph, RoverWorkflowResult, build_rover_graph, run_rover_decision_loop


def execute_rover_decision_loop(
	initial_state: Optional[Dict[str, Any]] = None,
	max_iterations: Optional[int] = None,
) -> RoverWorkflowResult:
	"""Execute the rover decision loop and return the final workflow result."""
	return run_rover_decision_loop(initial_state=initial_state, max_iterations=max_iterations)
