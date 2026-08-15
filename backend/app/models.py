"""Request/response schemas for the execution API."""
from typing import Any, Optional
from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    timeout_seconds: float = Field(5.0, ge=0.1, le=15.0)
    max_steps: int = Field(2000, ge=1, le=20000)


class VariableChange(BaseModel):
    kind: str  # "added" | "modified" | "removed" | "unchanged"
    previous: Optional[Any] = None
    current: Optional[Any] = None
    # For sequence-like types, index-level hints for animation
    added_indices: Optional[list] = None
    removed_indices: Optional[list] = None


class ExecutionStep(BaseModel):
    step: int
    line: Optional[int]
    code: str
    event: str  # "line" | "call" | "return" | "exception"
    scope: str  # function name or "<module>"
    variables: dict
    changes: dict
    stdout_delta: str
    duration_ms: float


class ExecutionError(BaseModel):
    type: str
    message: str
    line: Optional[int]
    traceback: str


class ExecuteResponse(BaseModel):
    success: bool
    steps: list[ExecutionStep]
    final_variables: dict
    stdout: str
    error: Optional[ExecutionError] = None
    timed_out: bool = False
    truncated: bool = False
    total_duration_ms: float
    runtime_source: str
    original_source: str
