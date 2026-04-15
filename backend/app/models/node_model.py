import uuid
from sqlalchemy import Column, String, DateTime, Integer, Float
from datetime import datetime
from app.database import Base
from sqlalchemy.orm import relationship


class Node(Base):
    __tablename__ = "nodes"

    # =========================
    # PRIMARY ID
    # =========================
    node_id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: str(uuid.uuid4())
    )

    # =========================
    # UNIQUE MACHINE ID
    # =========================
    agent_id = Column(String, unique=True, index=True, nullable=False)

    # =========================
    # NETWORK INFO
    # =========================
    ip_address = Column(String, nullable=True,
                        default=None)  # Optional metadata
    # NOTE: ws_connected is NOT persisted - it's runtime state tracked in connection_manager

    # =========================
    # HARDWARE INFO
    # =========================
    cpu_cores = Column(Integer, nullable=False)
    cpu_frequency = Column(Float, nullable=False)

    total_memory = Column(Float, nullable=False)

    total_storage = Column(Float)
    free_storage = Column(Float)

    os = Column(String)
    architecture = Column(String)

    # =========================
    # STATUS TRACKING
    # =========================
    status = Column(String, default="ACTIVE")
    last_heartbeat = Column(DateTime, default=datetime.utcnow)

    # =========================
    # METADATA
    # =========================
    created_at = Column(DateTime, default=datetime.utcnow)

    # =========================
    # RELATIONSHIPS
    # =========================
    metrics = relationship("Metrics", back_populates="node")
    executions = relationship("ExecutionMetrics", back_populates="node")


'''What This Does

✔ Each node gets a UUID automatically
✔ Tracks IP address
✔ Tracks online/offline status
✔ Tracks last heartbeat time

This supports 100+ dynamic devices.'''
