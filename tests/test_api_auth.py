import pytest
import jwt
from fastapi.testclient import TestClient
from datetime import datetime, timedelta, timezone

from app.main import app
from app.config import JWT_SECRET

client = TestClient(app)

def test_protected_route_without_token():
    # Attempting to access an owner-protected route without authorization
    response = client.get("/approvals")
    assert response.status_code == 401
    assert "Missing or invalid token format" in response.json()["detail"]

def test_protected_route_with_invalid_token():
    # Attempting to access with an invalid token signature
    response = client.get(
        "/approvals",
        headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]

def test_protected_route_with_expired_token():
    # Generate an expired token
    payload = {
        "sub": "owner",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    response = client.get(
        "/approvals",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert "Token expired" in response.json()["detail"]

def test_protected_route_with_valid_token():
    # Generate a valid token
    payload = {
        "sub": "owner",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    
    response = client.get(
        "/approvals",
        headers={"Authorization": f"Bearer {token}"}
    )
    # The route might return 200 (if DB works) or 500 (if DB is uninitialized in test)
    # The important part is we get past the 401 Unauthorized phase
    assert response.status_code != 401
