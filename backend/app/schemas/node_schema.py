from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class NodeRegistrationRequest(BaseModel):
    # 🔥 Identity
    agent_id: str = Field(
        ..., min_length=10, max_length=128,
        description="Unique agent identifier"
    )
    node_name: str = Field(
        ..., min_length=2, max_length=64,
        description="Human-readable device name shown in the admin dashboard"
    )

    # 🌐 Network
    ip_address: str = Field(
        ...,
        pattern=r"^(?:\d{1,3}\.){3}\d{1,3}:\d{2,5}$",
        description="IP:PORT of node"
    )

    # 🖥 Hardware
    cpu_cores: int = Field(..., gt=0, le=256)
    total_memory: float = Field(..., gt=0, le=1024, description="GB")
    cpu_frequency: float = Field(..., gt=0, description="GHz")

    # 💾 Optional system info
    os: Optional[str] = None
    architecture: Optional[str] = None
    total_storage: Optional[float] = None
    free_storage: Optional[float] = None
    metrics_access: bool = False
    network_access: bool = True


class NodeRegistrationResponse(BaseModel):
    node_id: str
    agent_id: str
    node_name: str
    ip_address: str
    status: str
    created_at: datetime
