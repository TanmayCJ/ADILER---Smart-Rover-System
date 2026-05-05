"""Navigation-focused workflow helpers."""

from __future__ import annotations

from typing import Any, Dict, Optional

from rover.brain.graph.rover_graph import run_rover_decision_loop


def execute_navigation_workflow(
	initial_state: Optional[Dict[str, Any]] = None,
	max_iterations: Optional[int] = None,
):
	"""Run the rover decision loop with a navigation-first intent."""
	return run_rover_decision_loop(initial_state=initial_state, max_iterations=max_iterations)
