"""
Data models for terrain and DTM datasets
Based on UA HIRISE DTM and Mars topography data
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class GridSpacingEnum(str, Enum):
    """Grid spacing options for HiRISE DTM products"""
    A = "0.25m"
    B = "0.5m"
    C = "1.0m"
    D = "2.0m"


class ProjectionEnum(str, Enum):
    """Projection types for DTM products"""
    EQUIRECTANGULAR = "Equirectangular"
    POLAR_STEREOGRAPHIC = "Polar Stereographic"


class DatasetTypeEnum(str, Enum):
    """Types of Mars terrain datasets"""
    HIRISE_DTM = "HiRISE DTM"
    MOLA = "MOLA"
    CTX = "CTX"
    AI4MARS = "AI4Mars"


class GeospatialBounds(BaseModel):
    """Geospatial bounds for a dataset"""
    north_latitude: float = Field(..., description="Northern extent in degrees")
    south_latitude: float = Field(..., description="Southern extent in degrees")
    east_longitude: float = Field(..., description="Eastern extent in degrees")
    west_longitude: float = Field(..., description="Western extent in degrees")

    class Config:
        json_schema_extra = {
            "example": {
                "north_latitude": -75.5,
                "south_latitude": -76.0,
                "east_longitude": 45.2,
                "west_longitude": 44.8
            }
        }


class DTMDataset(BaseModel):
    """HiRISE Digital Terrain Model dataset metadata"""
    product_id: str = Field(..., description="Unique DTM product identifier (e.g., DTE_022534_1120_021534_1120_UA00)")
    observation_id: str = Field(..., description="HiRISE observation ID (e.g., ESP_022534_1120)")
    orbit_number: int = Field(..., description="Mars Reconnaissance Orbiter orbit number")
    acquisition_date: datetime = Field(..., description="Date DTM was acquired")
    release_date: datetime = Field(..., description="Date DTM was released to PDS")
    grid_spacing: GridSpacingEnum = Field(..., description="DTM post spacing resolution")
    projection: ProjectionEnum = Field(default=ProjectionEnum.EQUIRECTANGULAR, description="Map projection type")
    bounds: GeospatialBounds = Field(..., description="Geographic extent")
    vertical_precision_cm: float = Field(default=50.0, description="Vertical precision in centimeters")
    file_size_mb: float = Field(..., description="Size of DTM file in megabytes")
    data_url: str = Field(..., description="URL to download DTM data")
    browse_url: Optional[str] = Field(default=None, description="URL to browse image")
    institution: str = Field(default="University of Arizona", description="Producing institution")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "DTE_022534_1120_021534_1120_UA00",
                "observation_id": "ESP_022534_1120",
                "orbit_number": 22534,
                "acquisition_date": "2012-08-15T00:00:00Z",
                "release_date": "2013-06-20T00:00:00Z",
                "grid_spacing": "1.0m",
                "projection": "Equirectangular",
                "bounds": {
                    "north_latitude": -75.5,
                    "south_latitude": -76.0,
                    "east_longitude": 45.2,
                    "west_longitude": 44.8
                },
                "vertical_precision_cm": 50.0,
                "file_size_mb": 128.5,
                "data_url": "https://pds.nasa.gov/...",
                "browse_url": "https://www.uahirise.org/...",
                "institution": "University of Arizona"
            }
        }


class ElevationPoint(BaseModel):
    """Single elevation data point"""
    latitude: float = Field(..., description="Latitude in degrees")
    longitude: float = Field(..., description="Longitude in degrees")
    elevation_m: float = Field(..., description="Elevation above Mars areoid in meters")
    accuracy_cm: float = Field(default=50.0, description="Vertical accuracy in centimeters")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -75.75,
                "longitude": 45.0,
                "elevation_m": -2234.5,
                "accuracy_cm": 50.0
            }
        }


class ElevationQueryRequest(BaseModel):
    """Request for elevation data at specific coordinates"""
    latitude: float = Field(..., description="Latitude in degrees (-90 to 90)")
    longitude: float = Field(..., description="Longitude in degrees (-180 to 180)")
    dataset_id: Optional[str] = Field(default=None, description="Specific DTM to query, defaults to closest coverage")

    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -75.75,
                "longitude": 45.0,
                "dataset_id": None
            }
        }


class ElevationQueryResponse(BaseModel):
    """Response with elevation data for queried coordinates"""
    point: ElevationPoint
    dataset_id: str = Field(..., description="DTM product used for this query")
    query_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Query execution time")

    class Config:
        json_schema_extra = {
            "example": {
                "point": {
                    "latitude": -75.75,
                    "longitude": 45.0,
                    "elevation_m": -2234.5,
                    "accuracy_cm": 50.0
                },
                "dataset_id": "DTE_022534_1120_021534_1120_UA00",
                "query_timestamp": "2026-03-16T10:30:00Z"
            }
        }


class TerrainTile(BaseModel):
    """Terrain tile data (heightmap for a region)"""
    tile_id: str = Field(..., description="Unique tile identifier")
    bounds: GeospatialBounds = Field(..., description="Geographic bounds of tile")
    resolution: str = Field(..., description="Tile resolution (e.g., '1.0m')")
    min_elevation_m: float = Field(..., description="Minimum elevation in tile")
    max_elevation_m: float = Field(..., description="Maximum elevation in tile")
    mean_elevation_m: float = Field(..., description="Mean elevation in tile")
    data_url: str = Field(..., description="URL to download tile heightmap data")
    format: str = Field(default="GeoTIFF", description="Data format (GeoTIFF, IMG, etc.)")

    class Config:
        json_schema_extra = {
            "example": {
                "tile_id": "TILE_022534_1120_0_0",
                "bounds": {
                    "north_latitude": -75.5,
                    "south_latitude": -75.75,
                    "east_longitude": 45.25,
                    "west_longitude": 45.0
                },
                "resolution": "1.0m",
                "min_elevation_m": -2350.0,
                "max_elevation_m": -2100.0,
                "mean_elevation_m": -2234.5,
                "data_url": "https://api.rover.local/tiles/TILE_022534_1120_0_0.tiff",
                "format": "GeoTIFF"
            }
        }


class TerrainTileQuery(BaseModel):
    """Request for terrain tiles in a region"""
    north_latitude: float = Field(..., description="Northern extent in degrees")
    south_latitude: float = Field(..., description="Southern extent in degrees")
    east_longitude: float = Field(..., description="Eastern extent in degrees")
    west_longitude: float = Field(..., description="Western extent in degrees")
    resolution: Optional[str] = Field(default="1.0m", description="Desired tile resolution")
    dataset_id: Optional[str] = Field(default=None, description="Specific dataset to query")

    class Config:
        json_schema_extra = {
            "example": {
                "north_latitude": -75.5,
                "south_latitude": -76.0,
                "east_longitude": 45.2,
                "west_longitude": 44.8,
                "resolution": "1.0m",
                "dataset_id": None
            }
        }


class TerrainTileResponse(BaseModel):
    """Response containing terrain tiles"""
    tiles: List[TerrainTile] = Field(..., description="List of available tiles")
    total_count: int = Field(..., description="Total number of tiles")
    datasets_used: List[str] = Field(..., description="DTM products used")

    class Config:
        json_schema_extra = {
            "example": {
                "tiles": [
                    {
                        "tile_id": "TILE_022534_1120_0_0",
                        "bounds": {
                            "north_latitude": -75.5,
                            "south_latitude": -75.75,
                            "east_longitude": 45.25,
                            "west_longitude": 45.0
                        },
                        "resolution": "1.0m",
                        "min_elevation_m": -2350.0,
                        "max_elevation_m": -2100.0,
                        "mean_elevation_m": -2234.5,
                        "data_url": "https://api.rover.local/tiles/TILE_022534_1120_0_0.tiff",
                        "format": "GeoTIFF"
                    }
                ],
                "total_count": 1,
                "datasets_used": ["DTE_022534_1120_021534_1120_UA00"]
            }
        }


class DatasetCatalogResponse(BaseModel):
    """Response containing DTM dataset catalog"""
    datasets: List[DTMDataset] = Field(..., description="Available DTM datasets")
    total_count: int = Field(..., description="Total number of datasets")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Catalog last updated")

    class Config:
        json_schema_extra = {
            "example": {
                "datasets": [],
                "total_count": 0,
                "last_updated": "2026-03-16T10:30:00Z"
            }
        }
