from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import datetime
from typing import Optional, Literal
import re


class NodeRegistrationRequest(BaseModel):
    """Node registration: IP is optional metadata only. WebSocket is the real connection."""
    agent_id: str = Field(..., min_length=10, max_length=128,
                          description="Unique machine identifier")

    ip_address: Optional[str] = Field(
        None, description="Optional: IP address metadata only")

    cpu_cores: int = Field(..., gt=0, le=256)
    total_memory: float = Field(..., gt=0, le=1024)
    cpu_frequency: float = Field(..., gt=0)

    os: Optional[str] = None
    architecture: Optional[str] = None

    total_storage: Optional[float] = Field(None, gt=0, le=10000)
    free_storage: Optional[float] = Field(None, ge=0)

    @field_validator("ip_address")
    def validate_ip(cls, v):
        """Soft validation: if provided, must be valid IP format (no PORT required)"""
        if v is None:
            return v

        # Accept IP with or without port
        ip_part = v.split(":")[0] if ":" in v else v

        # Validate IP octets
        try:
            parts = ip_part.split(".")
            if len(parts) != 4:
                raise ValueError()
            if any(int(p) > 255 or int(p) < 0 for p in parts):
                raise ValueError()
        except:
            raise ValueError(f"Invalid IP format: {v}")

        return v

    @field_validator("free_storage")
    def validate_storage(cls, v, info: ValidationInfo):
        total = info.data.get("total_storage")
        if total is not None and v is not None and v > total:
            raise ValueError("free_storage cannot exceed total_storage")
        return v


class NodeRegistrationResponse(BaseModel):
    """Registration response: returns system identity + connection status"""
    node_id: str = Field(..., description="System identity")
    agent_id: str = Field(..., description="Unique machine identifier")
    ip_address: Optional[str] = Field(
        None, description="Metadata: optional IP")
    status: Literal["ACTIVE",
                    "OFFLINE"] = Field(..., description="Registration status")
    ws_connected: bool = Field(
        False, description="WebSocket connection status")
    created_at: datetime
    last_heartbeat: Optional[datetime] = None
