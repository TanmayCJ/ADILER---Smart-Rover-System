# Mars Rover LangGraph Demo Run

## Scenario: easy_navigation
1. Scenario Loaded
Mission: mission_001
Start: (26.40, 25.00)
Goal: (28.80, 28.80)
Terrain Tile: mars_tile_r00_c00

2. Environment Agent Output
Risk Score: 0.309
Slope: 31.32
Roughness: 0.165
Wind Speed: 3.11
Dust Level: 0.156
Obstacle Count: 2
Risk Level: low

3. Planner/Aggregator Agent Output
Selected Action: proceed
Rationale: low risk, proceed

4. Navigation Agent Output
Initial Position: (26.93, 25.85)
Final Position: (27.47, 26.69)
Movement Step: 1.0 meters
Navigation Status: moved

5. Memory Agent Output
Memory Events Written: 1
Latest Memory Event: {'risk_score': 0.309, 'action': 'proceed', 'position': {'x': 27.47, 'y': 26.69, 'z': 1561.84}}

6. Final Verdict
Proceed toward the goal.

## Scenario: high_wind_navigation
1. Scenario Loaded
Mission: mission_001
Start: (26.40, 25.00)
Goal: (28.80, 28.80)
Terrain Tile: mars_tile_r00_c00

2. Environment Agent Output
Risk Score: 0.419
Slope: 31.32
Roughness: 0.165
Wind Speed: 9.33
Dust Level: 0.468
Obstacle Count: 4
Risk Level: low

3. Planner/Aggregator Agent Output
Selected Action: proceed
Rationale: low risk, proceed

4. Navigation Agent Output
Initial Position: (26.93, 25.85)
Final Position: (27.47, 26.69)
Movement Step: 1.0 meters
Navigation Status: moved

5. Memory Agent Output
Memory Events Written: 1
Latest Memory Event: {'risk_score': 0.419, 'action': 'proceed', 'position': {'x': 27.47, 'y': 26.69, 'z': 1561.84}}

6. Final Verdict
Proceed toward the goal.

## Scenario: dust_storm_escape
1. Scenario Loaded
Mission: mission_003
Start: (22.93, 3.35)
Goal: (28.80, 3.31)
Terrain Tile: mars_tile_r01_c00

2. Environment Agent Output
Risk Score: 0.585
Slope: 41.04
Roughness: 0.283
Wind Speed: 10.73
Dust Level: 0.526
Obstacle Count: 10
Risk Level: moderate

3. Planner/Aggregator Agent Output
Selected Action: proceed_cautious
Rationale: moderate risk, proceed cautiously

4. Navigation Agent Output
Initial Position: (23.93, 3.34)
Final Position: (24.33, 3.34)
Movement Step: 0.4 meters
Navigation Status: moved

5. Memory Agent Output
Memory Events Written: 1
Latest Memory Event: {'risk_score': 0.585, 'action': 'proceed_cautious', 'position': {'x': 24.33, 'y': 3.34, 'z': 1590.63}}

6. Final Verdict
Proceed cautiously toward the goal.

## Scenario: rocky_terrain
1. Scenario Loaded
Mission: mission_001
Start: (26.40, 25.00)
Goal: (28.80, 28.80)
Terrain Tile: mars_tile_r00_c00

2. Environment Agent Output
Risk Score: 0.375
Slope: 31.32
Roughness: 0.165
Wind Speed: 5.18
Dust Level: 0.26
Obstacle Count: 7
Risk Level: low

3. Planner/Aggregator Agent Output
Selected Action: proceed
Rationale: low risk, proceed

4. Navigation Agent Output
Initial Position: (26.93, 25.85)
Final Position: (27.47, 26.69)
Movement Step: 1.0 meters
Navigation Status: moved

5. Memory Agent Output
Memory Events Written: 1
Latest Memory Event: {'risk_score': 0.375, 'action': 'proceed', 'position': {'x': 27.47, 'y': 26.69, 'z': 1561.84}}

6. Final Verdict
Proceed toward the goal.

## Scenario: energy_critical_route
1. Scenario Loaded
Mission: mission_001
Start: (26.40, 25.00)
Goal: (28.80, 28.80)
Terrain Tile: mars_tile_r00_c00

2. Environment Agent Output
Risk Score: 0.378
Slope: 31.32
Roughness: 0.165
Wind Speed: 6.22
Dust Level: 0.312
Obstacle Count: 5
Risk Level: low

3. Planner/Aggregator Agent Output
Selected Action: proceed
Rationale: low risk, proceed

4. Navigation Agent Output
Initial Position: (26.93, 25.85)
Final Position: (27.47, 26.69)
Movement Step: 1.0 meters
Navigation Status: moved

5. Memory Agent Output
Memory Events Written: 1
Latest Memory Event: {'risk_score': 0.378, 'action': 'proceed', 'position': {'x': 27.47, 'y': 26.69, 'z': 1561.84}}

6. Final Verdict
Proceed toward the goal.

## Scenario Comparison

| Scenario | Risk Score | Wind | Dust | Obstacles | Action | Status |
| --- | --- | --- | --- | --- | --- | --- |
| easy_navigation | 0.309 | 3.11 | 0.156 | 2 | proceed | passed |
| high_wind_navigation | 0.419 | 9.33 | 0.468 | 4 | proceed | passed |
| dust_storm_escape | 0.585 | 10.73 | 0.526 | 10 | proceed_cautious | passed |
| rocky_terrain | 0.375 | 5.18 | 0.26 | 7 | proceed | passed |
| energy_critical_route | 0.378 | 6.22 | 0.312 | 5 | proceed | passed |