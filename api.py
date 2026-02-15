import uuid
import json
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.graphs.main_graph import travel_agent

app = FastAPI(title="AI Travel Deal Hunter")

# CORS — cho phép React dev server gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory session store ───────────────────────────
# Mỗi session lưu cả messages lẫn state data (flight/hotel results)
# để follow-up questions có thể truy cập kết quả trước đó.
sessions: dict[str, dict] = {}


def _init_session(sid: str):
    """Khởi tạo session mới nếu chưa tồn tại."""
    if sid not in sessions:
        sessions[sid] = {
            "messages": [],
            "flight_results": [],
            "hotel_results": [],
            "user_request": {},
        }


def _build_graph_input(sid: str) -> dict:
    """Xây dựng input cho LangGraph từ session, bao gồm cả state trước đó."""
    session = sessions[sid]
    graph_input = {"messages": list(session["messages"])}
    # Truyền kết quả tìm kiếm trước đó để follow_up_node có data
    if session["flight_results"]:
        graph_input["flight_results"] = session["flight_results"]
    if session["hotel_results"]:
        graph_input["hotel_results"] = session["hotel_results"]
    if session["user_request"]:
        graph_input["user_request"] = session["user_request"]
    return graph_input


def _save_state_from_result(sid: str, result: dict):
    """Lưu lại state từ kết quả graph (flight/hotel results, user_request)."""
    if result.get("flight_results"):
        sessions[sid]["flight_results"] = result["flight_results"]
    if result.get("hotel_results"):
        sessions[sid]["hotel_results"] = result["hotel_results"]
    if result.get("user_request"):
        sessions[sid]["user_request"] = result["user_request"]


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


# ── Synchronous endpoint (backward-compatible) ───────
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Nhận tin nhắn từ user, chạy qua LangGraph, trả kết quả."""
    sid = request.session_id or str(uuid.uuid4())
    _init_session(sid)

    sessions[sid]["messages"].append(("user", request.message))

    try:
        result = travel_agent.invoke(_build_graph_input(sid))
        ai_message = result["messages"][-1].content
        sessions[sid]["messages"].append(("assistant", ai_message))
        _save_state_from_result(sid, result)
        return ChatResponse(response=ai_message, session_id=sid)
    except Exception as e:
        return ChatResponse(response=f"Lỗi: {str(e)}", session_id=sid)


# ── SSE streaming endpoint ───────────────────────────
@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream response via Server-Sent Events."""
    sid = request.session_id or str(uuid.uuid4())
    _init_session(sid)

    sessions[sid]["messages"].append(("user", request.message))

    async def event_generator():
        try:
            # Send session_id first
            yield f"data: {json.dumps({'type': 'session', 'session_id': sid})}\n\n"

            # Run the agent (blocking) in a thread so we don't block the event loop
            result = await asyncio.to_thread(
                travel_agent.invoke,
                _build_graph_input(sid)
            )
            ai_message = result["messages"][-1].content
            sessions[sid]["messages"].append(("assistant", ai_message))
            _save_state_from_result(sid, result)

            # Stream the response in chunks for a typing effect
            chunk_size = 12
            for i in range(0, len(ai_message), chunk_size):
                chunk = ai_message[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                await asyncio.sleep(0.03)

            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ── Session management ────────────────────────────────
@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions with preview of last message."""
    result = []
    for sid, session in sessions.items():
        # Find first user message as title
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

