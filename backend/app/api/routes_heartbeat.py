from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.node_model import Node
from app.schemas.heartbeat_schema import HeartbeatRequest
from app.database import get_db


router = APIRouter()

STATUS_ACTIVE = "ACTIVE"


@router.post("/heartbeat")
def heartbeat(data: HeartbeatRequest, db: Session = Depends(get_db)):

    if not data.node_id:
        raise HTTPException(status_code=400, detail="Invalid node_id")

    node = db.query(Node).filter(Node.node_id == data.node_id).first()

    if not node:
        raise HTTPException(status_code=404, detail="Node not registered")

    current_time = datetime.utcnow()

    node.last_heartbeat = current_time

    # ✅ Update only if needed
    if node.status != STATUS_ACTIVE:
        node.status = STATUS_ACTIVE

    db.commit()

    print(f"[HEARTBEAT] Node: {data.node_id} at {current_time}")

    return {
        "message": "Heartbeat received",
        "timestamp": current_time
    }
