"""LLM chat endpoint.

POST /api/datasets/{dataset_id}/chat
    Accepts a message history and runs the Anthropic tool-calling loop.
    Returns the LLM answer with metadata about which tools were used.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from backend.app.database import get_engine
from backend.app.models.chat import ChatRequest, ChatResponse
from backend.app.services.profiler import profiles_from_json
from backend.app.services.llm import chat_with_data

router = APIRouter(prefix="/api/datasets", tags=["chat"])


@router.post("/{dataset_id}/chat", response_model=ChatResponse)
def chat(dataset_id: str, request: ChatRequest) -> ChatResponse:
    """Run a tool-calling LLM conversation about the dataset.

    Args:
        dataset_id: UUID of the uploaded dataset.
        request: Chat history (messages) and active filters.

    Returns:
        ChatResponse with the assistant's answer.
    """
    engine = get_engine()

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT profile_json FROM datasets WHERE id = :id"),
            {"id": dataset_id},
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    profiles = profiles_from_json(row[0])
    messages = [{"role": m.role, "content": m.content} for m in request.messages]

    try:
        answer, tools_called = chat_with_data(
            dataset_id=dataset_id,
            messages=messages,
            filters=request.filters,
            profiles=profiles,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"LLM service error: {exc}",
        )

    return ChatResponse(answer=answer, tool_calls_made=tools_called)
