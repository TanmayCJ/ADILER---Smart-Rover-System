
# Mars Autonomous Rover 

A web application that simulates a Martian terrain environment using open-source Mars terrain datasets. An agentic AI rover brain analyzes terrain and obstacles to autonomously decide navigation strategies.

## Overview

This project combines web-based terrain visualization, a Python backend API, and an AI agent system to create an interactive Mars rover simulator. The rover operates on real Mars topography data (HiRISE DEM, CTX DEM, AI4Mars) and uses autonomous reasoning to navigate challenging Martian terrain.

## Tech Stack

### Frontend
- **Next.js** / React web application
- Mars terrain visualization
- Rover position rendering
- Simulation controls

### Backend
- **Python FastAPI** service
- Dataset loader and management
- Terrain tile serving
- API endpoints for simulation control

### AI Layer
- Python-based agentic system
- Autonomous navigation reasoning
- Obstacle analysis and pathfinding
- Decision-making architecture

### Data & Simulation
- **Open-source Mars datasets**: HiRISE DEM, CTX DEM, AI4Mars
- Terrain tile generation from Digital Elevation Models (DEM)
- Rover physics simulation
- Browser-based real-time simulation

## Project Structure

```
mars-rover-ai-simulator/
├── frontend/                      # Web UI - Next.js application
│   ├── pages/                     # Page components
│   ├── components/                # React components
│   ├── utils/                     # Helper utilities
│   └── styles/                    # Styling
├── backend/                       # FastAPI server
│   ├── routes/                    # API endpoints
│   ├── models/                    # Data models
│   └── services/                  # Business logic
├── ai_brain/                      # Autonomous agent system
│   ├── reasoning/                 # Decision making logic
│   ├── agent.py                   # Main agent orchestration
│   ├── planner.py                 # Path planning
│   └── navigator.py               # Navigation execution
├── terrain_engine/                # Terrain processing
│   ├── dem_loader.py              # DEM file loading
│   ├── tile_generator.py          # Tile generation
│   └── elevation_queries.py       # Elevation queries
├── simulation/                    # Rover simulation
│   ├── rover_state.py             # Rover state management
│   ├── physics.py                 # Physics calculations
│   └── movement.py                # Movement simulation
├── datasets/                      # Mars dataset tools
│   ├── download_scripts/          # Dataset downloaders
│   └── preprocessing/             # Data preprocessing
├── config/                        # Configuration files
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md            # System architecture
│   ├── DATASETS.md                # Dataset documentation
│   └── API.md                     # API reference
└── tests/                         # Unit and integration tests
    ├── unit/                      # Unit tests
    └── integration/               # Integration tests
```

## Modules

### 1. **frontend**
Web-based Mars terrain visualization and rover control interface.
- Terrain tile rendering
- Live rover position tracking
- Simulation playback controls

### 2. **backend**
FastAPI service providing terrain and simulation APIs.
- REST endpoints for terrain tiles
- Rover state management
- Dataset serving

### 3. **ai_brain**
Autonomous rover intelligence system.
- Agent architecture for decision-making
- Path planning and navigation
- Obstacle analysis and reasoning
- Terrain assessment

### 4. **terrain_engine**
Mars terrain data processing and queries.
- DEM (Digital Elevation Model) loading
- Terrain tile generation
- Real-time elevation queries

### 5. **simulation**
Rover physics and movement simulation.
- Rover state tracking
- Simplified physics calculations
- Movement and trajectory execution

### 6. **datasets**
Tools for downloading and preprocessing Mars terrain data.
- HiRISE DEM downloader
- CTX DEM downloader
- AI4Mars dataset downloader
- DEM processing utilities
- Image preprocessing

### 7. **config**
Centralized configuration management.
- YAML configuration files
- Settings modules

### 8. **docs**
Comprehensive project documentation.
- System architecture
- Dataset details and sources
- API documentation

### 9. **tests**
Test suite with unit and integration tests.
- Unit tests for individual components
- Integration tests for simulation flows

## Open-Source Datasets

- **HiRISE DEM** - High-resolution orbital imagery and elevation data
- **CTX DEM** - Context camera digital elevation models
- **AI4Mars** - Rover-detected terrain features and classifications

## Getting Started

### Prerequisites
- Node.js 16+ (for frontend)
- Python 3.9+ (for backend and AI)
- pip or conda for Python package management

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mars-rover-ai-simulator

# Frontend setup
cd frontend
npm install
npm run dev

# Backend setup (in new terminal)
cd backend
pip install -r requirements.txt
python main.py

# AI Brain setup (as needed)
cd ai_brain
pip install -r requirements.txt
```

### Running the Simulator

1. Start the backend API
2. Start the frontend development server
3. Open http://localhost:3000 in your browser
4. Configure rover starting position and target
5. Run the simulation to watch the AI rover navigate

## Contributing

This is an open-source research project. Contributions are welcome!

## License

TBD

## References

- Mars Reconnaissance Orbiter (MRO) HiRISE data
- Mars Reconnaissance Orbiter (MRO) CTX data
- AI4Mars dataset from University of Chicago
