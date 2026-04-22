from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Any
import asyncio
import json
from datetime import datetime, UTC
import hashlib

from app.database import SessionLocal
from app.models.execution_metrics_model import ExecutionMetrics
from app.models.metrics_model import Metrics
from app.models.node_model import Node
from app.services.script_analyzer import extract_script_features


router = APIRouter()

# Connected node_id -> websocket
connected_nodes: dict[str, WebSocket] = {}

# Task lifecycle store for UI polling
task_results: dict[str, dict[str, Any]] = {}

# Guard shared state touched by HTTP + WS handlers
state_lock = asyncio.Lock()


async def register_node_socket(node_id: str, websocket: WebSocket) -> None:
    async with state_lock:
        connected_nodes[node_id] = websocket


async def unregister_node_socket(node_id: str, websocket: WebSocket) -> None:
    async with state_lock:
        current = connected_nodes.get(node_id)
        if current is websocket:
            connected_nodes.pop(node_id, None)


async def get_connected_node_socket(node_id: str) -> WebSocket | None:
    async with state_lock:
        return connected_nodes.get(node_id)


async def create_task_record(task_id: str, node_id: str, language: str, script: str) -> None:
    async with state_lock:
        task_results[task_id] = {
            "task_id": task_id,
            "node_id": node_id,
            "language": language,
            "script": script,
            "created_at": datetime.now(UTC).isoformat(),
            "status": "queued",
            "output": "",
            "error": "",
        }


async def append_task_log(task_id: str, message: str) -> None:
    async with state_lock:
        task = task_results.get(task_id)
        if not task:
            return
        if task.get("status") == "queued":
            task["status"] = "running"
        existing_output = task.get("output", "")
        task["output"] = f"{existing_output}\n{message}".strip()


async def store_task_result(data: dict[str, Any]) -> None:
    task_id = data.get("task_id")
    if not task_id:
        return

    async with state_lock:
        current = task_results.get(task_id, {})
        current.update(data)
        status = data.get("status")
        if status == "success":
            current["status"] = "completed"
        elif status == "failed":
            current["status"] = "failed"
        else:
            current["status"] = status or current.get("status", "completed")
        task_results[task_id] = current

    await persist_task_result(task_id)


async def persist_task_result(task_id: str) -> None:
    task = await get_task(task_id)
    if not task:
        return

    execution_time = task.get("execution_time")
    node_id = task.get("node_id")
    language = task.get("language")
    script = task.get("script")

    if not node_id or not language or not script:
        return

    execution_time = float(execution_time or 0)
    if execution_time <= 0:
        return

    db = SessionLocal()
    try:
        existing = db.query(ExecutionMetrics).filter(
            ExecutionMetrics.task_id == task_id
        ).first()
        if existing:
            return

        node = db.query(Node).filter(Node.node_id == node_id).first()
        metrics = (
            db.query(Metrics)
            .filter(Metrics.node_id == node_id)
            .order_by(Metrics.timestamp.desc())
            .limit(10)
            .all()
        )

        script_features = extract_script_features(script, language)

        cpu_values = [m.cpu_usage for m in metrics]
        mem_values = [m.memory_usage for m in metrics]
        temp_values = [m.temperature if m.temperature else 50 for m in metrics]

        cpu_avg = sum(cpu_values) / len(cpu_values) if cpu_values else 0
        cpu_peak = max(cpu_values) if cpu_values else 0
        memory_avg = sum(mem_values) / len(mem_values) if mem_values else 0
        memory_peak = max(mem_values) if mem_values else 0
        temp_avg = sum(temp_values) / len(temp_values) if temp_values else 0
        energy_proxy = cpu_avg * execution_time
        composite_score = 0.6 * execution_time + 0.4 * energy_proxy

        db.add(ExecutionMetrics(
            node_id=node_id,
            task_id=task_id,
            script_id=hashlib.md5(script.encode()).hexdigest(),
            script_content=script,
            language=language,
            file_size=script_features["file_size"],
            line_count=script_features["line_count"],
            imports=script_features["imports"],
            functions=script_features["functions"],
            classes=script_features["classes"],
            cpu_cores=node.cpu_cores if node else 0,
            total_memory=node.total_memory if node else 0,
            cpu_frequency=node.cpu_frequency if node else 0,
            cpu_avg=cpu_avg,
            cpu_peak=cpu_peak,
            memory_avg=memory_avg,
            memory_peak=memory_peak,
            temperature_avg=temp_avg,
            execution_time=execution_time,
            composite_score=composite_score,
        ))
        db.commit()
    finally:
        db.close()


async def get_task(task_id: str) -> dict[str, Any] | None:
    async with state_lock:
        task = task_results.get(task_id)
        return dict(task) if task else None


async def get_task_results_snapshot() -> dict[str, dict[str, Any]]:
    async with state_lock:
        return {task_id: dict(task) for task_id, task in task_results.items()}


async def dispatch_task_to_node(
    node_id: str,
    task_id: str,
    script: str,
    language: str,
) -> None:
    websocket = await get_connected_node_socket(node_id)
    if websocket is None:
        raise HTTPException(
            status_code=400,
            detail=f"Node {node_id} is not connected to /ws",
        )

    await create_task_record(task_id, node_id, language, script)

    await websocket.send_text(json.dumps({
        "type": "execute",
        "task_id": task_id,
        "script": script,
        "language": language,
    }))


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    task = await get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    node_id = None

    try:
        register_message = await websocket.receive_json()
        if register_message.get("type") != "register" or not register_message.get("node_id"):
            await websocket.close(code=1008, reason="Missing register payload")
            return

        node_id = str(register_message["node_id"])
        await register_node_socket(node_id, websocket)

        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "execution_result":
                data = message.get("data", {})
                await store_task_result(data)
            elif msg_type == "execution_log":
                raw_data = message.get("data", "")
                task_id = None
                if isinstance(raw_data, str) and raw_data.startswith("[") and "]" in raw_data:
                    task_id = raw_data[1:raw_data.index("]")]
                if task_id:
                    await append_task_log(task_id, raw_data)

    except WebSocketDisconnect:
        pass
    finally:
        if node_id is not None:
            await unregister_node_socket(node_id, websocket)
