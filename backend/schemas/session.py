"""
Pydantic schemas for session endpoints.
"""
from pydantic import BaseModel


class SessionInfo(BaseModel):
    """Summary info for a single session (used in list)."""
    session_id: str
    title: str
    message_count: int


class SessionMessage(BaseModel):
    """A single message within a session."""
    role: str
    content: str


class SessionDetail(BaseModel):
    """Full message history for a session."""
    messages: list[SessionMessage] = []


class DeleteResponse(BaseModel):
    """Response after deleting a session."""
    status: str = "deleted"
