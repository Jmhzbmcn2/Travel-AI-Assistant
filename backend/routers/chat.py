"""
Chat router — endpoints cho chat và streaming.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langgraph.graph.state import CompiledStateGraph

from backend.dependencies import get_graph, get_session_store
from backend.schemas.chat import ChatRequest, ChatResponse, ResumeRequest
from backend.services import chat_service
from backend.services.session_store import SessionStore

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# ── Helpers ──────────────────────────────────────────

def _resolve_session_id(session_id: str | None) -> str:
    """Trả về session_id hiện có hoặc tạo mới."""
    return session_id or str(uuid.uuid4())


async def _sse_generator(
    sid: str,
    processed: dict,
    store: SessionStore,
    *,
    include_session_event: bool = False,
) -> AsyncGenerator[str, None]:
    """SSE event generator dùng chung cho chat và resume."""
    try:
        if include_session_event:
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

        if processed["type"] == "interrupt":
            yield (
                f"data: {json.dumps({'type': 'interrupt', 'content': processed['message'], 'data': processed.get('data')}, ensure_ascii=False)}\n\n"
            )
        else:
            ai_message = processed["message"]
            store.add_message(sid, "assistant", ai_message)

            chunk_size = 12
            for i in range(0, len(ai_message), chunk_size):
                chunk = ai_message[i : i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.03)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


# ── Synchronous endpoints ────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
) -> ChatResponse:
    """Nhận tin nhắn từ user, chạy qua LangGraph, trả kết quả hoặc interrupt."""
    sid = _resolve_session_id(request.session_id)
    store.add_message(sid, "user", request.message)

    try:
        _, processed = await chat_service.invoke_graph(graph, sid, request.message)

        if processed["type"] == "done":
            store.add_message(sid, "assistant", processed["message"])

        return ChatResponse(
            response=processed["message"],
            session_id=sid,
            type=processed["type"],
            interrupt_data=processed.get("data"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resume", response_model=ChatResponse)
async def resume_chat(
    request: ResumeRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
) -> ChatResponse:
    """Resume graph sau khi user xác nhận interrupt."""
    sid = request.session_id
    store.init(sid)

    try:
        _, processed = await chat_service.resume_graph(graph, sid)

        if processed["type"] == "done":
            store.add_message(sid, "assistant", processed["message"])

        return ChatResponse(
            response=processed["message"],
            session_id=sid,
            type=processed["type"],
            interrupt_data=processed.get("data"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── SSE streaming endpoints ─────────────────────────

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
) -> StreamingResponse:
    """Stream response via Server-Sent Events. Hỗ trợ interrupt."""
    sid = _resolve_session_id(request.session_id)
    store.add_message(sid, "user", request.message)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

            _, processed = await chat_service.invoke_graph(graph, sid, request.message)

            async for event in _sse_generator(sid, processed, store):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stream/resume")
async def stream_resume(
    request: ResumeRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
) -> StreamingResponse:
    """Stream resume sau interrupt."""
    sid = request.session_id
    store.init(sid)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            _, processed = await chat_service.resume_graph(graph, sid)

            async for event in _sse_generator(sid, processed, store):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
