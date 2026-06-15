from fastapi import APIRouter, Depends
from travel_ai_agent.api.dependencies import get_session_store
from travel_ai_agent.api.routers.auth import get_current_user
from travel_ai_agent.api.services.session_store import SessionStore

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])

@router.get("/summary")
async def get_analytics_summary(
    store: SessionStore = Depends(get_session_store),
    owner_id: str = Depends(get_current_user),
) -> dict[str, int]:
    """Returns analytics summary (in a real app, this would be admin-only)."""
    with store._connect() as connection:
        rows = connection.execute(
            "SELECT event_type, COUNT(*) as count FROM usage_events GROUP BY event_type"
        ).fetchall()
        
    return {row["event_type"]: int(row["count"]) for row in rows}
