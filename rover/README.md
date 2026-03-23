
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
rover/
├── backend/                       # ✅ FastAPI service (Sprint 1 Complete)
│   ├── main.py                    # Application entry point
│   ├── requirements.txt
│   ├── models/
│   │   └── terrain_model.py       # DTM and elevation models
│   ├── routes/
│   │   ├── terrain.py             # Terrain endpoints
│   │   ├── rover.py               # Rover endpoints (placeholder)
│   │   └── simulation.py          # Simulation endpoints (placeholder)
│   ├── services/
│   │   └── dataset_loader.py      # Dataset management
│   ├── README.md                  # Backend setup & API docs
│   └── .env.example               # Configuration template
├── frontend/                      # Next.js web UI (Planned)
│   ├── pages/
│   ├── components/
│   ├── utils/
│   └── styles/
├── ai_brain/                      # Autonomous agent system (Planned)
├── terrain_engine/                # Terrain processing (Planned)
├── simulation/                    # Rover simulation (Planned)
├── datasets/                      # Download & preprocessing tools (Planned)
├── config/                        # Configuration files
├── docs/                          # Documentation
│   ├── ARCHITECTURE.md
│   ├── DATASETS.md
│   └── API.md
└── tests/                         # Test suite (Planned)
```

## Modules

### 1. **backend** (✅ Sprint 1 Complete)
FastAPI service providing terrain and simulation APIs.
- **Terrain Endpoints** - Query Mars elevation data and terrain tiles
  - `GET /api/v1/terrain/datasets` - List available DTM datasets
  - `POST /api/v1/terrain/elevation` - Query elevation at coordinates
  - `POST /api/v1/terrain/tiles` - Get terrain tiles for region
  - See [backend/README.md](backend/README.md) for full endpoint documentation
- REST API with Swagger UI at `http://localhost:8000/docs`
- Real-time elevation queries using HiRISE DTM data
- Terrain tile serving for visualization

### 2. **frontend** (Planned)
Web-based Mars terrain visualization and rover control interface.
- Terrain tile rendering
- Live rover position tracking
- Simulation playback controls

### 3. **ai_brain** (Planned)
Autonomous rover intelligence system.
- Agent architecture for decision-making
- Path planning and navigation
- Obstacle analysis and reasoning
- Terrain assessment

### 4. **terrain_engine** (Planned)
Mars terrain data processing and queries.
- DEM (Digital Elevation Model) loading
- Terrain tile generation
- Real-time elevation queries

### 5. **simulation** (Planned)
Rover physics and movement simulation.
- Rover state tracking
- Simplified physics calculations
- Movement and trajectory execution

### 6. **datasets** (Planned)
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

### 9. **tests** (Planned)
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
cd rover

# Backend setup (in new terminal)
cd backend
pip install -r requirements.txt
python main.py
# Backend API available at: http://localhost:8000
# Swagger UI: http://localhost:8000/docs

# Frontend setup (in new terminal)
cd frontend
npm install
npm run dev
# Frontend available at: http://localhost:3000
```

### Running the Simulator

1. **Start Backend API** - `python main.py` (in `backend/` directory)
2. **Test Endpoints** - Open `http://localhost:8000/docs` for interactive Swagger UI
3. **Start Frontend** - `npm run dev` (in `frontend/` directory, when ready)
4. **Access App** - Navigate to `http://localhost:3000` in your browser

### Quick Backend Test

Access the Swagger UI to test terrain endpoints:
```
http://localhost:8000/docs
```

Sample requests:
- **List Datasets**: `GET /api/v1/terrain/datasets`
- **Query Elevation**: `POST /api/v1/terrain/elevation` with `{"latitude": -75.75, "longitude": 45.0}`
- **Get Terrain Tiles**: `POST /api/v1/terrain/tiles` for region visualization

See [backend/README.md](backend/README.md) for detailed API documentation.

## Sprint Status

### ✅ Sprint 1: Backend Terrain API (Complete)
- FastAPI application with CORS support
- 6 terrain endpoints with Swagger documentation
- Pydantic data models with validation
- HiRISE DTM dataset integration
- Mock elevation data for testing
- Comprehensive API documentation
- Ready for frontend integration

### 📋 Sprint 2: Real Data & Enhancements (Planned)
- Load real DTM files (rasterio)
- Database integration
- Caching layer
- Rate limiting
- Authentication

### 📋 Sprint 3+: Frontend & AI Integration (Planned)
- React/Next.js terrain visualization
- 3D terrain rendering
- AI navigation system
- Rover physics simulation

## Contributing

This is an open-source research project. Contributions are welcome!

## License

TBD

## References

- Mars Reconnaissance Orbiter (MRO) HiRISE data
- Mars Reconnaissance Orbiter (MRO) CTX data
- AI4Mars dataset from University of Chicago
- NASA PDS: https://pds.nasa.gov/
