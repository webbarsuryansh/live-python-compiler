from fastapi import APIRouter

from ..models import ExecuteRequest, ExecuteResponse
from ..execution.engine import run_code
from ..execution.transform import build_runtime_source

router = APIRouter()


@router.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest) -> ExecuteResponse:
    result = run_code(req.code, timeout_seconds=req.timeout_seconds, max_steps=req.max_steps)

    runtime_source = build_runtime_source(req.code, result["final_variables"])

    return ExecuteResponse(
        success=result["success"],
        steps=result["steps"],
        final_variables=result["final_variables"],
        stdout=result["stdout"],
        error=result["error"],
        timed_out=result["timed_out"],
        truncated=result["truncated"],
        total_duration_ms=result["total_duration_ms"],
        runtime_source=runtime_source,
        original_source=req.code,
    )


@router.get("/health")
def health():
    return {"status": "ok"}
