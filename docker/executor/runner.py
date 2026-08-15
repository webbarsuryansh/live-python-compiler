"""Entrypoint for the isolated executor container.

Reads a JSON payload {"code": str, "timeout_seconds": float, "max_steps": int}
from stdin, runs it through the same execution engine used in dev, and writes
the JSON result to stdout. The host FastAPI process should invoke this via
`docker run --rm --network none ... < payload.json` (or over a tiny internal
socket) instead of importing/calling the engine in-process, once this
container is wired up as the real production sandbox.
"""
import json
import sys

from execution.engine import run_code


def main():
    payload = json.loads(sys.stdin.read())
    result = run_code(
        payload["code"],
        timeout_seconds=payload.get("timeout_seconds", 5.0),
        max_steps=payload.get("max_steps", 2000),
    )
    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
