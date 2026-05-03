from fastapi import APIRouter, Query
from services.aggregator import AggregatorAgent

router = APIRouter(
    tags=["Aggregator"]
)

@router.get("/aggregated-state")
def get_aggregated_state(
    latitude: float = Query(...),
    longitude: float = Query(...)
):
    aggregator = AggregatorAgent()
    return aggregator.aggregate(latitude, longitude)