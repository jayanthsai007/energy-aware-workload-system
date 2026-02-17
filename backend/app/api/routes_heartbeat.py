from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models.node_model import Node
from app.models.device_metrics_model import DeviceMetricsDB
from app.schemas.heartbeat_schema import HeartbeatRequest

router = APIRouter()

HEARTBEAT_TIMEOUT_SECONDS = 15


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/heartbeat")
def heartbeat(data: HeartbeatRequest, db: Session = Depends(get_db)):
    # Check if node exists
    node = db.query(Node).filter(Node.node_id == data.node_id).first()

    if not node:
        raise HTTPException(status_code=404, detail="Node not registered")

    current_time = datetime.utcnow()

    # Update current node heartbeat
    node.last_heartbeat = current_time
    node.status = "online"

    # Insert metrics record
    metrics = DeviceMetricsDB(
        node_id=data.node_id,
        cpu=data.cpu,
        memory=data.memory,
        temperature=data.temperature
    )

    db.add(metrics)

    # ---- OFFLINE DETECTION LOGIC ----
    all_nodes = db.query(Node).all()

    for n in all_nodes:
        if current_time - n.last_heartbeat > timedelta(seconds=HEARTBEAT_TIMEOUT_SECONDS):
            n.status = "offline"
        else:
            n.status = "online"

    db.commit()

    return {"message": "Heartbeat received successfully"}
