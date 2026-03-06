"""
In-memory session store.

Quản lý session metadata (messages cho UI display).
Checkpointer (MemorySaver) trong LangGraph quản lý graph state riêng.
"""
from __future__ import annotations

from backend.schemas.session import SessionInfo, SessionMessage


class SessionStore:
    """Thread-safe in-memory session storage."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict] = {}

    # ── CRUD ────────────────────────────────────────────

    def init(self, sid: str) -> None:
        """Khởi tạo session nếu chưa tồn tại."""
        if sid not in self._sessions:
            self._sessions[sid] = {"messages": []}

    def add_message(self, sid: str, role: str, content: str) -> None:
        """Thêm message vào session."""
        self.init(sid)
        self._sessions[sid]["messages"].append((role, content))

    def get_messages(self, sid: str) -> list[SessionMessage]:
        """Lấy danh sách messages cho một session."""
        if sid not in self._sessions:
            return []
        return [
            SessionMessage(role=role, content=content)
            for role, content in self._sessions[sid]["messages"]
        ]

    def exists(self, sid: str) -> bool:
        """Kiểm tra session có tồn tại không."""
        return sid in self._sessions

    def delete(self, sid: str) -> None:
        """Xóa session."""
        self._sessions.pop(sid, None)

    def list_all(self) -> list[SessionInfo]:
        """Liệt kê tất cả sessions với preview."""
        result = []
        for sid, session in self._sessions.items():
            title = "Cuộc trò chuyện mới"
            for role, content in session["messages"]:
                if role == "user":
                    title = content[:50] + ("…" if len(content) > 50 else "")
                    break
            result.append(
                SessionInfo(
                    session_id=sid,
                    title=title,
                    message_count=len(session["messages"]),
                )
            )
        return result
