from pydantic import BaseModel, Field


class ExecutionPlanRequest(BaseModel):
    file_size: float = Field(..., description="File size in KB")
    line_count: int = Field(..., description="Number of lines in script")
    language: str = Field(..., description="Programming language (python/java)")


class ExecutionPlanResponse(BaseModel):
    selected_node_id: str
    message: str
