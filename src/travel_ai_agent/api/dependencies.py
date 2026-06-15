"""
FastAPI dependencies — Depends() providers.
"""
from __future__ import annotations

from functools import lru_cache

from langgraph.graph.state import CompiledStateGraph

from travel_ai_agent.api.services.session_store import SessionStore


# ── Singleton instances ──────────────────────────────

@lru_cache(maxsize=1)
def _get_session_store() -> SessionStore:
    return SessionStore()


def get_session_store() -> SessionStore:
    """Dependency: returns the singleton SessionStore."""
    return _get_session_store()


from typing import AsyncGenerator
import os
from pathlib import Path

async def get_graph() -> AsyncGenerator[CompiledStateGraph, None]:
    """Dependency: returns the compiled travel agent graph with AsyncSqliteSaver."""
    from travel_ai_agent.graphs.main_graph import travel_agent as graph
    
    try:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        
        checkpoint_path = Path(os.getenv("LANGGRAPH_CHECKPOINT_PATH", "data/langgraph_checkpoints.sqlite"))
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with AsyncSqliteSaver.from_conn_string(str(checkpoint_path)) as memory:
            compiled_graph = graph.compile(
                checkpointer=memory,
                interrupt_before=["human_confirm"],
            )
            yield compiled_graph
            
    except ImportError:
        from langgraph.checkpoint.memory import MemorySaver
        memory = MemorySaver()
        compiled_graph = graph.compile(
            checkpointer=memory,
            interrupt_before=["human_confirm"],
        )
        yield compiled_graph
