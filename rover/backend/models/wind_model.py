"""
Data models for Mars wind datasets and wind query responses
Supports MEDA (Perseverance), InSight/TWINS, and future MCD adapters
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class WindDatasetSourceEnum(str, Enum):
    """Supported Mars wind dataset sources"""
    MEDA = "MEDA"
    INSIGHT_TWINS = "InSight/TWINS"
    MCD = "MCD"


class TimeReferenceTypeEnum(str, Enum):
    """Type of time reference used in wind queries"""
    SOL = "sol"
    TIMESTAMP = "timestamp"


class WindDataset(BaseModel):
    """Wind dataset metadata"""
    dataset_id: str = Field(..., description="Unique dataset identifier")
    source: WindDatasetSourceEnum = Field(..., description="Dataset source")
    station_name: str = Field(..., description="Rover/lander station name")
    latitude: float = Field(..., description="Station latitude in degrees")
    longitude: float = Field(..., description="Station longitude in degrees")
    start_sol: Optional[int] = Field(default=None, description="First available Mars sol")
    end_sol: Optional[int] = Field(default=None, description="Last available Mars sol")
    start_time_utc: Optional[datetime] = Field(default=None, description="Earliest available UTC time")
    end_time_utc: Optional[datetime] = Field(default=None, description="Latest available UTC time")
    resolution: str = Field(..., description="Temporal resolution (e.g. hourly)")
    unit_speed: str = Field(default="m/s", description="Wind speed units")
    data_url: str = Field(..., description="Dataset URL")
    status: str = Field(default="active", description="Dataset status")

    class Config:
        json_schema_extra = {
            "example": {
                "dataset_id": "MEDA_PERSEVERANCE_JEZERO_V1",
                "source": "MEDA",
                "station_name": "Perseverance (Jezero)",
                "latitude": 18.4447,
                "longitude": 77.4508,
                "start_sol": 1,
                "end_sol": 1500,
                "start_time_utc": "2021-02-18T20:55:00Z",
                "end_time_utc": "2026-03-01T00:00:00Z",
                "resolution": "hourly",
                "unit_speed": "m/s",
                "data_url": "https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MARS/meda.html",
                "status": "active"
            }
        }


class WindQueryRequest(BaseModel):
    """Request model for wind query"""
    latitude: float = Field(..., description="Latitude in degrees (-90 to 90)")
    longitude: float = Field(..., description="Longitude in degrees (-180 to 180)")
    sol: Optional[int] = Field(default=None, ge=0, description="Mars sol reference")
    timestamp_utc: Optional[datetime] = Field(default=None, description="UTC timestamp reference")
    dataset_id: Optional[str] = Field(default=None, description="Optional dataset identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": 18.4447,
                "longitude": 77.4508,
                "sol": 850,
                "timestamp_utc": None,
                "dataset_id": None
            }
        }


class WindPoint(BaseModel):
    """Single wind measurement/estimate"""
    wind_speed_mps: float = Field(..., description="Wind speed in meters per second")
    wind_direction_deg: Optional[float] = Field(default=None, description="Wind direction in degrees (0-360)")
    gust_speed_mps: Optional[float] = Field(default=None, description="Optional gust speed in meters per second")
    quality_flag: Optional[str] = Field(default=None, description="Quality indicator")

    class Config:
        json_schema_extra = {
            "example": {
                "wind_speed_mps": 6.4,
                "wind_direction_deg": 132.0,
                "gust_speed_mps": 9.1,
                "quality_flag": "good"
            }
        }


class WindQueryResponse(BaseModel):
    """Response model for wind query"""
    point: WindPoint
    source: WindDatasetSourceEnum = Field(..., description="Data source used")
    dataset_id: str = Field(..., description="Dataset used for query")
    time_reference_type: TimeReferenceTypeEnum = Field(..., description="Whether response is sol or timestamp referenced")
    sol: Optional[int] = Field(default=None, description="Returned sol reference")
    timestamp_utc: Optional[datetime] = Field(default=None, description="Returned UTC timestamp")
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")
    query_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Query execution timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "point": {
                    "wind_speed_mps": 6.4,
                    "wind_direction_deg": 132.0,
                    "gust_speed_mps": 9.1,
                    "quality_flag": "good"
                },
                "source": "MEDA",
                "dataset_id": "MEDA_PERSEVERANCE_JEZERO_V1",
                "time_reference_type": "sol",
                "sol": 850,
                "timestamp_utc": None,
                "metadata": {
                    "station_name": "Perseverance (Jezero)",
                    "distance_km": 0.0,
                    "mode": "mock-ready"
                },
                "query_timestamp": "2026-04-06T12:00:00Z"
            }
        }


class WindDatasetCatalogResponse(BaseModel):
    """Response wrapper for wind datasets"""
    datasets: List[WindDataset] = Field(..., description="Available wind datasets")
    total_count: int = Field(..., description="Total number of datasets")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Catalog update time")

    class Config:
        json_schema_extra = {
            "example": {
                "datasets": [],
                "total_count": 0,
                "last_updated": "2026-04-06T12:00:00Z"
            }
        }
