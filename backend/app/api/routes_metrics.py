from fastapi import APIRouter
from app.schemas.device_metrics_schema import DeviceMetrics

router = APIRouter()

@router.post("/metrics")
def receive_metrics(metrics: DeviceMetrics):
    return {
        "status": "Metrics received successfully",
        "received_data": metrics
    }
