from pydantic import BaseModel, Field


# Used for ML planning only
class ExecutionPlanRequest(BaseModel):
    file_size: float = Field(..., description="File size in KB")
    line_count: int = Field(..., description="Number of lines in script")
    language: str = Field(..., description="Programming language (python/java)")


class ExecutionPlanResponse(BaseModel):
    selected_node_id: str
    message: str


# Used for full execute pipeline
class ExecutionRequest(BaseModel):
    file_size: float
    line_count: int
    language: str
    script_content: str
