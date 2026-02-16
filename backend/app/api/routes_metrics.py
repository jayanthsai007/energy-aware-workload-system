from fastapi import APIRouter

router = APIRouter()

@router.post("/metrics")
def receive_metrics(data: dict):
    return {
        "status": "Metrics received successfully",
        "received_data": data
    }
