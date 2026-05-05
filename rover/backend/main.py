"""
Mars Rover AI Simulator - Backend API
FastAPI application for terrain data and rover simulation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn
import sys
import os

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
ROVER_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir, os.pardir))

# Add both the backend directory and repository root to the import path.
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if ROVER_ROOT not in sys.path:
    sys.path.insert(0, ROVER_ROOT)

from routes import rover, simulation, terrain, wind

# Create FastAPI application
app = FastAPI(
    title="Mars Rover AI Simulator API",
    description="Backend API for Mars terrain visualization and autonomous rover simulation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include terrain routes
app.include_router(terrain.router)
app.include_router(wind.router)
app.include_router(rover.router)
app.include_router(simulation.router)


@app.get("/", tags=["Root"])
def read_root():
    """
    Welcome endpoint providing API overview
    """
    return {
        "message": "Mars Rover AI Simulator Backend",
        "version": "0.1.0",
        "documentation": "/docs",
        "endpoints": {
            "terrain": "/api/v1/terrain",
            "wind": "/api/v1/wind",
            "rover": "/api/v1/rover",
            "simulation": "/api/v1/simulation",
            "health": "/health"
        }
    }


@app.get("/health", tags=["Health"])
def health():
    """
    API health check endpoint
    """
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Mars Rover AI Backend",
        "version": "0.1.0"
    }


@app.get("/api/v1/health", tags=["Health"])
def api_health():
    """
    API v1 health check endpoint
    """
    return {
        "status": "operational",
        "api_version": "v1",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "terrain": "available",
            "wind": "available",
            "rover": "available",
            "simulation": "available",
            "ai_brain": "available"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )


if __name__ == "__main__":
    # Run with: python -m uvicorn backend.main:app --reload
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
