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

from travel_ai_agent.api.dependencies import get_graph, get_session_store
from travel_ai_agent.api.schemas.chat import ChatRequest, ChatResponse, ResumeRequest
from travel_ai_agent.api.services import chat_service
from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.api.services.trip_service import trip_plan_from_graph_plan
from travel_ai_agent.schemas import DecisionOutput
from travel_ai_agent.services.guardrails import request_allowed
from travel_ai_agent.api.routers.auth import get_current_user

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

NODE_STATUS_MAP = {
    "classify_intent": "Đang phân tích ý định...",
    "chitchat": "Đang chuẩn bị câu trả lời...",
    "follow_up": "Đang liên kết lịch trình...",
    "out_of_scope": "Đang kiểm tra phạm vi câu hỏi...",
    "planner": "Đang phác thảo kế hoạch chuyến đi...",
    "supervisor": "Trưởng nhóm đang phân chia công việc...",
    "flight_agent": "Trợ lý Chuyến bay đang tìm kiếm vé...",
    "hotel_agent": "Trợ lý Khách sạn đang tìm kiếm phòng...",
    "weather_agent": "Trợ lý Thời tiết đang xem dự báo...",
    "info_agent": "Trợ lý Thông tin đang tra cứu địa điểm...",
    "reflect": "Đang đánh giá và tối ưu hóa hành trình...",
    "decision": "Đang phân tích rủi ro ngân sách...",
    "respond": "Đang hoàn thiện câu trả lời..."
}


# ── Helpers ──────────────────────────────────────────

def _resolve_session_id(session_id: str | None) -> str:
    """Trả về session_id hiện có hoặc tạo mới."""
    return session_id or str(uuid.uuid4())


def _persist_processed(sid: str, processed: dict, store: SessionStore, owner_id: str) -> None:
    if processed["type"] == "interrupt":
        store.save_trip(sid, owner_id, trip_plan_from_graph_plan(processed["data"]["plan"]), "awaiting_confirmation")
    if processed.get("decision"):
        dec = DecisionOutput.model_validate(processed["decision"])
        store.save_decision(sid, owner_id, dec)
        # S6 Analytics
        if dec.decision_status == "recommended":
            store.add_usage_event(sid, owner_id, "plan_completed", "decision_engine", {"status": dec.decision_status})
        else:
            store.add_usage_event(sid, owner_id, "decision_blocked", "decision_engine", {"status": dec.decision_status})


async def _sse_generator(
    sid: str,
    processed: dict,
    store: SessionStore,
    owner_id: str,
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
            store.add_message(sid, owner_id, "assistant", ai_message)

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
    owner_id: str = Depends(get_current_user),
) -> ChatResponse:
    """Nhận tin nhắn từ user, chạy qua LangGraph, trả kết quả hoặc interrupt."""
    sid = _resolve_session_id(request.session_id)
    if store.exists(sid, owner_id) == False and request.session_id is not None:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not request_allowed(store, sid):
        raise HTTPException(status_code=429, detail="Session request budget exceeded")
    store.add_message(sid, owner_id, "user", request.message)
    store.add_usage_event(sid, owner_id, "request", "chat")

    try:
        _, processed = await chat_service.invoke_graph(graph, sid, request.message)

        _persist_processed(sid, processed, store)
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
    owner_id: str = Depends(get_current_user),
) -> ChatResponse:
    """Resume graph sau khi user xác nhận interrupt."""
    sid = request.session_id
    store.init(sid, owner_id)

    try:
        _, processed = await chat_service.resume_graph(graph, sid)
        _persist_processed(sid, processed, store, owner_id)

        if processed["type"] == "done":
            store.add_message(sid, owner_id, "assistant", processed["message"])

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
    owner_id: str = Depends(get_current_user),
) -> StreamingResponse:
    """Stream response via Server-Sent Events. Hỗ trợ interrupt."""
    sid = _resolve_session_id(request.session_id)
    if store.exists(sid, owner_id) == False and request.session_id is not None:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not request_allowed(store, sid):
        raise HTTPException(status_code=429, detail="Session request budget exceeded")
    store.add_message(sid, owner_id, "user", request.message)
    store.add_usage_event(sid, owner_id, "request", "chat_stream")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

            from travel_ai_agent.api.services.chat_service import build_graph_input, get_graph_config
            
            # Chạy astream để lấy intermediate status updates từng node
            async for chunk in graph.astream(
                build_graph_input(request.message, sid),
                get_graph_config(sid),
                stream_mode="updates"
            ):
                if isinstance(chunk, dict):
                    for node_name in chunk.keys():
                        status_text = NODE_STATUS_MAP.get(node_name)
                        if status_text:
                            yield f"data: {json.dumps({'type': 'status', 'content': status_text}, ensure_ascii=False)}\n\n"

            # Xử lý kết quả cuối cùng từ graph
            processed = await chat_service.process_graph_result(graph, sid)
            
            snapshot = await graph.aget_state(get_graph_config(sid))
            if processed["type"] == "done":
                state_values = snapshot.values or {}
                if state_values.get("messages"):
                    processed["message"] = state_values["messages"][-1].content

            _persist_processed(sid, processed, store, owner_id)
            async for event in _sse_generator(sid, processed, store, owner_id):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stream/resume")
async def stream_resume(
    request: ResumeRequest,
    store: SessionStore = Depends(get_session_store),
    graph: CompiledStateGraph = Depends(get_graph),
    owner_id: str = Depends(get_current_user),
) -> StreamingResponse:
    """Stream resume sau interrupt."""
    sid = request.session_id
    store.init(sid, owner_id)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            from travel_ai_agent.api.services.chat_service import get_graph_config

            async for chunk in graph.astream(
                None,
                get_graph_config(sid),
                stream_mode="updates"
            ):
                if isinstance(chunk, dict):
                    for node_name in chunk.keys():
                        status_text = NODE_STATUS_MAP.get(node_name)
                        if status_text:
                            yield f"data: {json.dumps({'type': 'status', 'content': status_text}, ensure_ascii=False)}\n\n"

            processed = await chat_service.process_graph_result(graph, sid)
            
            snapshot = await graph.aget_state(get_graph_config(sid))
            if processed["type"] == "done":
                state_values = snapshot.values or {}
                if state_values.get("messages"):
                    processed["message"] = state_values["messages"][-1].content

            _persist_processed(sid, processed, store, owner_id)
            async for event in _sse_generator(sid, processed, store, owner_id):
                yield event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
