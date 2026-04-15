from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
import uuid

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"

    # =========================
    # PRIMARY KEY
    # =========================
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # =========================
    # TASK DATA
    # =========================
    script = Column(String, nullable=False)
    language = Column(String, default="python")

    # =========================
    # STATUS MANAGEMENT
    # =========================
    # pending, running, completed, failed
    status = Column(String, default="pending")
    assigned_node = Column(String, nullable=True)

    # =========================
    # RESULTS
    # =========================
    output = Column(String, nullable=True)
    error = Column(String, nullable=True)
    execution_time = Column(Integer, nullable=True)  # seconds

    # =========================
    # RETRY SYSTEM
    # =========================
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # =========================
    # TIMEOUT SYSTEM
    # =========================
    timeout = Column(Integer, default=20)  # seconds

    # =========================
    # TIMESTAMP
    # =========================
    created_at = Column(DateTime, default=datetime.utcnow)
