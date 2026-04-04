from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import requests
import numpy as np

from app.models.execution_metrics_model import ExecutionMetrics
from app.services.script_analyzer import extract_script_features
from app.database import get_db
from app.models.node_model import Node
from app.models.metrics_model import Metrics
from app.schemas.execution_schema import ExecutionRequest
from ml.models.model_loader import ModelLoader

router = APIRouter()
model = ModelLoader()


@router.post("/execute")
def execute(payload: ExecutionRequest, db: Session = Depends(get_db)):

    ACTIVE_THRESHOLD = 30

    # -------------------------
    # ✅ GET ACTIVE NODES
    # -------------------------
    nodes = db.query(Node).filter(
        Node.status == "ACTIVE",
        Node.last_heartbeat >= datetime.utcnow() - timedelta(seconds=ACTIVE_THRESHOLD)
    ).all()

    if not nodes:
        raise HTTPException(
            status_code=400, detail="No active nodes available")

    # -------------------------
    # 🔥 AUTO FEATURE EXTRACTION
    # -------------------------
    script_features = extract_script_features(
        payload.script_content,
        payload.language
    )

    node_scores = []

    # -------------------------
    # 🔍 EVALUATE NODES
    # -------------------------
    for node in nodes:

        metrics = (
            db.query(Metrics)
            .filter(Metrics.node_id == node.node_id)
            .order_by(Metrics.timestamp.desc())
            .limit(10)
            .all()
        )

        if len(metrics) < 10:
            print(f"[SKIP] Node {node.node_id} → Not enough metrics")
            continue

        metrics = list(reversed(metrics))

        # -------------------------
        # ✅ TIME SERIES (10 × 4)
        # -------------------------
        ts = np.array([
            [
                m.cpu_usage / 100,
                m.memory_usage / 100,
                (m.temperature if m.temperature else 50) / 100,
                (m.cpu_usage / 100) * 1.5
            ]
            for m in metrics
        ])

        # -------------------------
        # ✅ STATIC FEATURES
        # -------------------------
        static = np.array([
            node.cpu_cores / 16,
            node.total_memory / 32,
            node.cpu_frequency / 5
        ])

        # -------------------------
        # ✅ SCRIPT FEATURES
        # -------------------------
        script = np.array([
            script_features["file_size"],
            script_features["line_count"],
            script_features["imports"],
            script_features["functions"],
            script_features["classes"],
            script_features["language"]
        ])

        # -------------------------
        # ✅ ML PREDICTION
        # -------------------------
        try:
            score = model.predict(ts, static, script)
        except Exception as e:
            print(f"[ERROR] Prediction failed: {e}")
            continue

        # -------------------------
        # ✅ LOAD PENALTY
        # -------------------------
        cpu_avg = np.mean([m.cpu_usage for m in metrics]) / 100
        final_score = score + (cpu_avg * 0.05)

        print(f"[ML] Node {node.node_id} → Score: {final_score:.4f}")

        node_scores.append((node, final_score, metrics))

    if not node_scores:
        raise HTTPException(status_code=400, detail="No suitable nodes found")

    # -------------------------
    # ✅ SORT NODES
    # -------------------------
    node_scores.sort(key=lambda x: x[1])

    # -------------------------
    # 🚀 EXECUTION + FEEDBACK
    # -------------------------
    for node, score, metrics in node_scores:
        try:
            print(f"[EXEC] Trying node: {node.node_id}")

            response = requests.post(
                f"http://{node.ip_address}/node-execute",
                json={"script": payload.script_content},
                timeout=5
            )

            execution_result = response.json()

            # =========================
            # 🔥 FEEDBACK SYSTEM START
            # =========================

            cpu_values = [m.cpu_usage for m in metrics]
            mem_values = [m.memory_usage for m in metrics]
            temp_values = [
                m.temperature if m.temperature else 50 for m in metrics]

            cpu_avg = sum(cpu_values) / len(cpu_values)
            cpu_peak = max(cpu_values)

            memory_avg = sum(mem_values) / len(mem_values)
            memory_peak = max(mem_values)

            temp_avg = sum(temp_values) / len(temp_values)

            execution_time = execution_result.get("execution_time", 1)

            energy_proxy = cpu_avg * execution_time
            composite_score = 0.6 * execution_time + 0.4 * energy_proxy

            feedback = ExecutionMetrics(
                node_id=node.node_id,
                script_id=payload.script_id,
                language=payload.language,

                file_size=script_features["file_size"],
                line_count=script_features["line_count"],
                imports=script_features["imports"],
                functions=script_features["functions"],
                classes=script_features["classes"],

                cpu_cores=node.cpu_cores,
                total_memory=node.total_memory,
                cpu_frequency=node.cpu_frequency,

                cpu_avg=cpu_avg,
                cpu_peak=cpu_peak,
                memory_avg=memory_avg,
                memory_peak=memory_peak,
                temperature_avg=temp_avg,

                execution_time=execution_time,
                composite_score=composite_score
            )

            db.add(feedback)
            db.commit()

            print(f"[FEEDBACK] Stored execution for node {node.node_id}")

            # =========================
            # ✅ RETURN RESPONSE
            # =========================
            return {
                "selected_node_id": node.node_id,
                "prediction_score": score,
                "execution_result": execution_result
            }

        except Exception as e:
            print(f"[FAIL] Node {node.node_id}: {e}")
            continue

    raise HTTPException(status_code=500, detail="All nodes failed")
