from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models.node_model import Node
from app.schemas.node_schema import (
    NodeRegistrationRequest,
    NodeRegistrationResponse
)

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register-node", response_model=NodeRegistrationResponse)
def register_node(
    node_data: NodeRegistrationRequest,
    db: Session = Depends(get_db)
):
    # Create new node entry (UUID auto-generated)
    new_node = Node(
        ip_address=node_data.ip_address,
        status="online",
        last_heartbeat=datetime.utcnow()
    )

    db.add(new_node)
    db.commit()
    db.refresh(new_node)

    return new_node
