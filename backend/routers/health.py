"""
Health check router.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1", tags=["Health"])


@router.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
