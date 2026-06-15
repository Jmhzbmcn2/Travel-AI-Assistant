"""
FastAPI application entrypoint.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from travel_ai_agent.api.routers import auth, chat, health, sessions, trips, analytics


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup & shutdown hooks."""
    # Startup: có thể khởi tạo resources ở đây
    yield
    # Shutdown: giải phóng resources


def create_app() -> FastAPI:
    """Application factory — tạo và cấu hình FastAPI app."""
    app = FastAPI(
        title="AI Travel Deal Hunter",
        version="1.0.0",
        lifespan=lifespan,
    )

    # ── CORS ─────────────────────────────────────────
    _default_origins = ["http://localhost:5173", "http://localhost:3000"]
    _env_origins = os.getenv("CORS_ORIGINS", "")
    cors_origins = (
        [o.strip() for o in _env_origins.split(",") if o.strip()]
        if _env_origins
        else _default_origins
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    import time
    import collections
    
    # In-memory token bucket rate limiter per IP
    RATE_LIMIT_TOKENS = 100
    RATE_LIMIT_REFILL_RATE = 2.0  # tokens per second
    
    class RateLimiter:
        def __init__(self):
            self.tokens = collections.defaultdict(lambda: RATE_LIMIT_TOKENS)
            self.last_update = collections.defaultdict(time.time)
            
        def consume(self, client_ip: str) -> bool:
            now = time.time()
            elapsed = now - self.last_update[client_ip]
            self.tokens[client_ip] = min(RATE_LIMIT_TOKENS, self.tokens[client_ip] + elapsed * RATE_LIMIT_REFILL_RATE)
            self.last_update[client_ip] = now
            
            if self.tokens[client_ip] >= 1.0:
                self.tokens[client_ip] -= 1.0
                return True
            return False

    limiter = RateLimiter()

    from fastapi.responses import JSONResponse
    from fastapi import Request

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        client_ip = request.client.host if request.client else "127.0.0.1"
        if not limiter.consume(client_ip):
            return JSONResponse(status_code=429, content={"detail": "Too Many Requests"})
        return await call_next(request)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    # ── Routers ──────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(trips.router)
    app.include_router(health.router)
    app.include_router(analytics.router)

    return app


app = create_app()
