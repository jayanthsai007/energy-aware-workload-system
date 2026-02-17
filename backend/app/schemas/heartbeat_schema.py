from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    node_id: str = Field(..., description="UUID of the registered node")
    cpu: float = Field(..., ge=0, le=100)
    memory: float = Field(..., ge=0, le=100)
    temperature: float = Field(..., ge=0)       #Other Feilds To be added
