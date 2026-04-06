"""
Wind business logic service
Separates query logic from route handlers
"""

from datetime import datetime
from math import cos, sin
from typing import Optional

from fastapi import HTTPException, status

from models.wind_model import (
    TimeReferenceTypeEnum,
    WindDataset,
    WindDatasetCatalogResponse,
    WindDatasetSourceEnum,
    WindPoint,
    WindQueryRequest,
    WindQueryResponse,
)
from services.wind_loader import get_wind_loader


class WindService:
    """Domain service for wind dataset listing and wind queries."""

    def __init__(self):
        self.loader = get_wind_loader()

    def list_datasets(self, source: Optional[WindDatasetSourceEnum], limit: int, offset: int) -> WindDatasetCatalogResponse:
        datasets = self.loader.list_datasets(source)
        paged = datasets[offset : offset + limit]
        return WindDatasetCatalogResponse(
            datasets=paged,
            total_count=len(datasets),
            last_updated=datetime.utcnow(),
        )

    def query_wind(self, request: WindQueryRequest) -> WindQueryResponse:
        self._validate_coordinates(request.latitude, request.longitude)
        self._validate_time_reference(request)

        dataset = self._resolve_dataset(request)
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No wind dataset available for coordinates ({request.latitude}, {request.longitude})",
            )

        wind_point = self._mock_wind_from_location_and_time(request, dataset)
        time_reference_type, sol_value, timestamp_value = self._resolve_time_reference(request)

        return WindQueryResponse(
            point=wind_point,
            source=dataset.source,
            dataset_id=dataset.dataset_id,
            time_reference_type=time_reference_type,
            sol=sol_value,
            timestamp_utc=timestamp_value,
            metadata={
                "station_name": dataset.station_name,
                "dataset_status": dataset.status,
                "mode": "mock-ready",
            },
            query_timestamp=datetime.utcnow(),
        )

    @staticmethod
    def _validate_coordinates(latitude: float, longitude: float) -> None:
        if not -90 <= latitude <= 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Latitude must be between -90 and 90",
            )
        if not -180 <= longitude <= 180:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Longitude must be between -180 and 180",
            )

    @staticmethod
    def _validate_time_reference(request: WindQueryRequest) -> None:
        if request.sol is None and request.timestamp_utc is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either sol or timestamp_utc must be provided",
            )

    def _resolve_dataset(self, request: WindQueryRequest) -> Optional[WindDataset]:
        if request.dataset_id:
            dataset = self.loader.get_dataset(request.dataset_id)
            if dataset is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dataset {request.dataset_id} not found",
                )
            return dataset

        return self.loader.find_nearest_dataset(request.latitude, request.longitude)

    @staticmethod
    def _resolve_time_reference(request: WindQueryRequest):
        if request.sol is not None:
            return TimeReferenceTypeEnum.SOL, request.sol, None
        return TimeReferenceTypeEnum.TIMESTAMP, None, request.timestamp_utc

    @staticmethod
    def _mock_wind_from_location_and_time(request: WindQueryRequest, dataset: WindDataset) -> WindPoint:
        """
        Placeholder synthetic wind response.

        This keeps endpoint behavior stable while real MEDA/InSight adapters
        are wired in future sprints.
        """
        time_seed = float(request.sol if request.sol is not None else request.timestamp_utc.timestamp())
        spatial = abs(sin(request.latitude / 12.0) + cos(request.longitude / 18.0))
        temporal = abs(sin(time_seed / 50000.0))

        base_speed = 2.0 if dataset.source == WindDatasetSourceEnum.MEDA else 1.5
        speed = round(base_speed + (spatial * 4.0) + (temporal * 3.0), 2)
        direction = round(((request.longitude % 360) + temporal * 45.0) % 360, 2)
        gust = round(speed + (0.8 + spatial * 1.5), 2)

        quality = "good" if dataset.status == "active" else "archived"

        return WindPoint(
            wind_speed_mps=speed,
            wind_direction_deg=direction,
            gust_speed_mps=gust,
            quality_flag=quality,
        )


_service: Optional[WindService] = None


def get_wind_service() -> WindService:
    global _service
    if _service is None:
        _service = WindService()
    return _service
