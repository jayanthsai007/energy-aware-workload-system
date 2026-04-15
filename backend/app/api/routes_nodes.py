from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import uuid4
from app.database import SessionLocal
from app.models.node_model import Node
from app.schemas.node_schema import (
    NodeRegistrationRequest,
    NodeRegistrationResponse
)
from app.websocket.connection_manager import manager

router = APIRouter()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/active-nodes")
async def get_active_nodes(db: Session = Depends(get_db)):
    active_nodes = db.query(Node).filter(Node.status == "ACTIVE").all()
    connected_node_ids = set(await manager.get_connected_nodes())

    return [
        {
            "node_id": n.node_id,
            "status": n.status,
            "cpu_cores": n.cpu_cores,
            "memory": n.total_memory,
            "ws_connected": n.node_id in connected_node_ids
        }
        for n in active_nodes
    ]


@router.get("/nodes")
async def get_nodes(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()
    connected_node_ids = set(await manager.get_connected_nodes())

    return [
        {
            "node_id": n.node_id,
            "status": n.status,
            "cpu_cores": n.cpu_cores,
            "memory": n.total_memory,
            "ws_connected": n.node_id in connected_node_ids
        }
        for n in nodes
    ]


@router.post("/register-node", response_model=NodeRegistrationResponse)
async def register_node(node_data: NodeRegistrationRequest, db: Session = Depends(get_db)):

    existing_node = db.query(Node).filter(
        Node.agent_id == node_data.agent_id
    ).first()

    if existing_node:
        # 🔄 Update node info
        existing_node.ip_address = node_data.ip_address or existing_node.ip_address
        existing_node.cpu_cores = node_data.cpu_cores
        existing_node.cpu_frequency = node_data.cpu_frequency
        existing_node.total_memory = node_data.total_memory
        existing_node.total_storage = node_data.total_storage
        existing_node.free_storage = node_data.free_storage
        existing_node.os = node_data.os
        existing_node.architecture = node_data.architecture

        # 🔥 Mark active on re-registration
        existing_node.status = "ACTIVE"
        existing_node.last_heartbeat = datetime.utcnow()

        db.commit()
        db.refresh(existing_node)

        return NodeRegistrationResponse(
            node_id=existing_node.node_id,
            agent_id=existing_node.agent_id,
            ip_address=existing_node.ip_address,
            status=existing_node.status,
            ws_connected=await manager.is_node_connected(existing_node.node_id),
            created_at=existing_node.created_at,
            last_heartbeat=existing_node.last_heartbeat
        )

    # 🆕 New node
    new_node = Node(
        agent_id=node_data.agent_id,
        ip_address=node_data.ip_address,
        cpu_cores=node_data.cpu_cores,
        cpu_frequency=node_data.cpu_frequency,
        total_memory=node_data.total_memory,
        total_storage=node_data.total_storage,
        free_storage=node_data.free_storage,
        os=node_data.os,
        architecture=node_data.architecture,
        status="ACTIVE",
        last_heartbeat=datetime.utcnow()
    )

    db.add(new_node)
    db.commit()
    db.refresh(new_node)

    return NodeRegistrationResponse(
        node_id=new_node.node_id,
        agent_id=new_node.agent_id,
        ip_address=new_node.ip_address,
        status=new_node.status,
        ws_connected=await manager.is_node_connected(new_node.node_id),
        created_at=new_node.created_at,
        last_heartbeat=new_node.last_heartbeat
    )
