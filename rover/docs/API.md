# Terrain API Documentation

## Overview

The Terrain API provides access to Mars elevation data from HiRISE DTM (Digital Terrain Models) and related datasets. It supports querying elevation at specific coordinates, retrieving terrain tiles for regions, and accessing dataset metadata.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently not required. In production, implement API key or OAuth2 authentication.

## Datasets

### Available Mars Terrain Sources

1. **HiRISE DTM** (High Resolution Imaging Science Experiment)
   - Resolution: 0.25m - 2.0m post spacing
   - Coverage: Selected regions on Mars
   - Source: UA HIRISE (https://www.uahirise.org/dtm/)
   - Vertical precision: ~50cm

2. **MOLA** (Mars Orbiter Laser Altimeter)
   - Resolution: ~463m post spacing
   - Coverage: Global
   - Source: NASA Planetary Data System
   - Baseline for HiRISE DTM registration

3. **CTX DEM** (Context Camera DEM)
   - Resolution: ~20m post spacing
   - Coverage: Selected regions
   - Source: NASA MRO

4. **AI4Mars**
   - Rover-detected terrain features
   - Classification data
   - Source: University of Chicago

## Endpoints

### 1. List Datasets

**Endpoint:** `GET /terrain/datasets`

**Description:** Get catalog of available terrain datasets

**Query Parameters:**
- `region` (optional): Filter by region name
- `limit` (optional, default=100): Max results (1-1000)
- `offset` (optional, default=0): Pagination offset

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/datasets?limit=10&offset=0"
```

**Example Response:**
```json
{
  "datasets": [
    {
      "product_id": "DTE_022534_1120_021534_1120_UA00",
      "observation_id": "ESP_022534_1120",
      "orbit_number": 22534,
      "acquisition_date": "2012-08-15T00:00:00",
      "release_date": "2013-06-20T00:00:00",
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
      "data_url": "https://pds-geosciences.wustl.edu/mro/mro-m-hirise-3-dtm-v1/",
      "browse_url": "https://www.uahirise.org/dtm/ESP_022534_1120",
      "institution": "University of Arizona"
    }
  ],
  "total_count": 3,
  "last_updated": "2026-03-16T10:30:00"
}
```

---

### 2. Get Dataset Metadata

**Endpoint:** `GET /terrain/datasets/{dataset_id}`

**Description:** Get detailed metadata for a specific dataset

**Path Parameters:**
- `dataset_id`: Product ID (e.g., `DTE_022534_1120_021534_1120_UA00`) or observation ID (e.g., `ESP_022534_1120`)

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/datasets/ESP_022534_1120"
```

**Example Response:** Same as individual dataset object from list endpoint

---

### 3. Query Elevation at Coordinates

**Endpoint:** `POST /terrain/elevation`

**Description:** Get elevation data for specific latitude/longitude

**Request Body:**
```json
{
  "latitude": -75.75,
  "longitude": 45.0,
  "dataset_id": null
}
```

**Parameters:**
- `latitude` (required): -90 to 90 degrees
- `longitude` (required): -180 to 180 degrees
- `dataset_id` (optional): Specific DTM product to query

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/terrain/elevation" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -75.75,
    "longitude": 45.0
  }'
```

**Example Response:**
```json
{
  "point": {
    "latitude": -75.75,
    "longitude": 45.0,
    "elevation_m": -2234.5,
    "accuracy_cm": 50.0
  },
  "dataset_id": "DTE_022534_1120_021534_1120_UA00",
  "query_timestamp": "2026-03-16T10:30:00Z"
}
```

---

### 4. Quick Elevation Lookup (URL Parameters)

**Endpoint:** `GET /terrain/elevation/{latitude}/{longitude}`

**Description:** Simple elevation query without JSON body

**Path Parameters:**
- `latitude`: Latitude in degrees
- `longitude`: Longitude in degrees

**Query Parameters:**
- `dataset_id` (optional): Specific DTM to use

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/elevation/-75.75/45.0"
```

**Example Response:**
```json
{
  "latitude": -75.75,
  "longitude": 45.0,
  "elevation_m": -2234.5,
  "accuracy_cm": 50.0
}
```

---

### 5. Query Terrain Tiles for Region

**Endpoint:** `POST /terrain/tiles`

**Description:** Get terrain elevation tiles for a geographic region

**Request Body:**
```json
{
  "north_latitude": -75.5,
  "south_latitude": -76.0,
  "east_longitude": 45.2,
  "west_longitude": 44.8,
  "resolution": "1.0m",
  "dataset_id": null
}
```

**Parameters:**
- `north_latitude` (required): Northern extent
- `south_latitude` (required): Southern extent
- `east_longitude` (required): Eastern extent
- `west_longitude` (required): Western extent
- `resolution` (optional): Tile resolution ('0.25m', '0.5m', '1.0m', '2.0m')
- `dataset_id` (optional): Specific DTM product

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/terrain/tiles" \
  -H "Content-Type: application/json" \
  -d '{
    "north_latitude": -75.5,
    "south_latitude": -76.0,
    "east_longitude": 45.2,
    "west_longitude": 44.8,
    "resolution": "1.0m"
  }'
```

**Example Response:**
```json
{
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
```

---

### 6. Health Check

**Endpoint:** `GET /terrain/health`

**Description:** Check terrain service status

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/health"
```

**Example Response:**
```json
{
  "status": "healthy",
  "datasets_available": 3,
  "timestamp": "2026-03-16T10:30:00Z"
}
```

---

## Usage Examples

### Example 1: Find elevation in Jezero Crater (Rover landing site)

```bash
curl -X POST "http://localhost:8000/api/v1/terrain/elevation" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -18.38,
    "longitude": 77.45
  }'
```

### Example 2: Query terrain for rover navigation path

```bash
curl -X POST "http://localhost:8000/api/v1/terrain/tiles" \
  -H "Content-Type: application/json" \
  -d '{
    "north_latitude": -18.3,
    "south_latitude": -18.5,
    "east_longitude": 77.5,
    "west_longitude": 77.3,
    "resolution": "0.5m"
  }'
```

### Example 3: Batch elevation queries (pseudo-code)

```python
import requests

coordinates = [
    (-18.38, 77.45),   # Jezero Crater
    (-4.589, 137.4),   # Valles Marineris
    (-37.645, 138.45), # Hellas Planitia
]

for lat, lon in coordinates:
    response = requests.get(
        f"http://localhost:8000/api/v1/terrain/elevation/{lat}/{lon}"
    )
    print(f"Elevation at ({lat}, {lon}): {response.json()['elevation_m']}m")
```

---

## Error Handling

### Common Error Responses

**400 Bad Request** - Invalid coordinates or parameters
```json
{
  "detail": "Latitude must be between -90 and 90"
}
```

**404 Not Found** - No data available for region
```json
{
  "detail": "No terrain data available for coordinates (18.5, 200.0)"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error",
  "error": "Error details"
}
```

---

## Testing in Swagger

Access the interactive Swagger documentation at:
```
http://localhost:8000/docs
```

Or ReDoc documentation at:
```
http://localhost:8000/redoc
```

---

## Data Formats

### GeoTIFF Format

Terrain tiles are provided in GeoTIFF format for compatibility with:
- GDAL/rasterio (Python)
- ArcGIS
- QGIS
- Standard GIS software

### Elevation Units

All elevations are in meters above Mars areoid datum (MOLA reference).

---

## Rate Limiting

Currently unlimited. Production deployment should implement:
- Per-IP rate limiting
- User quota management
- Cache strategies

---

## Future Enhancements

- Terrain classification (rock type, slope steepness)
- Obstacle detection (boulders, cliffs)
- Traversability analysis
- Thermal properties
- Seasonal data (ice coverage)
- 3D mesh generation from DTM
