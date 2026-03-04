import os
import uuid
import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.graphs.main_graph import travel_agent


app = FastAPI(title="AI Travel Deal Hunter")

# CORS — đọc từ env CORS_ORIGINS (phân cách bằng dấu phẩy), mặc định localhost cho dev
_default_origins = ["http://localhost:5173", "http://localhost:3000"]
_env_origins = os.getenv("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in _env_origins.split(",") if o.strip()] if _env_origins else _default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Session metadata store ────────────────────────────
# Checkpointer (MemorySaver) quản lý state graph.
# sessions chỉ lưu metadata nhẹ (messages cho UI display).
sessions: dict[str, dict] = {}


def _init_session(sid: str):
    """Khởi tạo session metadata mới nếu chưa tồn tại."""
    if sid not in sessions:
        sessions[sid] = {"messages": []}


def _graph_config(sid: str) -> dict:
    """Tạo config cho graph invocation với thread_id."""
    return {"configurable": {"thread_id": sid}}


def _build_graph_input(sid: str, message: str) -> dict:
    """Xây dựng input cho LangGraph."""
    from langchain_core.messages import HumanMessage
    return {"messages": [HumanMessage(content=message)]}


def _process_graph_result(result, sid: str) -> dict:
    """Xử lý kết quả từ graph: normal completion hoặc interrupt."""
    snapshot = travel_agent.get_state(_graph_config(sid))

    if snapshot.next:
        # Graph bị interrupt_before — đọc plan từ state
        state_values = snapshot.values or {}
        plan = state_values.get("plan", {})

        # Tạo message confirm từ plan data
        message = _build_plan_message(plan)

        return {
            "type": "interrupt",
            "data": {"plan": plan, "type": "plan_confirmation"},
            "message": message,
            "waiting_for": list(snapshot.next),
        }

    # Normal completion
    ai_message = ""
    if result and isinstance(result, dict) and result.get("messages"):
        ai_message = result["messages"][-1].content

    return {
        "type": "done",
        "message": ai_message,
    }


STEP_LABELS = {
    "find_flights": "✈️ Tìm vé máy bay",
    "find_hotels": "🏨 Tìm khách sạn",
    "check_weather": "🌤️ Tra cứu thời tiết",
    "search_info": "🔍 Tìm kiếm thông tin du lịch",
}


def _build_plan_message(plan: dict) -> str:
    """Tạo message confirm đẹp từ plan data."""
    if not plan:
        return "Xác nhận kế hoạch?"

    constraints = plan.get("constraints", {})
    steps = plan.get("steps", [])
    goal = plan.get("goal", "")

    parts = [f"📋 **Kế hoạch:** {goal}\n"]

    if constraints.get("destination_name") or constraints.get("destination"):
        parts.append(f"📍 Điểm đến: {constraints.get('destination_name', constraints.get('destination', ''))}")
    if constraints.get("origin_name") or constraints.get("origin"):
        parts.append(f"🛫 Điểm đi: {constraints.get('origin_name', constraints.get('origin', ''))}")
    if constraints.get("departure_date"):
        parts.append(f"📅 Ngày: {constraints['departure_date']}")
    if constraints.get("days"):
        parts.append(f"⏱️ Số ngày: {constraints['days']}")
    if constraints.get("budget"):
        parts.append(f"💰 Budget: {constraints['budget']:,} VND")

    parts.append("\n**Các bước:**")
    for i, step in enumerate(steps):
        label = STEP_LABELS.get(step, step)
        parts.append(f"  {i+1}. {label}")

    parts.append("\nBạn xác nhận kế hoạch này không?")
    return "\n".join(parts)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ResumeRequest(BaseModel):
    session_id: str
    response: str | dict = "ok"  # User's response: "ok" or dict with modifications


class ChatResponse(BaseModel):
    response: str
    session_id: str
    type: str = "done"  # "done" | "interrupt"
    interrupt_data: dict | None = None


# ── Synchronous endpoint ─────────────────────────────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Nhận tin nhắn từ user, chạy qua LangGraph, trả kết quả hoặc interrupt."""
    sid = request.session_id or str(uuid.uuid4())
    _init_session(sid)
    sessions[sid]["messages"].append(("user", request.message))

    try:
        result = await asyncio.to_thread(
            travel_agent.invoke,
            _build_graph_input(sid, request.message),
            _graph_config(sid),
        )
        processed = _process_graph_result(result, sid)

        if processed["type"] == "done":
            sessions[sid]["messages"].append(("assistant", processed["message"]))

        return ChatResponse(
            response=processed["message"],
            session_id=sid,
            type=processed["type"],
            interrupt_data=processed.get("data"),
        )
    except Exception as e:
        return ChatResponse(response=f"Lỗi: {str(e)}", session_id=sid)


# ── Resume endpoint (HITL) ───────────────────────────
@app.post("/api/chat/resume", response_model=ChatResponse)
async def resume_chat(request: ResumeRequest):
    """Resume graph sau khi user xác nhận interrupt."""
    sid = request.session_id
    _init_session(sid)

    try:
        # Resume graph (interrupt_before → invoke(None, config))
        result = await asyncio.to_thread(
            travel_agent.invoke,
            None,
            _graph_config(sid),
        )
        processed = _process_graph_result(result, sid)

        if processed["type"] == "done":
            sessions[sid]["messages"].append(("assistant", processed["message"]))

        return ChatResponse(
            response=processed["message"],
            session_id=sid,
            type=processed["type"],
            interrupt_data=processed.get("data"),
        )
    except Exception as e:
        return ChatResponse(response=f"Lỗi: {str(e)}", session_id=sid)


# ── SSE streaming endpoint ──────────────────────────
@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream response via Server-Sent Events. Hỗ trợ interrupt."""
    sid = request.session_id or str(uuid.uuid4())
    _init_session(sid)
    sessions[sid]["messages"].append(("user", request.message))

    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

            result = await asyncio.to_thread(
                travel_agent.invoke,
                _build_graph_input(sid, request.message),
                _graph_config(sid),
            )
            processed = _process_graph_result(result, sid)

            if processed["type"] == "interrupt":
                # Gửi interrupt data cho frontend
                yield f"data: {json.dumps({'type': 'interrupt', 'content': processed['message'], 'data': processed.get('data')}, ensure_ascii=False)}\n\n"
            else:
                # Stream response trong chunks
                ai_message = processed["message"]
                sessions[sid]["messages"].append(("assistant", ai_message))

                chunk_size = 12
                for i in range(0, len(ai_message), chunk_size):
                    chunk = ai_message[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── SSE streaming resume ────────────────────────────
@app.post("/api/chat/stream/resume")
async def stream_resume(request: ResumeRequest):
    """Stream resume sau interrupt."""
    sid = request.session_id
    _init_session(sid)

    async def event_generator():
        try:
            result = await asyncio.to_thread(
                travel_agent.invoke,
                None,
                _graph_config(sid),
            )
            processed = _process_graph_result(result, sid)

            if processed["type"] == "interrupt":
                yield f"data: {json.dumps({'type': 'interrupt', 'content': processed['message'], 'data': processed.get('data')}, ensure_ascii=False)}\n\n"
            else:
                ai_message = processed["message"]
                sessions[sid]["messages"].append(("assistant", ai_message))

                chunk_size = 12
                for i in range(0, len(ai_message), chunk_size):
                    chunk = ai_message[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    await asyncio.sleep(0.03)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Session management ───────────────────────────────
@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions with preview of last message."""
    result = []
    for sid, session in sessions.items():
        title = "Cuộc trò chuyện mới"
        for role, content in session["messages"]:
            if role == "user":
                title = content[:50] + ("…" if len(content) > 50 else "")
                break
        result.append({"session_id": sid, "title": title, "message_count": len(session["messages"])})
    return result


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full message history for a session."""
    if session_id not in sessions:
        return {"messages": []}
    return {
        "messages": [
            {"role": role, "content": content}
            for role, content in sessions[session_id]["messages"]
        ]
    }


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    sessions.pop(session_id, None)
    return {"status": "deleted"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
