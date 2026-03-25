from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.schemas.device_metrics_schema import DeviceMetrics
from app.database import SessionLocal
from app.services.workload_classifier import classify_workload
from app.models.node_model import Node
from app.models.metrics_model import Metrics

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

    print(DeviceMetrics.model_fields)


@router.post("/metrics")
def receive_metrics(metrics: DeviceMetrics, db: Session = Depends(get_db)):

    # ✅ 1. Check if node exists
    node = db.query(Node).filter(Node.node_id == metrics.node_id).first()

    if not node:
        return {"error": "Node not found"}

    # ✅ 2. Store metrics
    db_metrics = Metrics(
        node_id=metrics.node_id,
        cpu_usage=metrics.cpu,
        memory_usage=metrics.memory
    )

    db.add(db_metrics)

    # ✅ 3. Update heartbeat
    node.last_heartbeat = datetime.utcnow()

    db.commit()
    db.refresh(db_metrics)

    # ✅ 4. Classify workload
    workload = classify_workload(
        cpu=metrics.cpu,
        memory=metrics.memory,
        temperature=metrics.temperature
    )

    return {
        "status": "Metrics stored successfully",
        "metric_id": db_metrics.id,
        "node_id": metrics.node_id,
        "workload_classification": workload
    }
