import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr

from travel_ai_agent.api.dependencies import get_session_store
from fastapi.security import OAuth2PasswordBearer
from travel_ai_agent.api.services import auth_service
from travel_ai_agent.api.services.session_store import SessionStore

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user() -> str:
    # Temporarily bypassed for testing without frontend
    return "demo_user_123"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest, response: Response, store: SessionStore = Depends(get_session_store)):
    if store.get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    hashed_password = auth_service.get_password_hash(req.password)
    store.create_user(user_id, req.email, hashed_password)

    # Login automatically
    access_token = auth_service.create_access_token(user_id)
    refresh_token = auth_service.generate_refresh_token()
    token_hash = auth_service.hash_refresh_token(refresh_token)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    store.save_refresh_token(token_hash, user_id, expires_at)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, response: Response, store: SessionStore = Depends(get_session_store)):
    user = store.get_user_by_email(req.email)
    if not user or not auth_service.verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token = auth_service.create_access_token(user["id"])
    refresh_token = auth_service.generate_refresh_token()
    token_hash = auth_service.hash_refresh_token(refresh_token)

    expires_at = (datetime.now(timezone.utc) + timedelta(days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    store.save_refresh_token(token_hash, user["id"], expires_at)

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    store: SessionStore = Depends(get_session_store),
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    token_hash = auth_service.hash_refresh_token(refresh_token)
    token_data = store.get_refresh_token(token_hash)

    if not token_data or token_data["revoked"]:
        raise HTTPException(status_code=401, detail="Invalid or revoked refresh token")

    if datetime.fromisoformat(token_data["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Revoke old token
    store.revoke_refresh_token(token_hash)

    # Issue new pair
    user_id = token_data["user_id"]
    new_access_token = auth_service.create_access_token(user_id)
    new_refresh_token = auth_service.generate_refresh_token()
    new_token_hash = auth_service.hash_refresh_token(new_refresh_token)
    new_expires_at = (datetime.now(timezone.utc) + timedelta(days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()

    store.save_refresh_token(new_token_hash, user_id, new_expires_at)

    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=auth_service.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return TokenResponse(access_token=new_access_token)


@router.post("/logout")
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    store: SessionStore = Depends(get_session_store),
):
    if refresh_token:
        token_hash = auth_service.hash_refresh_token(refresh_token)
        store.revoke_refresh_token(token_hash)
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out successfully"}
