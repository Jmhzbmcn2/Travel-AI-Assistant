"""
Sessions router — quản lý session metadata.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies import get_session_store
from backend.schemas.session import DeleteResponse, SessionDetail, SessionInfo
from backend.services.session_store import SessionStore

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.get("", response_model=list[SessionInfo])
async def list_sessions(
    store: SessionStore = Depends(get_session_store),
) -> list[SessionInfo]:
    """Liệt kê tất cả active sessions với preview."""
    return store.list_all()


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> SessionDetail:
    """Lấy full message history cho một session."""
    if not store.exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(messages=store.get_messages(session_id))


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
) -> DeleteResponse:
    """Xóa một session."""
    store.delete(session_id)
    return DeleteResponse()
