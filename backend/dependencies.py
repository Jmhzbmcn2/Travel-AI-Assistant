"""
FastAPI dependencies — Depends() providers.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from backend.services.session_store import SessionStore


# ── Singleton instances ──────────────────────────────

@lru_cache(maxsize=1)
def _get_session_store() -> SessionStore:
    return SessionStore()


def get_session_store() -> SessionStore:
    """Dependency: returns the singleton SessionStore."""
    return _get_session_store()


def get_graph() -> CompiledStateGraph:
    """Dependency: returns the compiled travel agent graph."""
    from src.graphs.main_graph import travel_agent
    return travel_agent
