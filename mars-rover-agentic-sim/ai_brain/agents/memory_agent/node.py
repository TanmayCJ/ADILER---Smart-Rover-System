"""Memory agent: append a summary of the latest decision."""

from __future__ import annotations

from typing import Dict


def memory_node(state: Dict[str, object]) -> Dict[str, object]:
	"""Store the latest environment + planner + navigation snapshot."""

	memory = dict(state.get("memory", {}))
	events = list(memory.get("events", []))
	events.append(
		{
			"risk_score": state.get("environment_state", {}).get("risk_score"),
			"action": state.get("plan", {}).get("action"),
			"position": state.get("rover_state", {}).get("position"),
		}
	)
	memory["events"] = events[-50:]
	return {"memory": memory}

