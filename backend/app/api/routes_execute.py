from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.execution_schema import ExecutionRequest

# 🔥 TASK SYSTEM
from app.services.task_queue import add_task
from app.models.task_model import Task
import time
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/execute")
def execute(payload: ExecutionRequest, db: Session = Depends(get_db)):

    # =========================
    # 🧠 CREATE TASK
    # =========================
    task_id = payload.task_id or str(uuid.uuid4())

    task = Task(
        id=task_id,
        script=payload.script_content,
        language=payload.language,
        status="pending",
        retry_count=0,
        max_retries=3,
        timeout=20,
        created_at=datetime.utcnow()
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    # =========================
    # 🔥 ADD TO QUEUE
    # =========================
    add_task(task)

    print(f"[TASK] Created → {task.id}")

    # =========================
    # ✅ RESPONSE
    # =========================
    return {
        "message": "Task added to queue",
        "task_id": task.id,
        "status": "pending"
    }
