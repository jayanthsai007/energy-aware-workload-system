import uuid
from sqlalchemy import Column, String, DateTime, Integer, Float
from datetime import datetime
from app.database import Base


class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String, primary_key=True, index=True)
    ip_address = Column(String, nullable=False)

    cpu_cores = Column(Integer, nullable=False)
    total_memory = Column(Float, nullable=False)
    base_frequency = Column(Float, nullable=False)

    status = Column(String, default="offline")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)


'''What This Does

✔ Each node gets a UUID automatically
✔ Tracks IP address
✔ Tracks online/offline status
✔ Tracks last heartbeat time

This supports 100+ dynamic devices.'''