"""
Wind dataset loader service
Provides source metadata and lookup helpers for Mars wind datasets
"""

from datetime import datetime
from math import sqrt
from typing import List, Optional

from models.wind_model import WindDataset, WindDatasetSourceEnum


class WindLoader:
    """
    Loader for wind dataset metadata.

    For Sprint scope, this is mock-ready but shaped for future real ingestion
    from MEDA/InSight/MCD adapters.
    """

    def __init__(self):
        self.datasets: List[WindDataset] = self._build_seed_datasets()

    def _build_seed_datasets(self) -> List[WindDataset]:
        return [
            WindDataset(
                dataset_id="MEDA_PERSEVERANCE_JEZERO_V1",
                source=WindDatasetSourceEnum.MEDA,
                station_name="Perseverance (Jezero)",
                latitude=18.4447,
                longitude=77.4508,
                start_sol=1,
                end_sol=1600,
                start_time_utc=datetime(2021, 2, 18, 20, 55),
                end_time_utc=datetime(2026, 4, 1, 0, 0),
                resolution="hourly",
                unit_speed="m/s",
                data_url="https://pds-atmospheres.nmsu.edu/data_and_services/atmospheres_data/MARS/meda.html",
                status="active",
            ),
            WindDataset(
                dataset_id="INSIGHT_TWINS_ELYSIUM_V1",
                source=WindDatasetSourceEnum.INSIGHT_TWINS,
                station_name="InSight (Elysium Planitia)",
                latitude=4.502,
                longitude=135.623,
                start_sol=1,
                end_sol=1440,
                start_time_utc=datetime(2018, 11, 26, 19, 52),
                end_time_utc=datetime(2022, 12, 15, 0, 0),
                resolution="hourly",
                unit_speed="m/s",
                data_url="https://pds-atmospheres.nmsu.edu/PDS/data/PDS4/InSight/twins_calibrated/data_calibrated/",
                status="archived",
            ),
        ]

    def list_datasets(self, source: Optional[WindDatasetSourceEnum] = None) -> List[WindDataset]:
        if source is None:
            return self.datasets
        return [dataset for dataset in self.datasets if dataset.source == source]

    def get_dataset(self, dataset_id: str) -> Optional[WindDataset]:
        for dataset in self.datasets:
            if dataset.dataset_id == dataset_id:
                return dataset
        return None

    def find_nearest_dataset(self, latitude: float, longitude: float) -> Optional[WindDataset]:
        if not self.datasets:
            return None

        best_dataset: Optional[WindDataset] = None
        best_distance = float("inf")

        for dataset in self.datasets:
            distance = self._distance_deg(latitude, longitude, dataset.latitude, dataset.longitude)
            if distance < best_distance:
                best_distance = distance
                best_dataset = dataset

        return best_dataset

    @staticmethod
    def _distance_deg(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
        return sqrt((lat_a - lat_b) ** 2 + (lon_a - lon_b) ** 2)


_loader: Optional[WindLoader] = None


def get_wind_loader() -> WindLoader:
    global _loader
    if _loader is None:
        _loader = WindLoader()
    return _loader
