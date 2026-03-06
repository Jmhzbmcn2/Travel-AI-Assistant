"""
Pydantic schemas for chat endpoints.
"""
from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""
    message: str
    session_id: str | None = None


class ResumeRequest(BaseModel):
    """Request body for resuming after an interrupt (HITL)."""
    session_id: str
    response: str | dict = "ok"


class ChatResponse(BaseModel):
    """Response body for chat endpoints."""
    response: str
    session_id: str
    type: str = "done"  # "done" | "interrupt"
    interrupt_data: dict | None = None
