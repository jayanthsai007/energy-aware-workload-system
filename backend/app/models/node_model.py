import uuid
from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.database import Base


class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = Column(String, nullable=False)
    status = Column(String, default="online")
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

'''What This Does

✔ Each node gets a UUID automatically
✔ Tracks IP address
✔ Tracks online/offline status
✔ Tracks last heartbeat time

This supports 100+ dynamic devices.'''