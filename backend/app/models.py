"""Request/response schemas for the execution API."""
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecuteRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute")
    input_value: str = Field(default="0", max_length=1000)
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


# ===== Authentication Models =====

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=80)
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=6, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=6, max_length=200)


class UserSummary(BaseModel):
    id: str
    name: str
    email: str
    role: str = "user"
    ai_plan: str = "free"
    ai_subscription_status: str = "active"


class AuthResponse(BaseModel):
    token: str
    refresh_token: Optional[str] = None
    user: UserSummary


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=200)
    new_password: str = Field(..., min_length=6, max_length=200)


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    email: Optional[str] = Field(None, min_length=3, max_length=200)


class UserProfileResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: str
    updated_at: str
    ai_plan: str = "free"
    ai_subscription_status: str = "active"


# ===== Code Management Models =====

class SaveCodeRequest(BaseModel):
    title: str = Field(default="Untitled script", max_length=120)
    code: str = Field(...)
    language: str = Field(default="python", max_length=40)
    is_public: bool = Field(default=False)


class SavedCodeEntry(BaseModel):
    id: str
    user_id: str
    title: str
    language: str
    code: str
    is_public: bool = False
    created_at: str
    updated_at: str


class UpdateCodeRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    code: Optional[str] = None
    is_public: Optional[bool] = None


class SharedCodeEntry(BaseModel):
    id: str
    user_id: str
    title: str
    language: str
    code: str
    is_public: bool
    permission: str  # "view" or "edit"
    shared_by: str
    created_at: str
    updated_at: str


# ===== Code Sharing/Permissions Models =====

class ShareCodeRequest(BaseModel):
    shared_with_email: str = Field(..., description="Email of user to share with")
    permission: str = Field(default="view", description="'view' or 'edit'")


class CodePermission(BaseModel):
    id: str
    code_id: str
    user_id: str
    shared_with: str
    permission: str
    created_at: str
    updated_at: str


# ===== AI Help Models =====

class AIHelpRequest(BaseModel):
    code: str = Field(...)
    question: str = Field(default="", max_length=500)


class AIHelpResponse(BaseModel):
    answer: str
    suggestions: list[str]
    generated_code: Optional[str] = None
    is_local_fallback: bool = True
