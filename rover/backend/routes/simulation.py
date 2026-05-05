"""API routes for simulation orchestration."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from agents.shared.mock_generators import get_mock_generator
from agents.workflows.rover_decision_loop import execute_rover_decision_loop
from models.rover_model import RoverDecisionRequest, RoverDecisionResponse

router = APIRouter(prefix="/api/v1/simulation", tags=["Simulation"], responses={404: {"description": "Not found"}})


@router.get("/health", summary="Simulation health check")
def health_check() -> Dict[str, Any]:
	"""Report simulation and mock-data readiness."""
	return {
		"status": "healthy",
		"timestamp": datetime.utcnow().isoformat(),
		"mock_data": get_mock_generator().get_stats(),
	}


@router.post("/run", response_model=RoverDecisionResponse, summary="Run a simulation cycle")
def run_simulation(request: RoverDecisionRequest) -> RoverDecisionResponse:
	"""Run the rover workflow against mock or provided state."""
	initial_state = request.initial_state or get_mock_generator().generate_initial_state()
	result = execute_rover_decision_loop(initial_state=initial_state, max_iterations=request.max_iterations)
	return RoverDecisionResponse(
		state=result.state,
		iterations=result.iterations,
		interrupted=result.interrupted,
		reason=result.reason,
	)
