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

# Add backend directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import routes
from routes import terrain
from routes.aggregator_routes import router as aggregator_router

# Create FastAPI application
app = FastAPI(
    title="Mars Rover AI Simulator API",
    description="Backend API for Mars terrain visualization and autonomous rover simulation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(terrain.router)
app.include_router(aggregator_router)

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Mars Rover AI Simulator Backend",
        "version": "0.1.0",
        "documentation": "/docs",
        "endpoints": {
            "terrain": "/api/v1/terrain",
            "aggregator": "/aggregated-state",
            "health": "/health"
        }
    }

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Mars Rover AI Backend",
        "version": "0.1.0"
    }

@app.get("/api/v1/health", tags=["Health"])
def api_health():
    return {
        "status": "operational",
        "api_version": "v1",
        "timestamp": datetime.utcnow().isoformat(),
        "modules": {
            "terrain": "available",
            "rover": "planned",
            "simulation": "planned",
            "ai_brain": "planned",
            "aggregator": "available"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error": str(exc)
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        app_dir=os.path.dirname(os.path.abspath(__file__)),
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )