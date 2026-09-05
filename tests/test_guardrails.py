from pathlib import Path
from uuid import uuid4

import pytest

from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.core.guardrails import record_tool_call, tool_allowed


def test_tool_budget_and_cache():
    database = Path("data") / f"test-guardrails-{uuid4()}.sqlite"
    store = SessionStore(str(database))
    for _ in range(3):
        record_tool_call(store, "session", "flight_search")
    assert not tool_allowed(store, "session", "flight_search")
    with pytest.raises(RuntimeError):
        record_tool_call(store, "session", "flight_search")

    store.set_cache("flight:sgn:dad", {"value": 1}, 60)
    assert store.get_cache("flight:sgn:dad") == {"value": 1}
