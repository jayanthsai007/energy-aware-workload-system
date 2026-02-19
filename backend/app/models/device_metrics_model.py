from sqlalchemy import Column, Integer, Float, DateTime, String, ForeignKey
from datetime import datetime
from app.database import Base


class DeviceMetricsDB(Base):
    __tablename__ = "device_metrics"

    id = Column(Integer, primary_key=True, index=True)

    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)

    cpu = Column(Float, nullable=False)
    memory = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    power = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
