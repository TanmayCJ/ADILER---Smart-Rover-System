# ADILER: Autonomous Decision Intelligence Layer for Exploratory Rover Systems

## Overview
ADILER is a Mars rover simulation and multi-agent intelligence layer that demonstrates how autonomous decision-making can be orchestrated with LangGraph. It combines synthetic Mars environment data with agent-based planning to evaluate rover behavior across multiple scenarios. The system is designed to be deterministic, testable, and presentation-ready, providing a clear foundation for future real-time autonomy research.

This project addresses the challenge of coordinating multiple specialized agents in a dynamic environment while maintaining traceability, reproducibility, and measurable outcomes. It is built to support scenario-driven validation, pipeline testing, and a professional demo dashboard.

## Key Features
- Multi-agent architecture with Environment, Planner, Navigation, and Memory agents
- LangGraph orchestration for deterministic, sequential decision flows
- Synthetic Mars dataset pipeline with terrain, wind, hazards, and mission data
- Scenario-based evaluation and multi-scenario execution
- JSON schema validation and scenario expectations checks
- JSON and Markdown demo reports for presentation use
- Interactive frontend dashboard (Next.js + React + Three.js)

## System Architecture
The system consists of a synthetic data pipeline, a multi-agent decision layer, orchestration with LangGraph, and a frontend visualization layer.

Text diagram:

Environment Data -> Environment Agent -> Planner Agent -> Navigation Agent -> Memory Agent -> Feedback
       |                                                                     |
       |---- Dataset Pipeline ---->|                                         |---- Reports / Dashboard

Architecture components:
- Agent flow: Environment -> Planner -> Navigation -> Memory -> Feedback loop
- Backend APIs: service endpoints for simulation and data access (FastAPI)
- Dataset pipeline: terrain, wind, hazards, missions, and simulation states
- Frontend visualization: mission-control dashboard and 3D terrain view
- LangGraph orchestration layer: deterministic, sequential agent graph

## Agent Responsibilities
- Environment Agent: analyzes terrain, wind, dust, and hazards to compute risk signals
- Planner/Aggregator Agent: selects a high-level action using rule-based thresholds and scenario cues
- Navigation Agent: applies movement based on the planner action and mission goal
- Memory Agent: records the decision context and latest rover state snapshot

## Dataset Pipeline
The synthetic dataset pipeline produces deterministic simulation assets used by the agents:
- Terrain tiles: slope, roughness, traversability, and heightmap metadata
- Wind fields: speed, direction, turbulence, dust density, and visibility series
- Hazards: obstacle and hazard distributions by terrain tile
- Missions: start/goal positions, priorities, and difficulty
- Scenario-based simulation states

Data is stored under `scripts/synthetic_data_full/` and referenced by the demo runners.

## Evaluation Framework
The evaluation layer enforces correctness and repeatability:
- Schema validation for scenarios, missions, and workflow outputs
- Scenario expectations for risk/action ranges
- Multi-scenario runner with pass/fail status
- JSON and Markdown reports for traceable demo output

## Demo Output
Generated demo artifacts:
- `reports/demo_agent_run.json`: structured outputs for each scenario
- `reports/demo_agent_run.md`: presentation-ready narrative report
- Scenario comparison table: risk, wind, dust, obstacles, and action columns
- Scenario outputs: step-by-step execution with action and rationale

## Frontend Dashboard
The dashboard visualizes demo outputs with a mission-control interface:
- Next.js + React frontend
- React Three Fiber 3D scene for rover, path, and terrain
- Scenario selector and agent output cards
- Replay mode with timeline highlighting
- Recharts comparison charts for risk, wind, dust, and obstacles

## Tech Stack
- Python, FastAPI
- LangGraph
- Qdrant (planned)
- Next.js, React
- Three.js / React Three Fiber
- Recharts
- Tailwind CSS

## Getting Started

### Backend
Install dependencies:

```bash
python -m pip install -r mars-rover-agentic-sim/ai_brain/requirements.txt
```

Run demo scenarios:

```bash
python mars-rover-agentic-sim/scripts/run_demo_multi.py
```

Run a single scenario:

```bash
python mars-rover-agentic-sim/scripts/run_demo_scenario.py --scenario easy_navigation
```

### Frontend

```bash
cd mars-rover-agentic-sim/frontend
npm install
npm run dev
```

## Example Commands

Run multi-scenario demo:

```bash
python mars-rover-agentic-sim/scripts/run_demo_multi.py
```

Run LangGraph workflow for one scenario:

```bash
python mars-rover-agentic-sim/scripts/run_langgraph_workflow.py --data-dir scripts/synthetic_data_full --scenario easy_navigation
```

Start frontend dashboard:

```bash
cd mars-rover-agentic-sim/frontend
npm run dev
```

## Project Structure
- `mars-rover-agentic-sim/`: core project folder
- `ai_brain/`: agent logic, LangGraph orchestration, decision nodes
- `backend/`: FastAPI services and route handlers
- `simulation/`: rover movement, physics, and state evolution
- `scripts/synthetic_data_full/`: synthetic Mars dataset assets
- `frontend/`: mission-control dashboard and 3D visualization

## Future Work
- Real-time simulation loop and live telemetry
- ROS/Gazebo integration for hardware-in-the-loop testing
- Reinforcement learning policies for adaptive planning
- Advanced memory retrieval with Qdrant

## License
TBD
