"""
Wind API endpoints for Mars atmospheric wind data
Provides wind dataset discovery and wind query capabilities
"""

from typing import Optional

from fastapi import APIRouter, Query

from models.wind_model import (
    WindDatasetCatalogResponse,
    WindDatasetSourceEnum,
    WindQueryRequest,
    WindQueryResponse,
)
from services.wind_service import get_wind_service

router = APIRouter(
    prefix="/api/v1/wind",
    tags=["Wind"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/datasets",
    response_model=WindDatasetCatalogResponse,
    summary="List available wind datasets",
    description="Get catalog of available Mars wind data sources",
)
def list_wind_datasets(
    source: Optional[WindDatasetSourceEnum] = Query(None, description="Optional source filter: MEDA, InSight/TWINS, MCD"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """List wind datasets available to the simulator backend."""
    service = get_wind_service()
    return service.list_datasets(source=source, limit=limit, offset=offset)


@router.post(
    "/query",
    response_model=WindQueryResponse,
    summary="Query wind at coordinates",
    description="Get wind speed and direction for location and sol/timestamp",
)
def query_wind(request: WindQueryRequest):
    """
    Query wind data for a Mars location.

    Request requires latitude, longitude, and one time reference
    (either sol or timestamp_utc).
    """
    service = get_wind_service()
    return service.query_wind(request)


@router.get(
    "/health",
    summary="Health check",
    description="Check wind service availability",
)
def health_check():
    """Check if wind service is operational."""
    service = get_wind_service()
    count = service.list_datasets(source=None, limit=1000, offset=0).total_count
    return {
        "status": "healthy",
        "datasets_available": count,
    }
