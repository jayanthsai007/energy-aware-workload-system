from pydantic import BaseModel, Field
from datetime import datetime


class NodeRegistrationRequest(BaseModel):
    ip_address: str = Field(..., description="IP address of the node")
    cpu_cores: int = Field(..., description="Number of CPU cores")
    total_memory: float = Field(..., description="Total memory in GB")
    base_frequency: float = Field(..., description="Base CPU frequency in GHz")


class NodeRegistrationResponse(BaseModel):
    node_id: str
    ip_address: str
    status: str
    created_at: datetime
