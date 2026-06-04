<div align="center">

# ADILER

### Autonomous Decision Intelligence Layer for Exploratory Rover Systems

A multi-agent autonomous rover intelligence platform that simulates decision-making, navigation, environmental reasoning, and memory-driven exploration in dynamic Martian environments.

---

[Architecture](#architecture) •
[Features](#features) •
[Simulation](#simulation) •
[Getting Started](#getting-started) •
[Roadmap](#future-work)

</div>

---

## Overview

ADILER is a multi-agent AI system designed to emulate the cognitive layer of an autonomous planetary rover.

The platform combines environmental analysis, mission planning, navigation, and memory management through a LangGraph-orchestrated agent architecture. A real-time simulation dashboard visualizes rover behavior across dynamic Martian scenarios including dust storms, rocky terrain, high-wind conditions, and energy-constrained missions.

The objective is to explore how agentic AI systems can improve autonomy, adaptability, and explainability in future space exploration missions.

---

## Core Capabilities

| Capability | Description |
|------------|-------------|
| Environment Analysis | Terrain and atmospheric risk assessment |
| Autonomous Planning | Scenario-aware action selection |
| Navigation Intelligence | Adaptive route traversal |
| Memory Systems | Mission state persistence |
| Mission Simulation | Interactive Mars environment |
| Replay Engine | Step-by-step mission playback |
| Scenario Evaluation | Multi-condition testing framework |
| Explainable AI | Transparent decision trace visualization |

---

## Architecture

```text
                    ┌──────────────────┐
                    │ Mission Scenario │
                    └────────┬─────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Environment Agent       │
                │ Risk Assessment         │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Planner Agent           │
                │ Decision Selection      │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Navigation Agent        │
                │ Route Execution         │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Memory Agent            │
                │ State Persistence       │
                └────────────┬────────────┘
                             │
                             ▼
                ┌─────────────────────────┐
                │ Mission Visualization   │
                └─────────────────────────┘
```

---

## Agent System

### Environment Agent

Analyzes:

- Terrain slope
- Surface roughness
- Obstacle density
- Wind conditions
- Dust intensity

Outputs a mission risk profile used by downstream agents.

### Planner Agent

Determines rover behavior using environmental signals.

Possible actions:

```text
proceed
proceed_cautious
reduce_speed
hold_position
reroute
conserve_energy
```

### Navigation Agent

Responsible for:

- Route execution
- Rover state updates
- Traversal simulation
- Path visualization

### Memory Agent

Stores:

- Risk assessments
- Planner decisions
- Navigation outcomes
- Mission events

Future versions will integrate vectorized long-term memory through Qdrant.

---

## Simulation System

The simulation layer visualizes rover behavior across multiple Martian mission scenarios.

Implemented scenarios:

| Scenario | Description |
|-----------|------------|
| Easy Navigation | Low-risk traversal |
| High Wind Navigation | Atmospheric hazards |
| Dust Storm Escape | Visibility-constrained navigation |
| Rocky Terrain | Obstacle-heavy traversal |
| Energy Critical Route | Resource-constrained mission |

Simulation features:

- Interactive 3D Mars environment
- Mission playback system
- Cinematic camera system
- Environmental effects
- Telemetry overlays
- Agent reasoning trace
- Mission analytics

---

## Technology Stack

### Backend

```text
Python
FastAPI
LangGraph
JSON Schema Validation
YAML Expectations
```

### Frontend

```text
Next.js
React
React Three Fiber
Three.js
Drei
Tailwind CSS
Recharts
```

### Data Layer

```text
Synthetic Mars Terrain
Wind Models
Hazard Maps
Mission Definitions
Telemetry Streams
```

---

## Dataset Pipeline

ADILER uses a synthetic Mars dataset generation framework capable of producing:

- Terrain grids
- Hazard distributions
- Wind conditions
- Dust environments
- Rover telemetry
- Mission scenarios

Generated data is stored inside:

```text
synthetic_data_full/
```

---

## Evaluation Framework

Mission scenarios are validated using:

- Schema validation
- Scenario expectations
- Automated workflow testing
- Multi-scenario replay execution

Outputs include:

```text
demo_agent_run.json
demo_agent_run.md
langgraph_multi_report.json
langgraph_multi_report.md
```

---

## Project Structure

```text
mars-rover-agentic-sim/
│
├── ai_brain/
├── backend/
├── frontend/
├── simulation_engine/
├── shared/
├── scripts/
├── synthetic_data_full/
├── reports/
└── docs/
```

---

## Getting Started

### Backend

```bash
pip install -r requirements.txt
```

Run scenario evaluation:

```bash
python scripts/run_langgraph_multi.py --markdown
```

Generate reports:

```bash
python scripts/run_demo_multi.py
```

---

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## Current Status

| Component | Status |
|------------|---------|
| Multi-Agent System | Complete |
| LangGraph Workflow | Complete |
| Simulation Dashboard | Complete |
| Replay Engine | Complete |
| Scenario Framework | Complete |
| Long-Term Memory | In Progress |
| ROS/Gazebo Integration | Planned |

---

## Future Work

Planned extensions include:

- ROS integration
- Gazebo simulation environments
- Reinforcement learning navigation
- Real Martian DEM support
- Multi-rover coordination
- Vectorized mission memory
- Real-time environment adaptation

---

## Contributors

| Name | Responsibility |
|--------|---------------|
| Tanmay C Jain | Navigation Agent, Backend APIs |
| Karthik J Ramoo | Memory Agent, LangGraph, Long-Term Memory |
| Jayashree Godige | Planner Agent |
| Ruchika C Lal | Environment Agent |

---

## License

This project is released under the repository license.
