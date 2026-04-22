from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict
from datetime import datetime


# =========================
# ML PLANNING
# =========================
class ExecutionPlanRequest(BaseModel):
    file_size: float = Field(
        ..., gt=0, description="File size in KB"
    )
    line_count: int = Field(
        ..., gt=0, description="Number of lines in script"
    )
    language: Literal["python", "java"]

    # 🔥 ML + tracking
    script_id: Optional[str] = None
    request_id: Optional[str] = None

    # 🔥 request time (not metrics time)
    request_timestamp: Optional[datetime] = None


class ExecutionPlanResponse(BaseModel):
    selected_node_id: str

    # 🔥 ML output (lower = better)
    prediction_score: float = Field(
        ..., description="Lower is better (predicted execution cost)"
    )

    # 🔥 Explainability (optional)
    candidate_nodes: Optional[List[Dict]] = None


# =========================
# FULL EXECUTION
# =========================
class ExecutionRequest(BaseModel):

    # 🔥 Only required inputs
    script_content: str = Field(..., max_length=10000)
    language: Literal["python", "java"]

    # 🔹 Optional tracking (keep if needed)
    script_id: Optional[str] = None
    task_id: Optional[str] = None
    request_id: Optional[str] = None
    request_timestamp: Optional[datetime] = None


# =========================
# RESPONSE (OPTIONAL BUT USEFUL)
# =========================
class ExecutionResponse(BaseModel):
    selected_node_id: str
    prediction_score: float

    status: str
    output: str
    error: str
    execution_time: float
