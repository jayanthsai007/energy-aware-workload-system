from pydantic import BaseModel, Field

class DeviceMetrics(BaseModel):
    cpu: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    temperature: float = Field(..., ge=0, description="Device temperature in Celsius")
