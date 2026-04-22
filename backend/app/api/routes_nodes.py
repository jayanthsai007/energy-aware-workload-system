from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import numpy as np
import asyncio
from datetime import datetime
from uuid import uuid4
from app.database import SessionLocal
from app.models.node_model import Node
from app.models.metrics_model import Metrics
from app.models.execution_metrics_model import ExecutionMetrics
from app.schemas.node_schema import (
    NodeRegistrationRequest,
    NodeRegistrationResponse
)
from app.services.script_analyzer import extract_script_features
from app.api.routes_ws import get_task, get_task_results_snapshot
from ml.models.model_loader import ModelLoader

router = APIRouter()
model = ModelLoader()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/active-nodes")
def get_active_nodes(db: Session = Depends(get_db)):
    active_nodes = db.query(Node).filter(
        (Node.status == "online") | (Node.status == "ACTIVE")
    ).all()
    return active_nodes


@router.get("/nodes")
def get_nodes(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()

    return [
        {
            "node_id": n.node_id,
            "node_name": n.node_name,
            "status": n.status,
            "cpu_cores": n.cpu_cores,
            "memory": n.total_memory,
            "metrics_access": n.metrics_access,
            "network_access": n.network_access,
        }
        for n in nodes
    ]


@router.get("/nodes/{node_id}/composite-score")
def get_node_composite_score(
    node_id: str,
    task_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        return {"composite_score": None, "node_id": node_id}

    metrics = (
        db.query(Metrics)
        .filter(Metrics.node_id == node_id)
        .order_by(Metrics.timestamp.desc())
        .limit(10)
        .all()
    )

    task = asyncio.run(get_task(task_id)) if task_id else None
    if task is None and task_id:
        snapshot = asyncio.run(get_task_results_snapshot())
        task = snapshot.get(task_id)

    if task and len(metrics) >= 10 and task.get("script") and task.get("language"):
        metrics = list(reversed(metrics))
        script_features = extract_script_features(task["script"], task["language"])
        ts = np.array([
            [
                m.cpu_usage / 100,
                m.memory_usage / 100,
                (m.temperature if m.temperature else 50) / 100,
                (m.cpu_usage / 100) * 1.5
            ]
            for m in metrics
        ])
        static = np.array([
            node.cpu_cores / 16,
            node.total_memory / 32,
            node.cpu_frequency / 5
        ])
        script = np.array([
            script_features["file_size"],
            script_features["line_count"],
            script_features["imports"],
            script_features["functions"],
            script_features["classes"],
            script_features["language"]
        ])
        model_score = float(model.predict(ts, static, script))
        cpu_avg = float(np.mean([m.cpu_usage for m in metrics]) / 100)
        cpu_adjustment = cpu_avg * 0.05
        return {
            "node_id": node_id,
            "task_id": task_id,
            "composite_score": model_score + cpu_adjustment,
            "model_score": model_score,
            "cpu_adjustment": cpu_adjustment,
            "metrics_window": len(metrics),
        }

    latest_execution = (
        db.query(ExecutionMetrics)
        .filter(ExecutionMetrics.node_id == node_id)
        .order_by(ExecutionMetrics.timestamp.desc())
        .first()
    )
    if latest_execution:
        return {
            "node_id": node_id,
            "task_id": task_id,
            "composite_score": latest_execution.composite_score,
            "model_score": None,
            "cpu_adjustment": None,
            "metrics_window": len(metrics),
        }

    return {
        "node_id": node_id,
        "task_id": task_id,
        "composite_score": None,
        "model_score": None,
        "cpu_adjustment": None,
        "metrics_window": len(metrics),
    }


@router.post("/register-node", response_model=NodeRegistrationResponse)
def register_node(node_data: NodeRegistrationRequest, db: Session = Depends(get_db)):

    existing_node = db.query(Node).filter(
        Node.agent_id == node_data.agent_id
    ).first()

    if existing_node:
        # 🔄 Update node info
        existing_node.ip_address = node_data.ip_address
        existing_node.node_name = node_data.node_name
        existing_node.cpu_cores = node_data.cpu_cores
        existing_node.cpu_frequency = node_data.cpu_frequency
        existing_node.total_memory = node_data.total_memory
        existing_node.total_storage = node_data.total_storage
        existing_node.free_storage = node_data.free_storage
        existing_node.os = node_data.os
        existing_node.architecture = node_data.architecture
        existing_node.metrics_access = node_data.metrics_access
        existing_node.network_access = node_data.network_access

        # 🔥 Mark active on re-registration
        existing_node.status = "ACTIVE"
        existing_node.last_heartbeat = datetime.utcnow()

        db.commit()
        db.refresh(existing_node)

        return NodeRegistrationResponse(
            node_id=existing_node.node_id,
            agent_id=existing_node.agent_id,
            node_name=existing_node.node_name or existing_node.node_id,
            ip_address=existing_node.ip_address,
            status=existing_node.status,
            created_at=existing_node.created_at
        )

    # 🆕 New node
    new_node = Node(
        agent_id=node_data.agent_id,
        node_name=node_data.node_name,
        ip_address=node_data.ip_address,
        cpu_cores=node_data.cpu_cores,
        cpu_frequency=node_data.cpu_frequency,
        total_memory=node_data.total_memory,
        total_storage=node_data.total_storage,
        free_storage=node_data.free_storage,
        os=node_data.os,
        architecture=node_data.architecture,
        metrics_access=node_data.metrics_access,
        network_access=node_data.network_access,
        status="ACTIVE",
        last_heartbeat=datetime.utcnow()
    )

    db.add(new_node)
    db.commit()
    db.refresh(new_node)

   # return new_node
    return NodeRegistrationResponse(
        node_id=new_node.node_id,
        agent_id=new_node.agent_id,
        node_name=new_node.node_name or new_node.node_id,
        ip_address=new_node.ip_address,
        status=new_node.status,
        created_at=new_node.created_at,)
