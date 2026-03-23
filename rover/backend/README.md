# Mars Rover AI Simulator - Backend API

Fast and modern FastAPI-based backend service for Mars terrain data access and rover simulation control.

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start Server

```bash
python main.py
```

Server runs on: `http://localhost:8000`

### 3. Access Swagger UI

```
http://localhost:8000/docs
```

## API Base URL

```
http://localhost:8000/api/v1
```

## Terrain Endpoints

### 1. List Datasets

**Endpoint:** `GET /terrain/datasets`

**Description:** Get catalog of available Mars terrain (HiRISE DTM) datasets

**Query Parameters:**
- `region` (optional): Filter by region name
- `limit` (optional, default=100): Max results (1-1000)
- `offset` (optional, default=0): Pagination offset

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/datasets?limit=10"
```

**Response (200 OK):**
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
  "last_updated": "2026-03-23T12:30:00.123456"
}
```

**Error Responses:**
- `404 Not Found`: No datasets match filter criteria

---

### 2. Get Dataset Metadata

**Endpoint:** `GET /terrain/datasets/{dataset_id}`

**Description:** Get detailed metadata for a specific DTM product

**Path Parameters:**
- `dataset_id` (required): Product ID or Observation ID

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/datasets/ESP_022534_1120"
```

**Response (200 OK):**
```json
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
```

**Error Responses:**
- `404 Not Found`: Dataset not found

---

### 3. Query Elevation at Coordinates

**Endpoint:** `POST /terrain/elevation`

**Description:** Get elevation data (Mars areoid) at specific latitude/longitude

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
- `dataset_id` (optional): Specific DTM product; if null, uses best coverage

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/terrain/elevation" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": -75.75,
    "longitude": 45.0
  }'
```

**Response (200 OK):**
```json
{
  "point": {
    "latitude": -75.75,
    "longitude": 45.0,
    "elevation_m": -2234.5,
    "accuracy_cm": 50.0
  },
  "dataset_id": "DTE_022534_1120_021534_1120_UA00",
  "query_timestamp": "2026-03-23T12:30:00.123456Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid coordinates
  ```json
  { "detail": "Latitude must be between -90 and 90" }
  ```
- `404 Not Found`: No terrain data for region
  ```json
  { "detail": "No terrain data available for coordinates (50.0, 100.0)" }
  ```

---

### 4. Quick Elevation Lookup

**Endpoint:** `GET /terrain/elevation/{latitude}/{longitude}`

**Description:** Simple elevation query via URL parameters (no JSON required)

**Path Parameters:**
- `latitude` (required): Latitude in degrees
- `longitude` (required): Longitude in degrees

**Query Parameters:**
- `dataset_id` (optional): Specific DTM to use

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/elevation/-18.38/77.45"
```

**Response (200 OK):**
```json
{
  "latitude": -18.38,
  "longitude": 77.45,
  "elevation_m": -2100.2,
  "accuracy_cm": 50.0
}
```

**Notable Locations:**
- **Jezero Crater** (Rover landing site): lat=-18.38, lon=77.45
- **South Pole**: lat=-75.75, lon=45.0
- **Valles Marineris**: lat=-13.5, lon=-72.0
- **Hellas Planitia**: lat=-42.0, lon=71.0

---

### 5. Query Terrain Tiles for Region

**Endpoint:** `POST /terrain/tiles`

**Description:** Get terrain elevation tiles for visualization in a geographic region

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
- `resolution` (optional, default="1.0m"): Desired resolution
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

**Response (200 OK):**
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

**Error Responses:**
- `400 Bad Request`: Invalid bounds
  ```json
  { "detail": "South latitude must be less than north latitude" }
  ```
- `404 Not Found`: No coverage for region
  ```json
  { "detail": "No terrain data available for region" }
  ```

---

### 6. Health Check

**Endpoint:** `GET /terrain/health`

**Description:** Check terrain service operational status

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/terrain/health"
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "datasets_available": 3,
  "timestamp": "2026-03-23T12:30:00Z"
}
```

---

## Root Endpoints

### Health Check (Root)

**Endpoint:** `GET /health`

**Response (200 OK):**
```json
{
  "status": "operational",
  "timestamp": "2026-03-23T12:30:00Z",
  "service": "Mars Rover AI Backend",
  "version": "0.1.0"
}
```

---

### API Root

**Endpoint:** `GET /`

**Response (200 OK):**
```json
{
  "message": "Mars Rover AI Simulator Backend",
  "version": "0.1.0",
  "documentation": "/docs",
  "endpoints": {
    "terrain": "/api/v1/terrain",
    "health": "/health"
  }
}
```

---

### API v1 Health

**Endpoint:** `GET /api/v1/health`

**Response (200 OK):**
```json
{
  "status": "operational",
  "api_version": "v1",
  "timestamp": "2026-03-23T12:30:00Z",
  "modules": {
    "terrain": "available",
    "rover": "planned",
    "simulation": "planned",
    "ai_brain": "planned"
  }
}
```

---

## Data Models

### DTMDataset
Metadata for a HiRISE Digital Terrain Model product

**Fields:**
- `product_id` (str): Unique DTM identifier (e.g., `DTE_022534_1120_021534_1120_UA00`)
- `observation_id` (str): HiRISE observation ID (e.g., `ESP_022534_1120`)
- `orbit_number` (int): MRO orbit number
- `acquisition_date` (datetime): When captured
- `release_date` (datetime): PDS release date
- `grid_spacing` (enum): Resolution - `0.25m`, `0.5m`, `1.0m`, `2.0m`
- `projection` (enum): `Equirectangular` or `Polar Stereographic`
- `bounds` (object): Geographic extent with lat/lon bounds
- `vertical_precision_cm` (float): Elevation accuracy
- `file_size_mb` (float): Data file size
- `data_url` (str): PDS download link
- `browse_url` (str, optional): Preview image
- `institution` (str): Producing institution

### ElevationPoint
Single elevation measurement

**Fields:**
- `latitude` (float): Latitude in degrees
- `longitude` (float): Longitude in degrees
- `elevation_m` (float): Elevation above Mars areoid (MOLA datum)
- `accuracy_cm` (float): Vertical accuracy

### TerrainTile
Heightmap tile for region visualization

**Fields:**
- `tile_id` (str): Unique identifier
- `bounds` (object): Tile geographic extent
- `resolution` (str): Tile resolution
- `min_elevation_m` (float): Minimum elevation in tile
- `max_elevation_m` (float): Maximum elevation
- `mean_elevation_m` (float): Mean elevation
- `data_url` (str): GeoTIFF download URL
- `format` (str): Data format (GeoTIFF, IMG, etc.)

---

## Testing

### Via Swagger UI (Recommended)
```
http://localhost:8000/docs
```
- Click any endpoint
- Click **"Try it out"**
- Enter parameters
- Click **"Execute"**

### Via cURL

**Test all endpoints:**
```bash
# Health check
curl http://localhost:8000/api/v1/terrain/health

# List datasets
curl http://localhost:8000/api/v1/terrain/datasets?limit=3

# Query elevation
curl -X POST http://localhost:8000/api/v1/terrain/elevation \
  -H "Content-Type: application/json" \
  -d '{"latitude": -75.75, "longitude": 45.0}'

# Quick elevation
curl http://localhost:8000/api/v1/terrain/elevation/-18.38/77.45

# Get tiles
curl -X POST http://localhost:8000/api/v1/terrain/tiles \
  -H "Content-Type: application/json" \
  -d '{"north_latitude": -75.5, "south_latitude": -76.0, "east_longitude": 45.2, "west_longitude": 44.8}'
```

### Via Python

```python
import requests

# Query elevation
response = requests.post(
    "http://localhost:8000/api/v1/terrain/elevation",
    json={"latitude": -75.75, "longitude": 45.0}
)
print(response.json())

# List datasets
response = requests.get("http://localhost:8000/api/v1/terrain/datasets")
datasets = response.json()
print(f"Available datasets: {datasets['total_count']}")
```

### Via JavaScript/Fetch

```javascript
// Query elevation
const response = await fetch('http://localhost:8000/api/v1/terrain/elevation', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    latitude: -75.75,
    longitude: 45.0
  })
});

const data = await response.json();
console.log(`Elevation: ${data.point.elevation_m}m`);
```

---

## Response Status Codes

| Code | Meaning | Typical Cause |
|------|---------|---------------|
| 200 | Success | Valid request, data returned |
| 400 | Bad Request | Invalid coordinates/parameters |
| 404 | Not Found | Dataset/region not covered |
| 500 | Server Error | Internal error |

---

## Configuration

### Environment Variables

Create `.env` file in `backend/` directory (see `.env.example`):

```
FASTAPI_ENV=development
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
CORS_ORIGINS=["http://localhost:3000"]
```

---

## Data Sources

### HiRISE DTM
- **Source**: University of Arizona / NASA MRO
- **URL**: https://www.uahirise.org/dtm/
- **Resolution**: 0.25m - 2.0m post spacing
- **Precision**: ~50cm vertical
- **Format**: IMG (PDS), GeoTIFF
- **Coverage**: Selected regions on Mars

### MOLA (Mars Orbiter Laser Altimeter)
- **Source**: NASA, USGS Astrogeology
- **Resolution**: ~463m global
- **Use**: Baseline for DTM registration

### CTX DEM
- **Source**: NASA MRO
- **Resolution**: ~20m
- **Coverage**: Selected regions

---

## Development

### Project Structure

```
backend/
├── main.py                   # FastAPI app entry point
├── requirements.txt
├── .env.example
├── models/
│   ├── __init__.py
│   ├── terrain_model.py      # Pydantic models
│   └── rover_model.py        # (Placeholder)
├── routes/
│   ├── __init__.py
│   ├── terrain.py            # Terrain endpoints
│   ├── rover.py              # (Placeholder)
│   └── simulation.py         # (Placeholder)
├── services/
│   ├── __init__.py
│   └── dataset_loader.py     # Dataset management
└── README.md
```

### Adding New Endpoints

1. Create function in `routes/` with `@router.get()` or `@router.post()`
2. Define request/response Pydantic models in `models/`
3. Add docstring with examples
4. Run server - Swagger auto-updates

### Adding New Data Sources

1. Create new model in `models/terrain_model.py`
2. Implement fetcher in `services/`
3. Create endpoint in `routes/`
4. Document in this README

---

## Performance Notes

- Current: Mock data (mathematical simulation)
- Sprint 2: Real DTM file loading (rasterio)
- Consider: Caching, database indexing, streaming for large tiles

---

## Future Enhancements

- [ ] Real HiRISE DTM file loading
- [ ] Database for dataset catalog
- [ ] Terrain classification (rock type, steepness)
- [ ] Obstacle detection (boulders, cliffs)
- [ ] Traversability analysis
- [ ] Authentication (API keys)
- [ ] Rate limiting
- [ ] WebSocket for real-time updates
- [ ] ML-based terrain features

---

## Dependencies

```
fastapi==0.104.1
uvicorn==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
numpy==1.24.3
rasterio==1.3.9
scipy==1.11.4
```

---

## Troubleshooting

### Port 8000 Already in Use

**Windows:**
```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Mac/Linux:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Import Errors

Ensure dependencies installed:
```bash
pip install -r requirements.txt
```

### CORS Errors

Check `CORS_ORIGINS` in `.env` and `main.py`

---

## API Documentation

- **OpenAPI Schema**: `/openapi.json`
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **Full API Docs**: See [docs/API.md](../docs/API.md)

---

## Support

- [Main README](../README.md)
- [API Documentation](../docs/API.md)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Pydantic Docs](https://docs.pydantic.dev/)

---

**Version**: 0.1.0  
**Status**: Ready for Sprint 1 ✅
