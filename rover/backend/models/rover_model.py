"""Pydantic models for rover decision-loop requests and responses."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class RoverInterruptCommand(str, Enum):
    """Supported rover interrupt commands."""

    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    CHANGE_GOAL = "change_goal"
    CLEAR = "clear"


class RoverDecisionRequest(BaseModel):
    """Request body for running the rover decision loop."""

    initial_state: Optional[Dict[str, Any]] = Field(default=None, description="Optional rover state to start from")
    max_iterations: int = Field(default=1, ge=1, le=1000, description="Maximum workflow iterations to execute")


class RoverDecisionResponse(BaseModel):
    """Response payload returned by rover workflow execution endpoints."""

    state: Dict[str, Any]
    iterations: int
    interrupted: bool
    reason: Optional[str] = None


class RoverInterruptRequest(BaseModel):
    """Request body for rover interrupt control."""

    command: RoverInterruptCommand
    new_goal: Optional[Dict[str, Any]] = Field(default=None, description="Goal payload for change_goal")


class RoverInterruptResponse(BaseModel):
    """Response payload for rover interrupt commands."""

    status: str
    interrupt_reason: Optional[str] = None
    paused: bool = False
    state: Optional[Dict[str, Any]] = None
