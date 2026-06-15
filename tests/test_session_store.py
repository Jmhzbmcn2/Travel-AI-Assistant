from pathlib import Path
from uuid import uuid4

from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.schemas import TripPlan


def test_session_and_trip_persist_across_store_instances():
    database = Path("data") / f"test-travel-{uuid4()}.sqlite"
    database.parent.mkdir(parents=True, exist_ok=True)
    first = SessionStore(str(database))
    first.add_message("session-1", "test_user", "user", "Da Nang")
    first.save_trip(
        "session-1",
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

    second = SessionStore(str(database))
    assert second.get_messages("session-1", "test_user")[0].content == "Da Nang"
    assert second.get_trip("session-1", "test_user").destination == "Da Nang"
    assert second.get_trip_status("session-1", "test_user") == "awaiting_confirmation"

    patched = second.patch_trip("session-1", "test_user", {"budget_total": 9_000_000})
    assert patched.version == 2
    assert patched.budget_total == 9_000_000
