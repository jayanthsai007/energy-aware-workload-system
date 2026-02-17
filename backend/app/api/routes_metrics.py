from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.device_metrics_schema import DeviceMetrics
from app.database import SessionLocal
from app.models.device_metrics_model import DeviceMetricsDB
from app.services.workload_classifier import classify_workload

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/metrics")
def receive_metrics(metrics: DeviceMetrics, db: Session = Depends(get_db)):

    # Store metrics in database
    db_metrics = DeviceMetricsDB(
        cpu=metrics.cpu,
        memory=metrics.memory,
        temperature=metrics.temperature
    )

    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)

    # Classify workload
    workload = classify_workload(
        cpu=metrics.cpu,
        memory=metrics.memory,
        temperature=metrics.temperature
    )

    return {
        "status": "Metrics stored successfully",
        "id": db_metrics.id,
        "workload_classification": workload
    }
