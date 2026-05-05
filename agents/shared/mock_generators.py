"""
Mock data generators for MVP testing.
Generates synthetic terrain, wind, and rover position data.
"""

import random
import logging
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MockDataGenerator:
    """Generates realistic mock sensor data for rover simulation."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize mock generator.
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        self.call_count = 0
    
    def generate_mock_rover_position(self) -> Dict[str, float]:
        """
        Generate mock rover geographic position.
        Simulates rover on Mars surface near south pole region.
        
        Returns:
            {latitude, longitude, elevation_m}
        """
        self.call_count += 1
        
        # South pole region (common rover territory)
        latitude = random.uniform(-80, -70)
        longitude = random.uniform(0, 360)
        elevation = random.uniform(-2400, -2000)
        
        logger.debug(f"Mock rover pos: lat={latitude:.2f}, lon={longitude:.2f}, elev={elevation:.1f}m")
        
        return {
            "latitude": latitude,
            "longitude": longitude,
            "elevation_m": elevation
        }
    
    def generate_mock_terrain_data(self) -> Dict[str, Any]:
        """
        Generate mock terrain sensor observations.
        
        Returns:
            {slope_deg, terrain_type, roughness, obstacles}
        """
        self.call_count += 1
        
        # Terrain parameters
        slope = random.uniform(0, 45)  # degrees
        terrain_types = ["sand", "rock", "mixed", "clay", "regolith"]
        terrain_type = random.choice(terrain_types)
        roughness = random.uniform(0, 1)  # 0=smooth, 1=very rough
        
        # Generate obstacles
        num_obstacles = random.randint(0, 4)
        obstacles = []
        for i in range(num_obstacles):
            obstacle = {
                "type": random.choice(["boulder", "crater", "dune", "escarpment"]),
                "distance_m": random.uniform(5, 100),
                "size_m": random.uniform(0.5, 10),
                "heading_deg": random.uniform(0, 360)
            }
            obstacles.append(obstacle)
        
        logger.debug(f"Mock terrain: slope={slope:.1f}°, type={terrain_type}, obstacles={len(obstacles)}")
        
        return {
            "slope_deg": slope,
            "terrain_type": terrain_type,
            "roughness": roughness,
            "obstacles": obstacles
        }
    
    def generate_mock_wind_data(self) -> Dict[str, float]:
        """
        Generate mock wind sensor observations.
        Mars winds vary significantly with time of day and elevation.
        
        Returns:
            {speed_mps, direction_deg, gust_speed_mps}
        """
        self.call_count += 1
        
        # Mars wind typical ranges: 2-15 m/s
        speed = random.uniform(2, 12)
        direction = random.uniform(0, 360)
        gust_speed = speed + random.uniform(2, 8)  # Gusts are stronger
        
        logger.debug(f"Mock wind: speed={speed:.1f}m/s, dir={direction:.0f}°, gust={gust_speed:.1f}m/s")
        
        return {
            "speed_mps": speed,
            "direction_deg": direction,
            "gust_speed_mps": gust_speed
        }
    
    def generate_mock_goal(self) -> Dict[str, Any]:
        """
        Generate mock navigation goal.
        
        Returns:
            {latitude, longitude, name, priority}
        """
        self.call_count += 1
        
        goals = [
            {"name": "Crater A", "priority": 8},
            {"name": "Icy Deposit", "priority": 9},
            {"name": "Ridge Survey", "priority": 6},
            {"name": "Sample Site", "priority": 7},
        ]
        
        selected_goal = random.choice(goals)
        
        return {
            "latitude": random.uniform(-80, -70),
            "longitude": random.uniform(0, 360),
            "name": selected_goal["name"],
            "priority": selected_goal["priority"]
        }
    
    def generate_initial_state(self) -> Dict[str, Any]:
        """
        Generate complete initial rover state for MVP.
        
        Returns:
            Dictionary with all required state fields
        """
        logger.info("Generating initial rover state...")
        
        now = datetime.now().isoformat()
        
        return {
            # Rover Position & Motion
            "rover_position": self.generate_mock_rover_position(),
            "rover_heading": random.uniform(0, 360),
            "rover_velocity": 0.0,  # Start stationary
            
            # Goal & Navigation
            "current_goal": self.generate_mock_goal(),
            "planned_route": [],
            "current_waypoint_index": 0,
            "current_action": "waiting_for_plan",
            
            # Environment Observations
            "terrain_data": self.generate_mock_terrain_data(),
            "wind_data": self.generate_mock_wind_data(),
            
            # Analysis Results
            "hazard_map": {
                "risk_score": 0.5,
                "safe_zones": [],
                "danger_zones": [],
                "summary": "Initial assessment pending"
            },
            "environment_summary": "Initial state - awaiting first analysis cycle",
            
            # Memory & Context
            "memory_context": {
                "recent_experiences": [],
                "learned_hazards": [],
                "success_patterns": [],
                "failure_patterns": []
            },
            "hazard_memory": [],
            "route_history": [],
            "experience_buffer": [],
            
            # Control & Metadata
            "cycle_count": 0,
            "timestamp": now,
            "loop_interrupted": False,
            "interrupt_reason": None,
            "max_cycles": 100,  # Default cycle limit
            
            # Debug/Monitoring
            "llm_calls": 0,
            "error_log": []
        }
    
    def update_mock_observations(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update mock sensor observations in state (simulate sensor changes).
        Used each cycle to refresh environmental data.
        
        Args:
            state: Current rover state
            
        Returns:
            Updated state with fresh sensor observations
        """
        state["terrain_data"] = self.generate_mock_terrain_data()
        state["wind_data"] = self.generate_mock_wind_data()
        state["timestamp"] = datetime.now().isoformat()
        
        logger.debug(f"Updated mock observations (cycle {state['cycle_count']})")
        return state
    
    def simulate_rover_movement(
        self,
        state: Dict[str, Any],
        speed: float,
        heading: float,
        time_delta_s: float = 1.0
    ) -> Dict[str, Any]:
        """
        Simulate rover movement by updating position.
        
        Args:
            state: Current rover state
            speed: Movement speed in m/s
            heading: Movement direction in degrees
            time_delta_s: Time elapsed in seconds (default 1 sec)
            
        Returns:
            Updated state with new rover position
        """
        # Calculate distance traveled
        distance_m = speed * time_delta_s
        
        # Simple lat/lon update (approximation for small distances)
        # Mars radius ~3390 km
        MARS_RADIUS_KM = 3390
        
        # Convert heading to radians
        import math
        heading_rad = math.radians(heading)
        
        # Update position (very simplified)
        lat_delta = (distance_m / 1000) / MARS_RADIUS_KM * math.cos(heading_rad)
        lon_delta = (distance_m / 1000) / MARS_RADIUS_KM * math.sin(heading_rad)
        
        state["rover_position"]["latitude"] += lat_delta
        state["rover_position"]["longitude"] += lon_delta
        state["rover_heading"] = heading
        state["rover_velocity"] = speed
        
        logger.debug(f"Simulated movement: {distance_m:.1f}m at {heading:.0f}°, new pos: {state['rover_position']}")
        
        return state
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mock generator statistics."""
        return {
            "call_count": self.call_count,
            "timestamp": datetime.now().isoformat()
        }


# Singleton instance
_generator_instance: MockDataGenerator = None


def get_mock_generator(seed: int = 42) -> MockDataGenerator:
    """
    Get or create singleton MockDataGenerator instance.
    
    Args:
        seed: Random seed
        
    Returns:
        MockDataGenerator instance
    """
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = MockDataGenerator(seed=seed)
    return _generator_instance
