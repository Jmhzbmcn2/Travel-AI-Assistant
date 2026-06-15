"""SQLite persistence for UI sessions, trips, decisions, cache, and usage."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from travel_ai_agent.api.schemas.session import SessionInfo, SessionMessage
from travel_ai_agent.schemas import DecisionOutput, TripPlan


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionStore:
    def __init__(self, database_path: str | None = None) -> None:
        default_path = Path(os.getenv("TRAVEL_DB_PATH", "data/travel_ai_agent.sqlite"))
        self.database_path = Path(database_path) if database_path else default_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                """
            )
            row = connection.execute("SELECT MAX(version) as version FROM schema_migrations").fetchone()
            current_version = row["version"] if row and row["version"] is not None else 0

            if current_version == 0:
                has_sessions = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
                ).fetchone()
                if has_sessions:
                    connection.execute("INSERT INTO schema_migrations (version, applied_at) VALUES (1, ?)", (_utc_now(),))
                    current_version = 1
                else:
                    connection.executescript(
                        """
                        CREATE TABLE sessions (
                            session_id TEXT PRIMARY KEY,
                            title TEXT NOT NULL DEFAULT 'Cuộc trò chuyện mới',
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id TEXT NOT NULL,
                            role TEXT NOT NULL,
                            content TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                        CREATE TABLE trips (
                            session_id TEXT PRIMARY KEY,
                            plan_json TEXT NOT NULL,
                            status TEXT NOT NULL,
                            version INTEGER NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE decisions (
                            session_id TEXT PRIMARY KEY,
                            decision_json TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        );
                        CREATE TABLE provider_cache (
                            cache_key TEXT PRIMARY KEY,
                            payload_json TEXT NOT NULL,
                            expires_at TEXT NOT NULL
                        );
                        CREATE TABLE usage_events (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            name TEXT NOT NULL,
                            metadata_json TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                        INSERT INTO schema_migrations (version, applied_at) VALUES (1, datetime('now'));
                        """
                    )
                    current_version = 1

            if current_version == 1:
                connection.executescript(
                    """
                    CREATE TABLE users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    );
                    CREATE TABLE refresh_tokens (
                        token_hash TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        expires_at TEXT NOT NULL,
                        revoked BOOLEAN NOT NULL DEFAULT 0
                    );
                    ALTER TABLE sessions ADD COLUMN owner_id TEXT DEFAULT 'test_user';
                    ALTER TABLE trips ADD COLUMN owner_id TEXT DEFAULT 'test_user';
                    ALTER TABLE decisions ADD COLUMN owner_id TEXT DEFAULT 'test_user';
                    ALTER TABLE usage_events ADD COLUMN owner_id TEXT DEFAULT 'test_user';
                    INSERT INTO schema_migrations (version, applied_at) VALUES (2, datetime('now'));
                    """
                )
                current_version = 2

    def init(self, sid: str, owner_id: str) -> None:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT OR IGNORE INTO sessions(session_id, owner_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (sid, owner_id, now, now),
            )

    def add_message(self, sid: str, owner_id: str, role: str, content: str) -> None:
        self.init(sid, owner_id)
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO messages(session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (sid, role, content, now),
            )
            if role == "user":
                connection.execute(
                    """
                    UPDATE sessions SET
                        title = CASE WHEN title = 'Cuộc trò chuyện mới' THEN ? ELSE title END,
                        updated_at = ?
                    WHERE session_id = ? AND owner_id = ?
                    """,
                    (content[:50], now, sid, owner_id),
                )

    def get_messages(self, sid: str, owner_id: str) -> list[SessionMessage]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT role, content FROM messages WHERE session_id = (SELECT session_id FROM sessions WHERE session_id = ? AND owner_id = ?) ORDER BY id",
                (sid, owner_id),
            ).fetchall()
        return [SessionMessage(role=row["role"], content=row["content"]) for row in rows]

    def exists(self, sid: str, owner_id: str) -> bool:
        with self._connect() as connection:
            return connection.execute(
                "SELECT 1 FROM sessions WHERE session_id = ? AND owner_id = ?", (sid, owner_id)
            ).fetchone() is not None

    def get_session_owner(self, sid: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT owner_id FROM sessions WHERE session_id = ?", (sid,)).fetchone()
        return row["owner_id"] if row else None

    def delete(self, sid: str, owner_id: str) -> None:
        with self._lock, self._connect() as connection:
            # Check owner first
            if not self.exists(sid, owner_id):
                return
            for table in ("messages", "trips", "decisions", "usage_events", "sessions"):
                connection.execute(f"DELETE FROM {table} WHERE session_id = ?", (sid,))

    def rename_session(self, sid: str, owner_id: str, title: str) -> None:
        now = _utc_now()
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ? AND owner_id = ?",
                (title, now, sid, owner_id),
            )

    def list_all(self, owner_id: str) -> list[SessionInfo]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT s.session_id, s.title, COUNT(m.id) AS message_count
                FROM sessions s LEFT JOIN messages m ON m.session_id = s.session_id
                WHERE s.owner_id = ?
                GROUP BY s.session_id, s.title, s.updated_at
                ORDER BY s.updated_at DESC
                """,
                (owner_id,)
            ).fetchall()
        return [
            SessionInfo(session_id=row["session_id"], title=row["title"], message_count=row["message_count"])
            for row in rows
        ]

    def save_trip(self, sid: str, owner_id: str, plan: TripPlan, status: str = "draft") -> TripPlan:
        self.init(sid, owner_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO trips(session_id, owner_id, plan_json, status, version, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    plan_json=excluded.plan_json,
                    status=excluded.status,
                    version=excluded.version,
                    updated_at=excluded.updated_at
                """,
                (sid, owner_id, plan.model_dump_json(), status, plan.version, _utc_now()),
            )
        return plan

    def get_trip(self, sid: str, owner_id: str) -> TripPlan | None:
        with self._connect() as connection:
            row = connection.execute("SELECT plan_json FROM trips WHERE session_id = ? AND owner_id = ?", (sid, owner_id)).fetchone()
        return TripPlan.model_validate_json(row["plan_json"]) if row else None

    def get_trip_status(self, sid: str, owner_id: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute("SELECT status FROM trips WHERE session_id = ? AND owner_id = ?", (sid, owner_id)).fetchone()
        return row["status"] if row else None

    def patch_trip(self, sid: str, owner_id: str, changes: dict[str, Any]) -> TripPlan:
        current = self.get_trip(sid, owner_id)
        if current is None:
            raise KeyError(sid)
        payload = current.model_dump()
        payload.update(changes)
        payload["version"] = current.version + 1
        return self.save_trip(sid, owner_id, TripPlan.model_validate(payload), self.get_trip_status(sid, owner_id) or "draft")

    def save_decision(self, sid: str, owner_id: str, decision: DecisionOutput) -> None:
        self.init(sid, owner_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO decisions(session_id, owner_id, decision_json, updated_at) VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET decision_json=excluded.decision_json, updated_at=excluded.updated_at
                """,
                (sid, owner_id, decision.model_dump_json(), _utc_now()),
            )
            connection.execute(
                "UPDATE trips SET status = 'decided', updated_at = ? WHERE session_id = ?",
                (_utc_now(), sid),
            )

    def get_decision(self, sid: str, owner_id: str) -> DecisionOutput | None:
        with self._connect() as connection:
            row = connection.execute("SELECT decision_json FROM decisions WHERE session_id = ? AND owner_id = ?", (sid, owner_id)).fetchone()
        return DecisionOutput.model_validate_json(row["decision_json"]) if row else None

    def add_usage_event(self, sid: str, owner_id: str, event_type: str, name: str, metadata: dict[str, Any] | None = None) -> None:
        self.init(sid, owner_id)
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO usage_events(session_id, owner_id, event_type, name, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (sid, owner_id, event_type, name, json.dumps(metadata or {}, ensure_ascii=False), _utc_now()),
            )

    def usage_count(self, sid: str, owner_id: str, event_type: str, name: str | None = None) -> int:
        query = "SELECT COUNT(*) AS count FROM usage_events WHERE session_id = ? AND owner_id = ? AND event_type = ?"
        params: list[Any] = [sid, owner_id, event_type]
        if name:
            query += " AND name = ?"
            params.append(name)
        with self._connect() as connection:
            return int(connection.execute(query, params).fetchone()["count"])

    def set_cache(self, cache_key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO provider_cache(cache_key, payload_json, expires_at) VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET payload_json=excluded.payload_json, expires_at=excluded.expires_at
                """,
                (cache_key, json.dumps(payload, ensure_ascii=False), expires_at),
            )

    def get_cache(self, cache_key: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json, expires_at FROM provider_cache WHERE cache_key = ?",
                (cache_key,),
            ).fetchone()
        if not row or datetime.fromisoformat(row["expires_at"]) <= datetime.now(timezone.utc):
            return None
        return json.loads(row["payload_json"])

    def add_llm_usage(
        self,
        sid: str,
        owner_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
    ) -> None:
        """Record an LLM call's token usage."""
        self.add_usage_event(sid, owner_id, "llm_call", model, {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd, 6),
        })

    def get_usage_summary(self, sid: str, owner_id: str) -> dict[str, Any]:
        """Aggregate usage stats for a session."""
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT event_type, name, metadata_json FROM usage_events WHERE session_id = ? AND owner_id = ?",
                (sid, owner_id),
            ).fetchall()
        total_input = 0
        total_output = 0
        total_cost = 0.0
        llm_calls = 0
        tool_calls = 0
        for row in rows:
            event_type = row["event_type"]
            if event_type == "llm_call":
                llm_calls += 1
                meta = json.loads(row["metadata_json"])
                total_input += meta.get("input_tokens", 0)
                total_output += meta.get("output_tokens", 0)
                total_cost += meta.get("cost_usd", 0)
            elif event_type == "tool_call":
                tool_calls += 1
        return {
            "session_id": sid,
            "llm_calls": llm_calls,
            "tool_calls": tool_calls,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost_usd": round(total_cost, 6),
        }

    # --- Authentication Methods ---

    def create_user(self, user_id: str, email: str, password_hash: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO users(id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, email, password_hash, _utc_now()),
            )

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT id, email, password_hash, created_at FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT id, email, password_hash, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def save_refresh_token(self, token_hash: str, user_id: str, expires_at: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO refresh_tokens(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (token_hash, user_id, expires_at),
            )

    def get_refresh_token(self, token_hash: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT token_hash, user_id, expires_at, revoked FROM refresh_tokens WHERE token_hash = ?",
                (token_hash,)
            ).fetchone()
        return dict(row) if row else None

    def revoke_refresh_token(self, token_hash: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
                (token_hash,)
            )
