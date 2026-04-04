from pydantic import BaseModel, Field
from datetime import datetime


class DeviceMetrics(BaseModel):
    node_id: str = Field(..., min_length=10)

    cpu: float = Field(..., ge=0, le=100)
    memory: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=0)

    # ✅ Node-side timestamp
    node_timestamp: datetime | None = None

    class Config:
        from_attributes = True
