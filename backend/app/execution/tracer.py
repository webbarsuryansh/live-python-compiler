"""Line-by-line execution tracer.

Uses sys.settrace to observe every line/call/return/exception event inside
the user's code (identified by a sentinel filename) and records a snapshot
of visible variables *after* each line finishes executing, along with the
console output produced since the previous step.

This is generic: it has no knowledge of which statement mutated what. It
just watches state before/after each line and lets `diff.py` figure out
what changed.
"""
from __future__ import annotations

import sys
import time
import linecache
from io import StringIO

from .serialize import snapshot_vars, to_safe

USER_CODE_FILENAME = "<live_python_compiler>"


class ExecutionTimeout(Exception):
    pass


class StepLimitExceeded(Exception):
    pass


class Tracer:
    def __init__(self, source_lines: list[str], timeout_seconds: float, max_steps: int):
        self.source_lines = source_lines
        self.timeout_seconds = timeout_seconds
        self.max_steps = max_steps
        self.deadline = None
        self.steps: list[dict] = []
        self._prev_vars: dict = {}
        self._pending_line = None
        self._pending_scope = None
        self._stdout = StringIO()
        self._stdout_mark = 0
        self._real_stdout = None
        self._step_start_time = None

    # ---- lifecycle -------------------------------------------------

    def start(self):
        self.deadline = time.monotonic() + self.timeout_seconds
        self._real_stdout = sys.stdout
        sys.stdout = self._stdout
        sys.settrace(self._trace)

    def stop(self):
        sys.settrace(None)
        if self._real_stdout is not None:
            sys.stdout = self._real_stdout

    @property
    def full_stdout(self) -> str:
        return self._stdout.getvalue()

    # ---- core trace callback ----------------------------------------

    def _check_limits(self):
        if time.monotonic() > self.deadline:
            raise ExecutionTimeout()
        if len(self.steps) >= self.max_steps:
            raise StepLimitExceeded()

    def _code_line(self, lineno: int) -> str:
        if 1 <= lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].rstrip("\n")
        return ""

    def _stdout_delta(self) -> str:
        full = self._stdout.getvalue()
        delta = full[self._stdout_mark:]
        self._stdout_mark = len(full)
        return delta

    def _record_pending(self, frame):
        """Flush the previously-seen line as a completed step, now that we
        know its post-execution state (the state visible at this new event).
        """
        if self._pending_line is None:
            return

        visible = dict(frame.f_globals)
        if frame.f_code.co_name != "<module>":
            visible.update(frame.f_locals)
        curr_vars = snapshot_vars(visible)

        duration_ms = (time.monotonic() - self._step_start_time) * 1000 if self._step_start_time else 0.0

        self.steps.append({
            "step": len(self.steps) + 1,
            "line": self._pending_line,
            "code": self._code_line(self._pending_line),
            "event": "line",
            "scope": self._pending_scope,
            "variables": curr_vars,
            "prev_variables": self._prev_vars,
            "stdout_delta": self._stdout_delta(),
            "duration_ms": round(duration_ms, 4),
        })
        self._prev_vars = curr_vars

    def _trace(self, frame, event, arg):
        if frame.f_code.co_filename != USER_CODE_FILENAME:
            return None

        self._check_limits()

        if event == "line":
            self._record_pending(frame)
            self._pending_line = frame.f_lineno
            self._pending_scope = frame.f_code.co_name
            self._step_start_time = time.monotonic()
            return self._trace

        if event == "call":
            # Enter a function: flush whatever line was pending in the caller.
            self._record_pending(frame)
            self._pending_line = None
            return self._trace

        if event == "return":
            self._record_pending(frame)
            if frame.f_code.co_name == "<module>":
                # Module-level code "returning" just means the script ended —
                # the final line was already flushed above; nothing new to add.
                self._pending_line = None
                return self._trace
            visible = dict(frame.f_globals)
            visible.update(frame.f_locals)
            curr_vars = snapshot_vars(visible)
            self.steps.append({
                "step": len(self.steps) + 1,
                "line": frame.f_lineno,
                "code": self._code_line(frame.f_lineno),
                "event": "return",
                "scope": frame.f_code.co_name,
                "variables": curr_vars,
                "prev_variables": self._prev_vars,
                "stdout_delta": self._stdout_delta(),
                "duration_ms": 0.0,
                "return_value": to_safe(arg) if arg is not None else None,
            })
            self._prev_vars = curr_vars
            self._pending_line = None
            return self._trace

        if event == "exception":
            self._record_pending(frame)
            self._pending_line = None
            return self._trace

        return self._trace

    def finalize(self, frame_globals: dict):
        """Flush the final pending line once the program finishes normally."""
        if self._pending_line is not None:
            curr_vars = snapshot_vars(frame_globals)
            duration_ms = (time.monotonic() - self._step_start_time) * 1000 if self._step_start_time else 0.0
            self.steps.append({
                "step": len(self.steps) + 1,
                "line": self._pending_line,
                "code": self._code_line(self._pending_line),
                "event": "line",
                "scope": self._pending_scope,
                "variables": curr_vars,
                "prev_variables": self._prev_vars,
                "stdout_delta": self._stdout_delta(),
                "duration_ms": round(duration_ms, 4),
            })
            self._prev_vars = curr_vars
            self._pending_line = None
