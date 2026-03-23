"""
Dataset loading and management service
Handles loading HiRISE DTM and other Mars terrain datasets
"""

import os
import json
from typing import List, Optional
from pathlib import Path
from datetime import datetime
from ..models.terrain_model import DTMDataset, GeospatialBounds, GridSpacingEnum, ProjectionEnum


class DatasetLoader:
    """
    Service for loading and managing Mars terrain datasets
    
    In production, this would:
    - Load dataset metadata from PDS catalog
    - Cache dataset information
    - Provide search and filtering
    - Handle dataset updates
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize dataset loader
        
        Args:
            cache_dir: Directory for caching dataset metadata
        """
        self.cache_dir = cache_dir or "./datasets/cache"
        self.datasets: List[DTMDataset] = []
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
    
    def load_datasets_from_pds(self) -> List[DTMDataset]:
        """
        Load datasets from PDS (Planetary Data System) catalog
        
        In production, this would query the PDS API via:
        - https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/
        
        Returns:
            List of available DTM datasets
        """
        # This is a placeholder for actual PDS catalog loading
        # Would implement HTTP requests to PDS API
        pass
    
    def load_datasets_from_csv(self, csv_path: str) -> List[DTMDataset]:
        """
        Load datasets from CSV catalog file
        
        CSV should have columns:
        - product_id, observation_id, orbit_number, acquisition_date,
        - release_date, grid_spacing, bounds_north, bounds_south,
        - bounds_east, bounds_west, vertical_precision_cm, file_size_mb,
        - data_url, browse_url
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of DTM datasets
        """
        # Would implement CSV parsing
        pass
    
    def load_datasets_from_json(self, json_path: str) -> List[DTMDataset]:
        """
        Load datasets from JSON manifest file
        
        Args:
            json_path: Path to JSON manifest
            
        Returns:
            List of DTM datasets
        """
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            datasets = []
            for item in data.get('datasets', []):
                dataset = self._parse_dataset_dict(item)
                if dataset:
                    datasets.append(dataset)
            
            self.datasets = datasets
            return datasets
        except Exception as e:
            print(f"Error loading datasets from JSON: {e}")
            return []
    
    def _parse_dataset_dict(self, data: dict) -> Optional[DTMDataset]:
        """Parse dataset dictionary into DTMDataset model"""
        try:
            bounds = GeospatialBounds(
                north_latitude=data['bounds']['north_latitude'],
                south_latitude=data['bounds']['south_latitude'],
                east_longitude=data['bounds']['east_longitude'],
                west_longitude=data['bounds']['west_longitude']
            )
            
            return DTMDataset(
                product_id=data['product_id'],
                observation_id=data['observation_id'],
                orbit_number=data['orbit_number'],
                acquisition_date=datetime.fromisoformat(data['acquisition_date']),
                release_date=datetime.fromisoformat(data['release_date']),
                grid_spacing=GridSpacingEnum(data['grid_spacing']),
                projection=ProjectionEnum(data.get('projection', 'Equirectangular')),
                bounds=bounds,
                vertical_precision_cm=data.get('vertical_precision_cm', 50.0),
                file_size_mb=data['file_size_mb'],
                data_url=data['data_url'],
                browse_url=data.get('browse_url'),
                institution=data.get('institution', 'University of Arizona')
            )
        except Exception as e:
            print(f"Error parsing dataset: {e}")
            return None
    
    def search_datasets(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        region_name: Optional[str] = None,
        resolution: Optional[str] = None
    ) -> List[DTMDataset]:
        """
        Search datasets by various criteria
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            region_name: Region name (would require region database)
            resolution: Desired resolution ('0.25m', '0.5m', '1.0m', '2.0m')
            
        Returns:
            Filtered list of datasets
        """
        results = self.datasets
        
        # Filter by geographic location
        if latitude is not None and longitude is not None:
            results = [
                d for d in results
                if d.bounds.south_latitude <= latitude <= d.bounds.north_latitude
                and d.bounds.west_longitude <= longitude <= d.bounds.east_longitude
            ]
        
        # Filter by resolution
        if resolution:
            results = [d for d in results if d.grid_spacing.value == resolution]
        
        return results
    
    def get_dataset(self, product_id: str) -> Optional[DTMDataset]:
        """Get specific dataset by product ID"""
        for dataset in self.datasets:
            if dataset.product_id == product_id:
                return dataset
        return None
    
    def cache_dataset_metadata(self, dataset: DTMDataset):
        """Cache dataset metadata to disk"""
        cache_file = Path(self.cache_dir) / f"{dataset.product_id}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(dataset.model_dump(), f, indent=2, default=str)
        except Exception as e:
            print(f"Error caching dataset: {e}")
    
    def load_cached_datasets(self) -> List[DTMDataset]:
        """Load all cached datasets from disk"""
        datasets = []
        cache_path = Path(self.cache_dir)
        
        if not cache_path.exists():
            return datasets
        
        for json_file in cache_path.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                dataset = self._parse_dataset_dict(data)
                if dataset:
                    datasets.append(dataset)
            except Exception as e:
                print(f"Error loading cached dataset {json_file}: {e}")
        
        self.datasets = datasets
        return datasets


# Global dataset loader instance
_loader = None


def get_dataset_loader(cache_dir: Optional[str] = None) -> DatasetLoader:
    """Get or create global dataset loader"""
    global _loader
    if _loader is None:
        _loader = DatasetLoader(cache_dir)
    return _loader
