from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from travel_ai_agent.api.dependencies import get_graph, get_session_store
from travel_ai_agent.api.main import app
from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.schemas import TripPlan
from travel_ai_agent.api.routers.auth import get_current_user


class FakeGraph:
    def __init__(self):
        self.updates = []

    async def aupdate_state(self, config, values):
        self.updates.append((config, values))


def test_patch_trip_plan_keeps_session_id():
    database = Path("data") / f"test-api-{uuid4()}.sqlite"
    store = SessionStore(str(database))
    store.save_trip(
        "same-session",
        "test_user",
        TripPlan(
            destination="Da Nang",
            days=3,
            travelers=2,
            budget_total=8_000_000,
            preferences=["bien"],
            comfort_level="medium",
        ),
        "awaiting_confirmation",
    )
    graph = FakeGraph()

    async def fake_get_graph():
        yield graph

    app.dependency_overrides[get_session_store] = lambda: store
    app.dependency_overrides[get_graph] = fake_get_graph
    app.dependency_overrides[get_current_user] = lambda: "test_user"
    try:
        response = TestClient(app).patch(
            "/api/v1/trips/same-session/plan",
            json={"budget_total": 9_000_000, "preferences": ["bien", "an ngon"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["session_id"] == "same-session"
    assert response.json()["plan"]["version"] == 2
    assert response.json()["status"] == "awaiting_confirmation"
    assert graph.updates[0][0]["configurable"]["thread_id"] == "same-session"
