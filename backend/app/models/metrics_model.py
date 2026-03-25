from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String, ForeignKey("nodes.node_id"))

    cpu_usage = Column(Float)
    memory_usage = Column(Float)

    timestamp = Column(DateTime, default=datetime.utcnow)

    # 🔗 relationship
    node = relationship("Node", back_populates="metrics")
