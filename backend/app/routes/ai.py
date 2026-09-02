from __future__ import annotations

import re
import os

from fastapi import APIRouter, HTTPException
from google import genai

from ..models import AIHelpRequest, AIHelpResponse

router = APIRouter()


@router.post("/ai-help", response_model=AIHelpResponse)
def ai_help(payload: AIHelpRequest):
    code = (payload.code or "").strip()
    question = (payload.question or "").strip()

    if not code and not question:
        raise HTTPException(status_code=400, detail="Enter a prompt or provide code for AI help.")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise HTTPException(status_code=503, detail="Gemini is not configured. Add GEMINI_API_KEY to backend/.env and restart the server.")

    configured_model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()
    if configured_model in {"gemini-2.0-flash", "models/gemini-2.0-flash"}:
        configured_model = "gemini-3.6-flash"

    prompt = (
        "You are the AI assistant inside a Python compiler. Answer the user's question directly. "
        "If they ask to write, create, or fix a program, include a complete runnable Python program "
        "inside one ```python code fence. Do not invent missing requirements.\n\n"
        f"User question: {question or 'Explain and improve this Python code.'}\n\n"
        f"Current Python code:\n{code or '(none - generate from the question)'}"
    )
    try:
        client = genai.Client(api_key=gemini_key)
        interaction = client.interactions.create(model=configured_model, input=prompt)
        answer = interaction.output_text.strip()
        code_match = re.search(r"```(?:python|py)?\s*\n?(.*?)```", answer, re.IGNORECASE | re.DOTALL)
        generated_code = code_match.group(1).strip() if code_match else None
        return AIHelpResponse(
            answer=answer,
            suggestions=[],
            generated_code=generated_code,
            is_local_fallback=False,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Gemini request failed: {exc}") from exc
