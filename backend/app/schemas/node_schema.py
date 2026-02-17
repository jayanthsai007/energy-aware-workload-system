from pydantic import BaseModel, Field
from datetime import datetime


class NodeRegistrationRequest(BaseModel):
    ip_address: str = Field(..., description="IP address of the node")


class NodeRegistrationResponse(BaseModel):
    node_id: str
    ip_address: str
    status: str
    created_at: datetime
