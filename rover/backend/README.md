# Mars Rover AI Simulator - Backend API

FastAPI backend for Mars terrain and wind data used by the simulator.

## Quick Start

1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

2. Start server

```bash
python main.py
```

3. Open API docs

- http://localhost:8000/docs
- http://localhost:8000/redoc

## API Base URL

`http://localhost:8000/api/v1`

## Terrain Endpoints

- `GET /terrain/datasets`
- `GET /terrain/datasets/{dataset_id}`
- `POST /terrain/elevation`
- `GET /terrain/elevation/{latitude}/{longitude}`
- `POST /terrain/tiles`
- `GET /terrain/health`

Example terrain elevation request:

```json
{
  "latitude": -75.75,
  "longitude": 45.0,
  "dataset_id": null
}
```

## Wind Endpoints

- `GET /wind/datasets` - list wind sources (MEDA, InSight/TWINS, future MCD)
- `POST /wind/query` - query wind by location + `sol` or `timestamp_utc`
- `GET /wind/health` - wind service health

Example wind query request (sol-based):

```json
{
  "latitude": 18.4447,
  "longitude": 77.4508,
  "sol": 850,
  "timestamp_utc": null,
  "dataset_id": null
}
```

Example wind query request (timestamp-based):

```json
{
  "latitude": 4.502,
  "longitude": 135.623,
  "sol": null,
  "timestamp_utc": "2022-08-01T12:00:00Z",
  "dataset_id": "INSIGHT_TWINS_ELYSIUM_V1"
}
```

Wind query response includes:

- `wind_speed_mps`
- `wind_direction_deg` (if available)
- `source`
- `dataset_id`
- `time_reference_type`
- metadata and quality flags

Validation rules:

- `latitude` in [-90, 90]
- `longitude` in [-180, 180]
- at least one of `sol` or `timestamp_utc`

## Root Endpoints

- `GET /`
- `GET /health`
- `GET /api/v1/health`

## Project Structure

```text
backend/
├── main.py
├── requirements.txt
├── .env.example
├── models/
│   ├── terrain_model.py
│   ├── wind_model.py
│   └── rover_model.py
├── routes/
│   ├── terrain.py
│   ├── wind.py
│   ├── rover.py
│   └── simulation.py
├── services/
│   ├── dataset_loader.py
│   ├── wind_loader.py
│   └── wind_service.py
└── README.md
```

## Notes

- Terrain and wind currently use mock-ready dataset adapters.
- The wind layer is structured for future real MEDA / InSight / MCD ingestion.
