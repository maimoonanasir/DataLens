"""Pydantic models for the LLM chat interface."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the chat history."""

    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Request body for the /chat endpoint."""

    messages: list[ChatMessage]
    filters: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response from the /chat endpoint."""

    answer: str
    tool_calls_made: list[str] = Field(default_factory=list)


class SummaryRequest(BaseModel):
    """Request body for the /summary endpoint."""

    filters: dict[str, Any] = Field(default_factory=dict)


class SummaryResponse(BaseModel):
    """Response from the /summary endpoint."""

    summary: str
    generated_at: str
