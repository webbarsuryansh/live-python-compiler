"""Orchestrates compiling + running user code under the Tracer and turning
the raw trace into the API's step/diff/error response shape.

NOTE ON SECURITY: this module executes Python in-process using CPython's
built-in `exec`. That is acceptable for local development only. Before any
production deployment, this module must be swapped for a call into the
isolated sandbox described in `docker/executor/` (separate container, no
network, capped CPU/memory, non-root, filesystem isolated) — see README.
"""
from __future__ import annotations

import builtins
import time
import traceback

from .tracer import Tracer, ExecutionTimeout, StepLimitExceeded, USER_CODE_FILENAME
from .diff import diff_variables
from .serialize import snapshot_vars

# A conservative builtins allowlist for the dev sandbox. Even though this is
# not a security boundary by itself, it removes the most obviously dangerous
# names so accidental misuse (not malicious abuse) fails fast.
_BLOCKED_BUILTINS = {"open", "exec", "eval", "compile", "__import__", "input"}


def _make_safe_builtins():
    safe = {}
    for name in dir(builtins):
        if name in _BLOCKED_BUILTINS:
            continue
        safe[name] = getattr(builtins, name)
    return safe


def _friendly_error(exc: BaseException, source_lines: list[str]):
    tb = exc.__traceback__
    line = None
    # Walk to the deepest frame that belongs to the user's code.
    frame_tb = tb
    while frame_tb is not None:
        if frame_tb.tb_frame.f_code.co_filename == USER_CODE_FILENAME:
            line = frame_tb.tb_lineno
        frame_tb = frame_tb.tb_next

    return {
        "type": type(exc).__name__,
        "message": str(exc),
        "line": line,
        "traceback": "".join(traceback.format_exception(type(exc), exc, tb)),
    }


def run_code(code: str, timeout_seconds: float = 5.0, max_steps: int = 2000) -> dict:
    start = time.monotonic()
    source_lines = code.splitlines()

    try:
        compiled = compile(code, USER_CODE_FILENAME, "exec")
    except SyntaxError as e:
        return {
            "success": False,
            "steps": [],
            "final_variables": {},
            "stdout": "",
            "error": {
                "type": "SyntaxError",
                "message": str(e),
                "line": e.lineno,
                "traceback": "".join(traceback.format_exception_only(type(e), e)),
            },
            "timed_out": False,
            "truncated": False,
            "total_duration_ms": round((time.monotonic() - start) * 1000, 3),
        }

    tracer = Tracer(source_lines, timeout_seconds=timeout_seconds, max_steps=max_steps)
    exec_globals = {"__name__": "__main__", "__builtins__": _make_safe_builtins()}

    error = None
    timed_out = False
    truncated = False

    tracer.start()
    try:
        exec(compiled, exec_globals)
        tracer.finalize(exec_globals)
    except ExecutionTimeout:
        timed_out = True
        error = {
            "type": "TimeoutError",
            "message": f"Execution exceeded {timeout_seconds}s and was stopped.",
            "line": tracer._pending_line,
            "traceback": "",
        }
    except StepLimitExceeded:
        truncated = True
        error = {
            "type": "StepLimitExceeded",
            "message": f"Execution produced more than {max_steps} steps and was stopped "
                       f"(likely an infinite loop). Increase max_steps or fix the loop.",
            "line": tracer._pending_line,
            "traceback": "",
        }
    except BaseException as e:  # noqa: BLE001 - we intentionally surface all user errors
        error = _friendly_error(e, source_lines)
    finally:
        tracer.stop()

    # Build final step list with diffs against the previous step.
    steps_out = []
    prev_vars: dict = {}
    for raw in tracer.steps:
        curr_vars = raw["variables"]
        changes = diff_variables(prev_vars, curr_vars)
        steps_out.append({
            "step": raw["step"],
            "line": raw["line"],
            "code": raw["code"],
            "event": raw["event"],
            "scope": raw["scope"],
            "variables": curr_vars,
            "changes": changes,
            "stdout_delta": raw["stdout_delta"],
            "duration_ms": raw["duration_ms"],
        })
        prev_vars = curr_vars

    final_vars = steps_out[-1]["variables"] if steps_out else {}

    return {
        "success": error is None,
        "steps": steps_out,
        "final_variables": final_vars,
        "stdout": tracer.full_stdout,
        "error": error,
        "timed_out": timed_out,
        "truncated": truncated,
        "total_duration_ms": round((time.monotonic() - start) * 1000, 3),
    }
