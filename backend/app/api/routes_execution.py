from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.node_model import Node
from app.models.device_metrics_model import DeviceMetricsDB
from app.schemas.execution_schema import (
    ExecutionPlanRequest,
    ExecutionPlanResponse
)

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/plan-execution", response_model=ExecutionPlanResponse)
def plan_execution(data: ExecutionPlanRequest, db: Session = Depends(get_db)):

    # Get all active (online) nodes
    active_nodes = db.query(Node).filter(Node.status == "online").all()

    if not active_nodes:
        raise HTTPException(status_code=404, detail="No active nodes available")

    best_node = None
    best_score = float("inf")

    for node in active_nodes:
        # Get latest metrics for this node
        latest_metrics = (
            db.query(DeviceMetricsDB)
            .filter(DeviceMetricsDB.node_id == node.node_id)
            .order_by(DeviceMetricsDB.created_at.desc())
            .first()
        )

        if not latest_metrics:
            continue

        # Simple rule-based scoring:
        # Lower CPU + lower memory = better
        score = latest_metrics.cpu + latest_metrics.memory

        if score < best_score:
            best_score = score
            best_node = node

    if not best_node:
        raise HTTPException(status_code=404, detail="No suitable node found")

    return ExecutionPlanResponse(
        selected_node_id=best_node.node_id,
        message="Node selected successfully"
    )
