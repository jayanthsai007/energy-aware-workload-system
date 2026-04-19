from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.node_model import Node
from app.models.task_model import Task
from app.schemas.execution_schema import (
    ExecutionPlanRequest,
    ExecutionPlanResponse,
    TaskStatusResponse
)

# 🔥 ML imports
from app.services.feature_builder import build_features


router = APIRouter()

# 🔥 Lazy-loaded model
_model = None


def get_model():
    global _model
    if _model is None:
        from ml.models.model_loader import ModelLoader
        _model = ModelLoader()
    return _model


# ---------------------------
# DB Dependency
# ---------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------
# 🔥 ML-based Node Selection
# ---------------------------
def select_best_node(db: Session, script: dict):

    nodes = db.query(Node).filter(Node.status == "ACTIVE").all()

    if not nodes:
        return None, None

    best_node = None
    best_score = float("inf")

    for node in nodes:

        # Build ML features
        features = build_features(db, node, script)

        if features is None:
            print(f"[SKIP] Node {node.node_id} → Not enough data")
            continue

        ts, static, script_f = features

        try:
            model = get_model()
            score = model.predict(ts, static, script_f)
        except Exception as e:
            print(f"[ERROR] Prediction failed for {node.node_id}: {e}")
            continue

        print(f"[ML] Node {node.node_id} → Score: {score:.4f}")

        if score < best_score:
            best_score = score
            best_node = node

    return best_node, best_score


# ---------------------------
# 🔥 Execution Planning API
# ---------------------------
@router.post("/plan-execution", response_model=ExecutionPlanResponse)
def plan_execution(data: ExecutionPlanRequest, db: Session = Depends(get_db)):

    # Convert request → script features
    script = {
        "file_size": data.file_size,
        "line_count": data.line_count,
        "imports": data.imports,
        "functions": data.functions,
        "classes": data.classes,
        "language": data.language
    }

    # 🔥 Use ML scheduler
    best_node, best_score = select_best_node(db, script)

    if not best_node:
        raise HTTPException(status_code=404, detail="No suitable node found")

    return ExecutionPlanResponse(
        selected_node_id=best_node.node_id,
        message=f"Selected using ML (score={best_score:.4f})"
    )


# ---------------------------
# 🔥 Task Status API
# ---------------------------
@router.get("/task/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str, db: Session = Depends(get_db)):

    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusResponse(
        task_id=task.id,
        status=task.status,
        assigned_node=task.assigned_node,
        output=task.output,
        error=task.error,
        execution_time=task.execution_time,
        created_at=task.created_at
    )
