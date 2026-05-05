"""
Shared schema definitions for rover agentic system.
Central TypedDict for LangGraph state management.
"""

from typing import TypedDict, Optional, List, Dict, Any
from typing_extensions import Annotated
import operator
from datetime import datetime


class RoverPosition(TypedDict):
    """Rover geographic position."""
    latitude: float
    longitude: float
    elevation_m: float


class RoverVelocity(TypedDict):
    """Rover velocity parameters."""
    speed_mps: float  # meters per second
    heading_deg: float  # direction 0-360


class Goal(TypedDict):
    """Navigation goal specification."""
    latitude: float
    longitude: float
    name: str
    priority: int  # 0-10, higher = more important


class TerrainData(TypedDict):
    """Terrain sensor observations."""
    slope_deg: float
    terrain_type: str  # "sand", "rock", "mixed", "clay"
    roughness: float  # 0-1
    obstacles: List[Dict[str, Any]]  # {type, distance_m, size_m}


class WindData(TypedDict):
    """Wind sensor observations."""
    speed_mps: float
    direction_deg: float
    gust_speed_mps: float


class HazardData(TypedDict):
    """Hazard classification for a location."""
    hazard_type: str  # "obstacle", "slope", "wind", "thermal"
    severity: float  # 0-1
    location: dict  # {lat, lon}
    recommendation: str


class HazardMap(TypedDict):
    """Aggregated hazard analysis for current area."""
    risk_score: float  # 0-1
    safe_zones: List[dict]  # [{lat, lon, safety_level}, ...]
    danger_zones: List[HazardData]
    summary: str


class Waypoint(TypedDict):
    """Individual waypoint in route."""
    latitude: float
    longitude: float
    action: str  # "move", "stop", "wait", "collect_sample"
    priority: int


class Route(TypedDict):
    """Planned navigation route."""
    waypoints: List[Waypoint]
    estimated_duration_s: float
    success_probability: float
    created_at: str  # ISO timestamp


class Experience(TypedDict):
    """Stored experience for memory system."""
    rover_position: dict
    action_taken: str
    outcome: str  # "success", "failure", "partial"
    observations: dict
    timestamp: str
    cycle_number: int


class MemoryContext(TypedDict):
    """Retrieved contextual memory for decision making."""
    recent_experiences: List[Experience]
    learned_hazards: List[HazardData]
    success_patterns: List[str]
    failure_patterns: List[str]


class RoverState(TypedDict):
    """
    Central state container for LangGraph rover brain.
    Persists throughout agent execution cycle.
    Uses Annotated[list, operator.add] for message appending.
    """
    # Rover Position & Motion
    rover_position: RoverPosition
    rover_heading: float  # 0-360 degrees
    rover_velocity: float  # m/s
    
    # Goal & Navigation
    current_goal: Optional[Goal]
    planned_route: List[Waypoint]
    current_waypoint_index: int
    current_action: str  # "moving", "stopped", "replan_required", "reached_goal", "error"
    
    # Environment Observations
    terrain_data: TerrainData
    wind_data: WindData
    
    # Analysis Results (from agents)
    hazard_map: HazardMap
    environment_summary: str  # LLM-generated text summary
    
    # Memory & Context
    memory_context: MemoryContext
    hazard_memory: List[HazardData]
    route_history: List[Route]
    experience_buffer: List[Experience]
    
    # Control & Metadata
    cycle_count: int
    timestamp: str  # ISO timestamp
    loop_interrupted: bool
    interrupt_reason: Optional[str]  # "user_stop", "user_pause", "user_goal_change", None
    max_cycles: int
    
    # Debug/Monitoring
    llm_calls: int  # Track LLM invocations
    error_log: List[str]
