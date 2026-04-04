from pydantic import BaseModel, Field


class HeartbeatRequest(BaseModel):
    node_id: str = Field(
        ...,
        min_length=10,
        max_length=64,
    )
    cpu: float | None = None
    memory: float | None = None
    temperature: float | None = None
