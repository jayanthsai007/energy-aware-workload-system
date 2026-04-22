from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
import asyncio

from app.database import get_db
from app.models.metrics_model import Metrics
from app.models.node_model import Node
from app.api.routes_ws import get_task_results_snapshot


router = APIRouter()


@router.get("/node-inputs")
def get_node_inputs():
    task_snapshot = asyncio.run(get_task_results_snapshot())
    latest_by_node = {}

    for task in sorted(
        task_snapshot.values(),
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    ):
        node_id = task.get("node_id")
        if node_id and node_id not in latest_by_node:
            latest_by_node[node_id] = {
                "task_id": task.get("task_id"),
                "language": task.get("language"),
                "script": task.get("script"),
                "status": task.get("status"),
                "created_at": task.get("created_at"),
            }

    return latest_by_node


@router.get("/background-activity")
def get_background_activity(db: Session = Depends(get_db)):
    task_snapshot = asyncio.run(get_task_results_snapshot())
    tasks = list(task_snapshot.values())
    queued_count = sum(1 for task in tasks if task.get("status") == "queued")
    running_tasks = [
        task for task in tasks if str(task.get("status", "")).lower() == "running"
    ]
    recent_tasks = sorted(
        tasks,
        key=lambda item: item.get("created_at") or "",
        reverse=True,
    )

    if running_tasks:
        current = running_tasks[0]
        return {
            "message": f"Node {current.get('node_id')} is executing a task",
            "details": f"Task {current.get('task_id')} is currently running",
            "level": "info",
            "queue_size": queued_count,
        }

    if recent_tasks:
        latest = recent_tasks[0]
        return {
            "message": f"Latest task status: {latest.get('status', 'unknown')}",
            "details": f"Task {latest.get('task_id')} on node {latest.get('node_id')}",
            "level": "info" if latest.get("status") == "completed" else "warning",
            "queue_size": queued_count,
        }

    threshold = datetime.utcnow() - timedelta(seconds=30)
    active_nodes = db.query(Node).filter(
        or_(Node.status == "ACTIVE", Node.status == "online"),
        Node.last_heartbeat >= threshold,
    ).count()
    latest_metric = db.query(Metrics).order_by(Metrics.timestamp.desc()).first()

    if latest_metric:
        return {
            "message": "Metrics stream active",
            "details": f"Latest metric from node {latest_metric.node_id}",
            "level": "info",
            "queue_size": queued_count,
            "active_nodes": active_nodes,
        }

    return {
        "message": "Waiting for backend activity",
        "details": "No recent tasks or metrics yet",
        "level": "warning",
        "queue_size": queued_count,
        "active_nodes": active_nodes,
    }
