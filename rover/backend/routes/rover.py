"""API routes for rover brain control and decision-loop execution."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status

from agents.core.agent_state import get_rover_state_container
from agents.core.interrupt_handler import InterruptReason, get_interrupt_handler
from agents.shared.mock_generators import get_mock_generator
from agents.workflows.rover_decision_loop import execute_rover_decision_loop
from services.rover_controller import get_rover_controller
from models.rover_model import (
	RoverDecisionRequest,
	RoverDecisionResponse,
	RoverInterruptCommand,
	RoverInterruptRequest,
	RoverInterruptResponse,
)

router = APIRouter(prefix="/api/v1/rover", tags=["Rover"], responses={404: {"description": "Not found"}})


@router.get("/health", summary="Rover brain health check")
def health_check() -> Dict[str, Any]:
	"""Report rover brain readiness and current state metadata."""
	handler = get_interrupt_handler()
	container = get_rover_state_container()
	return {
		"status": "healthy",
		"timestamp": datetime.utcnow().isoformat(),
		"interrupt_state": handler.get_state(),
		"state_stats": container.get_stats(),
	}


@router.get("/state", summary="Get current rover state")
def get_state() -> Dict[str, Any]:
	"""Return the current in-memory rover state snapshot."""
	return get_rover_state_container().get_state()


@router.get("/session", summary="Get rover session status")
def get_session_status() -> Dict[str, Any]:
	"""Return the current background controller status."""
	controller = get_rover_controller()
	status = controller.status()
	return {
		"running": status.running,
		"paused": status.paused,
		"stopped": status.stopped,
		"cycles_completed": status.cycles_completed,
		"started_at": status.started_at,
		"updated_at": status.updated_at,
		"reason": status.reason,
		"last_state": status.last_state,
	}


@router.post("/session/start", summary="Start rover background session")
def start_session(request: RoverDecisionRequest) -> Dict[str, Any]:
	"""Start the rover decision loop in the background."""
	controller = get_rover_controller()
	status = controller.start(initial_state=request.initial_state, max_cycles=request.max_iterations)
	return {
		"status": "started",
		"session": {
			"running": status.running,
			"paused": status.paused,
			"stopped": status.stopped,
			"cycles_completed": status.cycles_completed,
			"started_at": status.started_at,
			"updated_at": status.updated_at,
			"reason": status.reason,
		},
	}


@router.post("/session/pause", summary="Pause rover background session")
def pause_session() -> Dict[str, Any]:
	"""Pause the rover controller thread."""
	status = get_rover_controller().pause()
	return {"status": "paused", "session": status.__dict__}


@router.post("/session/resume", summary="Resume rover background session")
def resume_session() -> Dict[str, Any]:
	"""Resume the rover controller thread."""
	status = get_rover_controller().resume()
	return {"status": "resumed", "session": status.__dict__}


@router.post("/session/stop", summary="Stop rover background session")
def stop_session() -> Dict[str, Any]:
	"""Stop the rover controller thread."""
	status = get_rover_controller().stop()
	return {"status": "stopped", "session": status.__dict__}


@router.post("/decision-loop", response_model=RoverDecisionResponse, summary="Run rover decision loop")
def decision_loop(request: RoverDecisionRequest) -> RoverDecisionResponse:
	"""Execute the rover brain once or for a bounded number of cycles."""
	initial_state = request.initial_state or get_mock_generator().generate_initial_state()
	result = execute_rover_decision_loop(initial_state=initial_state, max_iterations=request.max_iterations)
	return RoverDecisionResponse(
		state=result.state,
		iterations=result.iterations,
		interrupted=result.interrupted,
		reason=result.reason,
	)


@router.post("/interrupt", response_model=RoverInterruptResponse, summary="Control rover execution")
def interrupt_rover(request: RoverInterruptRequest) -> RoverInterruptResponse:
	"""Apply an interrupt command to the rover execution loop."""
	handler = get_interrupt_handler()

	if request.command == RoverInterruptCommand.STOP:
		handler.stop()
	elif request.command == RoverInterruptCommand.PAUSE:
		handler.pause()
	elif request.command == RoverInterruptCommand.RESUME:
		handler.resume()
	elif request.command == RoverInterruptCommand.CHANGE_GOAL:
		if not request.new_goal:
			raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="new_goal is required for change_goal")
		handler.change_goal(request.new_goal)
	elif request.command == RoverInterruptCommand.CLEAR:
		handler.clear()
		handler.clear_pause()
	else:  # pragma: no cover - defensive guard
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported command: {request.command}")

	state = handler.get_state()
	return RoverInterruptResponse(
		status="ok",
		interrupt_reason=state.get("interrupt_reason"),
		paused=bool(state.get("paused")),
		state=state,
	)

