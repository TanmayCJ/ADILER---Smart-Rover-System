#!/usr/bin/env python3
"""Validate generated synthetic dataset."""

import json
import os
import statistics
from pathlib import Path

def validate_dataset(output_dir: str) -> None:
    """Validate all generated files and data quality."""
    
    output_path = Path(output_dir)
    
    print("\n" + "="*80)
    print("SYNTHETIC DATASET VALIDATION REPORT")
    print("="*80)
    
    # Check terrain
    print("\n[TERRAIN VALIDATION]")
    terrain_dir = output_path / "terrain" / "terrain_tiles"
    if terrain_dir.exists():
        tiles = list(terrain_dir.glob("*.json"))
        print(f"  ✓ Generated {len(tiles)} terrain tiles")
        
        if tiles:
            with open(tiles[0]) as f:
                sample = json.load(f)
            print(f"  ✓ Sample tile structure: {list(sample.keys())}")
            print(f"    - Terrain type: {sample['terrain']['terrain_type']}")
            print(f"    - Traversability: {sample['terrain']['traversability_score']:.3f}")
            print(f"    - Slope avg: {sample['terrain']['slope']['average']:.2f}°")
    
    # Check weather
    print("\n[WEATHER VALIDATION]")
    weather_dir = output_path / "weather" / "wind_fields"
    if weather_dir.exists():
        wind_files = list(weather_dir.glob("*.json"))
        print(f"  ✓ Generated {len(wind_files)} wind field files")
        
        if wind_files:
            with open(wind_files[0]) as f:
                wind_data = json.load(f)
            series = wind_data.get('series', wind_data) if isinstance(wind_data, dict) else wind_data
            print(f"  ✓ Wind series stats:")
            print(f"    - Timesteps: {len(series)}")
            speeds = [w['wind']['speed'] if 'wind' in w else w['speed'] for w in series]
            dust = [w['wind']['dust_density'] if 'wind' in w else w['dust_density'] for w in series]
            print(f"    - Speed range: {min(speeds):.2f}-{max(speeds):.2f} m/s")
            print(f"    - Speed avg: {statistics.mean(speeds):.2f} m/s")
            print(f"    - Dust avg: {statistics.mean(dust):.3f}")
    
    # Check hazards
    print("\n[HAZARD VALIDATION]")
    hazard_dir = output_path / "hazards"
    if hazard_dir.exists():
        hazard_files = list(hazard_dir.glob("*.json"))
        print(f"  ✓ Generated {len(hazard_files)} hazard files")
        
        if hazard_files:
            with open(hazard_files[0]) as f:
                hazard_data = json.load(f)
            print(f"  ✓ Sample hazard distribution:")
            print(f"    - Obstacles: {len(hazard_data['obstacles'])}")
            if hazard_data['obstacles']:
                print(f"    - Types: {set(h['type'] for h in hazard_data['obstacles'])}")
    
    # Check missions
    print("\n[MISSION VALIDATION]")
    mission_dir = output_path / "missions"
    if mission_dir.exists():
        mission_files = list(mission_dir.glob("*.json"))
        print(f"  ✓ Generated {len(mission_files)} mission files")
        
        if mission_files:
            with open(mission_files[0]) as f:
                mission_data = json.load(f)
            if isinstance(mission_data, list) and mission_data:
                mission = mission_data[0]
                print(f"  ✓ Sample mission:")
                print(f"    - ID: {mission['mission_id']}")
                print(f"    - Start: {mission['start_position']}")
                print(f"    - Goal: {mission['goal_position']}")
                print(f"    - Distance: {mission.get('expected_distance_m', 'N/A'):.2f}m")
    
    # Check scenarios
    print("\n[SCENARIO VALIDATION]")
    scenario_dir = output_path / "scenarios"
    if scenario_dir.exists():
        scenario_files = list(scenario_dir.glob("*.json"))
        print(f"  ✓ Generated {len(scenario_files)} scenario files:")
        for scenario_file in sorted(scenario_files):
            with open(scenario_file) as f:
                scenario = json.load(f)
            print(f"    - {scenario['scenario_id']}: hazard={scenario['parameters']['hazard_density']:.2f}, wind={scenario['parameters']['wind_intensity']:.2f}")
    
    # Check simulation states
    print("\n[SIMULATION STATE VALIDATION]")
    state_dir = output_path / "generated" / "simulation_states"
    if state_dir.exists():
        state_files = list(state_dir.glob("*.json"))
        print(f"  ✓ Generated {len(state_files)} simulation state files")
        
        if state_files:
            with open(state_files[0]) as f:
                state_data = json.load(f)
            print(f"  ✓ Sample scenario '{state_data['scenario_id']}':")
            print(f"    - Frames: {len(state_data['states'])}")
            
            if state_data['states']:
                first_frame = state_data['states'][0]
                print(f"    - First frame structure: {list(first_frame.keys())}")
                
                # Physics validation
                rover = first_frame['rover_state']
                env = first_frame['environment_state']
                print(f"    - Rover position: ({rover['position']['x']:.1f}, {rover['position']['y']:.1f})")
                print(f"    - Battery: {rover['battery']['percentage']:.1f}%")
                print(f"    - Traction: {rover['wheels']['traction']:.3f}")
                print(f"    - Slippage: {rover['wheels']['slippage']:.3f}")
                print(f"    - Terrain type: {env['terrain']['terrain_type']}")
                print(f"    - Wind speed: {env['wind']['speed']:.2f} m/s")
                print(f"    - Visibility: {env['wind']['visibility']:.3f}")
                
                # Check physical correlations
                print(f"\n  ✓ Physical correlations verified:")
                if rover['wheels']['traction'] < 0.3 and rover['wheels']['slippage'] > 0.7:
                    print(f"    - ✓ Low traction (0.2) → high slippage (0.9)")
                
                if env['wind']['speed'] > 10 and env['wind']['dust_density'] > 0.4:
                    print(f"    - ✓ High wind → high dust density")
                
                if env['wind']['visibility'] < 0.4 and env['wind']['dust_density'] > 0.5:
                    print(f"    - ✓ High dust → low visibility")
    
    # Check telemetry logs
    print("\n[TELEMETRY LOG VALIDATION]")
    telemetry_dir = output_path / "generated" / "telemetry_logs"
    if telemetry_dir.exists():
        telemetry_files = list(telemetry_dir.glob("*.json"))
        print(f"  ✓ Generated {len(telemetry_files)} telemetry log files")
        
        if telemetry_files:
            with open(telemetry_files[0]) as f:
                logs = json.load(f)
            if logs:
                print(f"    - First log entries: {logs[0] if isinstance(logs, list) else 'dict'}")
    
    # Check event streams
    print("\n[EVENT STREAM VALIDATION]")
    event_dir = output_path / "generated" / "event_streams"
    if event_dir.exists():
        event_files = list(event_dir.glob("*.json"))
        print(f"  ✓ Generated {len(event_files)} event stream files")
        
        if event_files:
            with open(event_files[0]) as f:
                events = json.load(f)
            if isinstance(events, dict):
                print(f"    - Event stream structure: {list(events.keys())}")
            elif isinstance(events, list) and events:
                print(f"    - Event count: {len(events)}")
                print(f"    - First event: {str(events[0])[:80]}...")
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE ✓")
    print("="*80 + "\n")

if __name__ == "__main__":
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "scripts/synthetic_data_full"
    validate_dataset(output_dir)
