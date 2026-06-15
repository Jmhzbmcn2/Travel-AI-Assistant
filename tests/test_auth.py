import os
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest
from datetime import datetime, timezone, timedelta

# Avoid DB issues
os.environ["TRAVEL_DB_PATH"] = ":memory:" # just to avoid overriding default

from travel_ai_agent.api.main import app
from travel_ai_agent.api.services.session_store import SessionStore
from travel_ai_agent.api.services import auth_service
from travel_ai_agent.api.dependencies import get_session_store

client = TestClient(app)

import uuid
from pathlib import Path

@pytest.fixture
def store():
    database = Path("data") / f"test-auth-{uuid.uuid4()}.sqlite"
    database.parent.mkdir(parents=True, exist_ok=True)
    db = SessionStore(str(database))
    yield db
    if database.exists():
        try:
            database.unlink()
        except PermissionError:
            pass

def test_register_and_login(store):
    app.dependency_overrides[get_session_store] = lambda: store
    
    # 1. Register
    res = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "strongpassword123"
    })
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.cookies
    
    # 2. Login
    res_login = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "strongpassword123"
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
    
    # 3. Wrong password
    res_bad = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "wrong"
    })
    assert res_bad.status_code == 401
        
    app.dependency_overrides.clear()

def test_refresh_and_logout(store):
    app.dependency_overrides[get_session_store] = lambda: store
    
    res = client.post("/api/v1/auth/register", json={
        "email": "refresh@example.com",
        "password": "pw"
    })
    refresh_cookie = res.cookies.get("refresh_token")
    
    # Refresh token
    client.cookies.set("refresh_token", refresh_cookie)
    res_refresh = client.post("/api/v1/auth/refresh")
    assert res_refresh.status_code == 200
    assert "access_token" in res_refresh.json()
    
    # Logout
    res_logout = client.post("/api/v1/auth/logout")
    assert res_logout.status_code == 200
    
    # Try refresh after logout
    res_fail = client.post("/api/v1/auth/refresh")
    assert res_fail.status_code == 401
