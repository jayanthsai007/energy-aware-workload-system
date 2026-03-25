from sqlalchemy import Column, String, Float, Integer, DateTime
from datetime import datetime
from uuid import uuid4
from app.database import Base


class Workload(Base):
    __tablename__ = "workloads"

    workload_id = Column(String, primary_key=True,
                         default=lambda: str(uuid4()))
    file_size = Column(Float)
    line_count = Column(Integer)
    language = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
