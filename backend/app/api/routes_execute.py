from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import numpy as np

from app.database import get_db
from app.models.node_model import Node
from app.models.device_metrics_model import DeviceMetricsDB
from app.schemas.execution_schema import ExecutionRequest
from ml.models.model_loader import ModelLoader

router = APIRouter()

model = ModelLoader()


@router.post("/execute")
def execute(payload: ExecutionRequest, db: Session = Depends(get_db)):

    # Step 1 — Get online nodes
    nodes = db.query(Node).filter(Node.status == "online").all()

    if not nodes:
        raise HTTPException(status_code=400, detail="No active nodes available")

    best_node = None
    best_score = float("inf")

    for node in nodes:

        metrics = (
            db.query(DeviceMetricsDB)
            .filter(DeviceMetricsDB.node_id == node.node_id)
            .order_by(DeviceMetricsDB.created_at.desc())
            .limit(1)  # using 1 for now
            .all()
        )

        if len(metrics) < 1:
            continue

        # Prepare time-series (dummy expand to 10 steps)
        ts = np.array([[metrics[0].cpu,
                        metrics[0].memory,
                        metrics[0].temperature,
                        0.5]] * 10)

        static = np.array([
            node.cpu_cores,
            node.total_memory,
            node.base_frequency
        ])

        script = np.array([
            payload.file_size,
            payload.line_count,
            1 if payload.language == "python" else 0,
            0, 0, 0
        ])

        score = model.predict(ts, static, script)

        if score < best_score:
            best_score = score
            best_node = node

    if not best_node:
        raise HTTPException(status_code=400, detail="No suitable node found")

    # Step 2 — Send script to node-execute
    try:
        response = requests.post(
            "http://127.0.0.1:8000/node-execute",
            json={"script": payload.script_content}
        )

        execution_result = response.json()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "selected_node_id": best_node.node_id,
        "prediction_score": best_score,
        "execution_result": execution_result
    }
