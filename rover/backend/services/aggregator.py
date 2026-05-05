import time
from routes import terrain
from models.terrain_model import ElevationQueryRequest

class AggregatorAgent:

    def aggregate(self, latitude: float, longitude: float):
        
        # 🔥 Call REAL terrain function
        elevation_request = ElevationQueryRequest(
            latitude=latitude,
            longitude=longitude
        )

        elevation_response = terrain.query_elevation(elevation_request)

        return {
            "rover": {
                "position": [latitude, longitude]
            },
            "environment": {
                "elevation": elevation_response.point.elevation_m,
                "accuracy_cm": elevation_response.point.accuracy_cm,
                "dataset_used": elevation_response.dataset_id
            },
            "timestamp": time.time()
        }