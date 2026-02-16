from sqlalchemy import Column, Integer, Float, DateTime
from datetime import datetime
from app.database import Base


class DeviceMetricsDB(Base):
    __tablename__ = "device_metrics"

    id = Column(Integer, primary_key=True, index=True)
    cpu = Column(Float, nullable=False)
    memory = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
