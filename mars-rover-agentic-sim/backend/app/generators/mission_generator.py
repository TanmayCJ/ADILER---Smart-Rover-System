"""Mission generation utilities for synthetic datasets."""

from __future__ import annotations

import math
import random
from typing import Dict, List


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _choose_difficulty(traversability: float, hazard_density: float) -> str:
    if traversability < 0.5 or hazard_density > 0.6:
        return "hard"
    if traversability < 0.7 or hazard_density > 0.35:
        return "medium"
    return "easy"


def generate_mission(
    tile_id: str,
    tile_size_m: float,
    traversability: float,
    hazard_density: float,
    seed: int,
    mission_index: int,
) -> Dict[str, object]:
    rng = random.Random(seed)
    margin = tile_size_m * 0.1
    start_x = rng.uniform(margin, tile_size_m - margin)
    start_y = rng.uniform(margin, tile_size_m - margin)

    # Bias goals to be meaningfully far from start.
    angle = rng.uniform(0, 2 * math.pi)
    distance = rng.uniform(tile_size_m * 0.4, tile_size_m * 0.8)
    goal_x = _clamp(start_x + math.cos(angle) * distance, margin, tile_size_m - margin)
    goal_y = _clamp(start_y + math.sin(angle) * distance, margin, tile_size_m - margin)

    difficulty = _choose_difficulty(traversability, hazard_density)

    mission = {
        "mission": {
            "mission_id": f"mission_{mission_index:03d}",
            "start_position": [round(start_x, 2), round(start_y, 2)],
            "goal_position": [round(goal_x, 2), round(goal_y, 2)],
            "priority": "navigation",
            "difficulty": difficulty,
        },
        "tile_id": tile_id,
    }

    return mission


def generate_missions(
    tiles: List[Dict[str, object]],
    hazard_summary: Dict[str, float],
    seed: int,
    missions_per_tile: int = 1,
) -> List[Dict[str, object]]:
    missions: List[Dict[str, object]] = []
    base_seed = seed
    mission_index = 1

    for tile in tiles:
        tile_id = tile["tile_id"]
        tile_size_m = float(tile.get("tile_size_m", 256.0))
        traversability = float(tile["terrain"]["traversability_score"])
        hazard_density = float(hazard_summary.get(tile_id, 0.3))

        for _ in range(missions_per_tile):
            mission_seed = base_seed + mission_index * 101
            missions.append(
                generate_mission(
                    tile_id=tile_id,
                    tile_size_m=tile_size_m,
                    traversability=traversability,
                    hazard_density=hazard_density,
                    seed=mission_seed,
                    mission_index=mission_index,
                )
            )
            mission_index += 1

    return missions
