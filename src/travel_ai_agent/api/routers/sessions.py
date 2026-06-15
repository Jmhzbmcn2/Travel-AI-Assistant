"""
Sessions router — quản lý session metadata.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from travel_ai_agent.api.dependencies import get_session_store
from travel_ai_agent.api.schemas.session import DeleteResponse, SessionDetail, SessionInfo, RenameRequest
from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.api.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/sessions", tags=["Sessions"])


@router.get("", response_model=list[SessionInfo])
async def list_sessions(
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> list[SessionInfo]:
    """Liệt kê tất cả active sessions với preview."""
    return store.list_all(owner_id)


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> SessionDetail:
    """Lấy full message history cho một session."""
    if not store.exists(session_id, owner_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(messages=store.get_messages(session_id, owner_id))


@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> DeleteResponse:
    """Xóa một session."""
    store.delete(session_id, owner_id)
    return DeleteResponse()


@router.patch("/{session_id}", response_model=SessionInfo)
async def rename_session(
    session_id: str,
    request: RenameRequest,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> SessionInfo:
    """Đổi tên một session."""
    if not store.exists(session_id, owner_id):
        raise HTTPException(status_code=404, detail="Session not found")
    store.rename_session(session_id, owner_id, request.title)
    all_sessions = store.list_all(owner_id)
    for s in all_sessions:
        if s.session_id == session_id:
            return s
    raise HTTPException(status_code=500, detail="Failed to retrieve updated session")


@router.get("/{session_id}/usage")
async def get_session_usage(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
):
    """Lấy tổng token usage và cost cho một session."""
    if not store.exists(session_id, owner_id):
        raise HTTPException(status_code=404, detail="Session not found")
    return store.get_usage_summary(session_id, owner_id)
