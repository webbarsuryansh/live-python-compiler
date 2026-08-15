# Production execution sandbox (placeholder).
#
# In development, backend/app/execution/engine.py runs user code in-process
# with exec(). That is NOT safe for untrusted input in production.
#
# This Dockerfile is where the real sandbox goes: a minimal, network-disabled
# container that receives {code, timeout_seconds, max_steps} on stdin (or via
# a tiny internal HTTP server bound to localhost only), runs engine.run_code()
# inside itself, and returns the JSON result on stdout — with the *host*
# FastAPI process launching this container per-request (or per short-lived
# pool of pre-warmed containers) instead of calling run_code() directly.
#
# Recommended hardening when you wire this up:
#   docker run \
#     --rm \
#     --network none \
#     --memory 128m --memory-swap 128m \
#     --cpus 0.5 \
#     --pids-limit 64 \
#     --read-only \
#     --tmpfs /tmp:size=16m \
#     --user 1000:1000 \
#     --cap-drop ALL \
#     --security-opt no-new-privileges \
#     live-python-compiler-executor

FROM python:3.11-slim

RUN useradd -m -u 1000 sandbox
WORKDIR /sandbox

COPY ./runner.py /sandbox/runner.py
COPY ../../backend/app/execution /sandbox/execution

USER sandbox

ENTRYPOINT ["python3", "/sandbox/runner.py"]
