from pydantic import BaseModel, Field


class DeviceMetrics(BaseModel):
    node_id: str   # ✅ MUST BE HERE

    cpu: float = Field(..., ge=0, le=100)
    memory: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=0)
