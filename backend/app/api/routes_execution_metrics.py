from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.execution_metrics_model import ExecutionMetrics

router = APIRouter()


@router.get("/execution-metrics")
def get_execution_metrics(db: Session = Depends(get_db)):

    rows = db.query(ExecutionMetrics).order_by(
        ExecutionMetrics.timestamp.desc()
    ).limit(50).all()

    return [
        {
            "node_id": r.node_id,
            "task_id": r.task_id,
            "script_id": r.script_id,
            "script": r.script_content,
            "language": r.language,
            "execution_time": r.execution_time,
            "cpu_avg": r.cpu_avg,
            "memory_avg": r.memory_avg,
            "cpu_peak": r.cpu_peak,
            "memory_peak": r.memory_peak,
            "composite_score": r.composite_score,
            "timestamp": r.timestamp
        }
        for r in rows
    ]
