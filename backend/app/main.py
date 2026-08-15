from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.execute import router as execute_router

app = FastAPI(
    title="Live Python Compiler API",
    description="Executes Python code and returns a line-by-line, state-aware execution trace.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(execute_router, prefix="/api")


@app.get("/")
def root():
    return {"service": "live-python-compiler-backend", "status": "running"}
