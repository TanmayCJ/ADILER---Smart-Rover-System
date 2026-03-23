"""
Terrain API endpoints for Mars DTM data
Provides access to HiRISE DTM and related terrain datasets
"""

from fastapi import APIRouter, Query, Path, HTTPException, status
from typing import Optional, List
from datetime import datetime
from models.terrain_model import (
    DTMDataset, ElevationQueryRequest, ElevationQueryResponse,
    ElevationPoint, TerrainTile, TerrainTileQuery, TerrainTileResponse,
    DatasetCatalogResponse, GeospatialBounds, GridSpacingEnum,
    ProjectionEnum, DatasetTypeEnum
)

router = APIRouter(
    prefix="/api/v1/terrain",
    tags=["Terrain"],
    responses={404: {"description": "Not found"}}
)

# Mock dataset catalog - in production this would be loaded from database
SAMPLE_DATASETS = [
    DTMDataset(
        product_id="DTE_022534_1120_021534_1120_UA00",
        observation_id="ESP_022534_1120",
        orbit_number=22534,
        acquisition_date=datetime(2012, 8, 15),
        release_date=datetime(2013, 6, 20),
        grid_spacing=GridSpacingEnum.C,
        projection=ProjectionEnum.EQUIRECTANGULAR,
        bounds=GeospatialBounds(
            north_latitude=-75.5,
            south_latitude=-76.0,
            east_longitude=45.2,
            west_longitude=44.8
        ),
        vertical_precision_cm=50.0,
        file_size_mb=128.5,
        data_url="https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/",
        browse_url="https://www.uahirise.org/dtm/ESP_022534_1120",
        institution="University of Arizona"
    ),
    DTMDataset(
        product_id="DTE_089104_2190_084704_2190_UA00",
        observation_id="ESP_089104_2190",
        orbit_number=89104,
        acquisition_date=datetime(2023, 3, 10),
        release_date=datetime(2023, 8, 15),
        grid_spacing=GridSpacingEnum.C,
        projection=ProjectionEnum.EQUIRECTANGULAR,
        bounds=GeospatialBounds(
            north_latitude=-22.0,
            south_latitude=-22.5,
            east_longitude=335.0,
            west_longitude=334.5
        ),
        vertical_precision_cm=50.0,
        file_size_mb=256.0,
        data_url="https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/",
        browse_url="https://www.uahirise.org/dtm/ESP_089104_2190",
        institution="University of Arizona"
    ),
    DTMDataset(
        product_id="DTE_076968_1475_071768_1475_UA00",
        observation_id="ESP_076968_1475",
        orbit_number=76968,
        acquisition_date=datetime(2022, 12, 5),
        release_date=datetime(2023, 4, 10),
        grid_spacing=GridSpacingEnum.B,
        projection=ProjectionEnum.EQUIRECTANGULAR,
        bounds=GeospatialBounds(
            north_latitude=-37.2,
            south_latitude=-37.8,
            east_longitude=157.5,
            west_longitude=157.0
        ),
        vertical_precision_cm=30.0,
        file_size_mb=512.0,
        data_url="https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/",
        browse_url="https://www.uahirise.org/dtm/ESP_076968_1475",
        institution="University of Arizona"
    )
]


@router.get(
    "/datasets",
    response_model=DatasetCatalogResponse,
    summary="List available DTM datasets",
    description="Get catalog of available HiRISE DTM and other Mars terrain datasets"
)
def list_datasets(
    region: Optional[str] = Query(None, description="Filter by region (e.g., 'Valles Marineris', 'Jezero Crater')"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """
    Retrieve a catalog of available Mars terrain datasets.
    
    - **region**: Optional region name filter
    - **limit**: Maximum results (1-1000)
    - **offset**: Pagination offset
    
    Returns dataset metadata including bounds, resolution, and download links.
    """
    # In production, would query database with filters
    datasets = SAMPLE_DATASETS[offset:offset+limit]
    
    return DatasetCatalogResponse(
        datasets=datasets,
        total_count=len(SAMPLE_DATASETS),
        last_updated=datetime.utcnow()
    )


@router.get(
    "/datasets/{dataset_id}",
    response_model=DTMDataset,
    summary="Get dataset metadata",
    description="Retrieve detailed metadata for a specific DTM product"
)
def get_dataset_metadata(dataset_id: str):
    """
    Get detailed metadata for a specific DTM dataset.
    
    - **dataset_id**: Product ID (e.g., 'DTE_022534_1120_021534_1120_UA00')
    """
    for dataset in SAMPLE_DATASETS:
        if dataset.product_id == dataset_id or dataset.observation_id == dataset_id:
            return dataset
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Dataset {dataset_id} not found"
    )


@router.post(
    "/elevation",
    response_model=ElevationQueryResponse,
    summary="Query elevation at coordinates",
    description="Get elevation data for specific latitude/longitude coordinates"
)
def query_elevation(request: ElevationQueryRequest):
    """
    Query elevation at specific Mars coordinates.
    
    Returns elevation above Mars areoid (datum).
    
    **Example usage:**
    - Query south pole terrain: lat=-75.75, lon=45.0
    - Query Jezero Crater region: lat=-18.38, lon=77.45
    - Query Valles Marineris: lat=-13.5, lon=-72.0
    """
    # Validate coordinates
    if not -90 <= request.latitude <= 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90"
        )
    if not -180 <= request.longitude <= 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180"
        )
    
    # Find best dataset covering this point
    dataset = None
    if request.dataset_id:
        dataset = next((d for d in SAMPLE_DATASETS if d.product_id == request.dataset_id), None)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {request.dataset_id} not found"
            )
    else:
        # Find first dataset containing these coordinates
        for d in SAMPLE_DATASETS:
            if (d.bounds.south_latitude <= request.latitude <= d.bounds.north_latitude and
                d.bounds.west_longitude <= request.longitude <= d.bounds.east_longitude):
                dataset = d
                break
    
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No terrain data available for coordinates ({request.latitude}, {request.longitude})"
        )
    
    # Mock elevation calculation (in production, would query actual DTM data)
    # Simulate elevation based on coordinates and dataset
    import math
    base_elevation = -2000.0
    variation = 300.0 * math.sin((request.latitude + 90) / 20) * math.cos(request.longitude / 30)
    elevation = base_elevation + variation
    
    return ElevationQueryResponse(
        point=ElevationPoint(
            latitude=request.latitude,
            longitude=request.longitude,
            elevation_m=elevation,
            accuracy_cm=dataset.vertical_precision_cm
        ),
        dataset_id=dataset.product_id,
        query_timestamp=datetime.utcnow()
    )


@router.post(
    "/tiles",
    response_model=TerrainTileResponse,
    summary="Request terrain tiles for region",
    description="Get terrain elevation tiles for a geographic region"
)
def query_terrain_tiles(request: TerrainTileQuery):
    """
    Get terrain tiles for a geographic region.
    
    Tiles contain heightmap data for efficient terrain visualization and analysis.
    
    **Parameters:**
    - **north_latitude, south_latitude**: Region latitude bounds
    - **east_longitude, west_longitude**: Region longitude bounds
    - **resolution**: Tile resolution ('0.25m', '0.5m', '1.0m', '2.0m')
    - **dataset_id**: Specific DTM to use (optional)
    """
    # Validate bounds
    if request.south_latitude >= request.north_latitude:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="South latitude must be less than north latitude"
        )
    if request.west_longitude >= request.east_longitude:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="West longitude must be less than east longitude"
        )
    
    # Find covering datasets
    covering_datasets = []
    for dataset in SAMPLE_DATASETS:
        # Check if dataset bounds overlap with query region
        if not (dataset.bounds.south_latitude > request.north_latitude or
                dataset.bounds.north_latitude < request.south_latitude or
                dataset.bounds.east_longitude < request.west_longitude or
                dataset.bounds.west_longitude > request.east_longitude):
            covering_datasets.append(dataset)
    
    if request.dataset_id:
        covering_datasets = [d for d in covering_datasets if d.product_id == request.dataset_id]
        if not covering_datasets:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {request.dataset_id} does not cover requested region"
            )
    
    if not covering_datasets:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No terrain data available for region"
        )
    
    # Generate mock tiles
    tiles = []
    tile_idx = 0
    
    # Create tiles with ~0.5 degree spacing
    lat = request.south_latitude
    while lat < request.north_latitude:
        lon = request.west_longitude
        next_lat = min(lat + 0.5, request.north_latitude)
        while lon < request.east_longitude:
            next_lon = min(lon + 0.5, request.east_longitude)
            
            tile = TerrainTile(
                tile_id=f"TILE_{covering_datasets[0].observation_id}_{tile_idx}",
                bounds=GeospatialBounds(
                    north_latitude=next_lat,
                    south_latitude=lat,
                    east_longitude=next_lon,
                    west_longitude=lon
                ),
                resolution=request.resolution or "1.0m",
                min_elevation_m=-2350.0,
                max_elevation_m=-2100.0,
                mean_elevation_m=-2234.5,
                data_url=f"https://api.rover.local/tiles/TILE_{covering_datasets[0].observation_id}_{tile_idx}.tiff",
                format="GeoTIFF"
            )
            tiles.append(tile)
            tile_idx += 1
            lon = next_lon
        lat = next_lat
    
    return TerrainTileResponse(
        tiles=tiles,
        total_count=len(tiles),
        datasets_used=[d.product_id for d in covering_datasets]
    )


@router.get(
    "/elevation/{latitude}/{longitude}",
    response_model=ElevationPoint,
    summary="Quick elevation lookup",
    description="Simple elevation query via URL parameters"
)
def get_elevation(
    latitude: float = Path(..., ge=-90, le=90, description="Latitude in degrees"),
    longitude: float = Path(..., ge=-180, le=180, description="Longitude in degrees"),
    dataset_id: Optional[str] = Query(None, description="Optional specific dataset")
):
    """
    Quick elevation lookup by coordinates.
    
    Returns elevation above Mars areoid datum.
    """
    request = ElevationQueryRequest(
        latitude=latitude,
        longitude=longitude,
        dataset_id=dataset_id
    )
    
    response = query_elevation(request)
    return response.point


@router.get(
    "/health",
    summary="Health check",
    description="Check terrain service availability"
)
def health_check():
    """Check if terrain service is operational."""
    return {
        "status": "healthy",
        "datasets_available": len(SAMPLE_DATASETS),
        "timestamp": datetime.utcnow().isoformat()
    }
