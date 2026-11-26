import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app
from app.database import get_db
from app.models import AdminUser
from app.auth import create_access_token


class FakeSession:
    """Stand-in AsyncSession whose execute() returns canned model rows."""
    def __init__(self, rows):
        self._rows = rows
        self._added = []

    async def execute(self, stmt):
        class FakeResult:
            def __init__(self, rows):
                self._rows = rows
            def scalar_one_or_none(self):
                return self._rows[0] if self._rows else None
            def scalars(self):
                class Scalars:
                    def __init__(self, rows):
                        self._rows = rows
                    def all(self):
                        return self._rows
                return Scalars(self._rows)
        return FakeResult(self._rows)

    def add(self, obj):
        self._added.append(obj)

    async def commit(self):
        pass

    async def refresh(self, obj):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def admin_user():
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return AdminUser(
        id=1,
        username="admin",
        password_hash=pwd_context.hash("admin123"),
        role="ADMIN",
    )


@pytest.fixture
def admin_session(admin_user):
    return FakeSession([admin_user])


@pytest.mark.asyncio
async def test_admin_login_success(monkeypatch, admin_user, admin_session):
    """Test successful admin login returns token with role admin."""
    app.dependency_overrides[get_db] = lambda: admin_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"
    
    # Verify token is valid
    from app.auth import decode_access_token
    payload = decode_access_token(data["access_token"])
    assert payload is not None
    assert payload["sub"] == "admin"
    assert payload["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_admin_login_wrong_password(monkeypatch, admin_user, admin_session):
    """Test admin login with wrong password returns 401."""
    app.dependency_overrides[get_db] = lambda: admin_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 401, resp.text
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_admin_login_nonexistent_user(monkeypatch, admin_session):
    """Test admin login with nonexistent user returns 401."""
    # Create a session with no admin user
    empty_session = FakeSession([])
    app.dependency_overrides[get_db] = lambda: empty_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/auth/login", json={"username": "nonexistent", "password": "admin123"})
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 401, resp.text
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_admin_me_endpoint(monkeypatch, admin_user, admin_session):
    """Test /api/admin/me endpoint returns current admin."""
    app.dependency_overrides[get_db] = lambda: admin_session
    
    # Create a valid token
    token = create_access_token({"sub": "admin", "role": "ADMIN"})
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/admin/me", headers={"Authorization": f"Bearer {token}"})
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "admin"
    assert data["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_admin_me_invalid_token(monkeypatch, admin_session):
    """Test /api/admin/me with invalid token returns 401."""
    app.dependency_overrides[get_db] = lambda: admin_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/admin/me", headers={"Authorization": "Bearer invalid_token"})
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_admin_endpoints_require_auth(monkeypatch, admin_session):
    """Test that admin endpoints require authentication."""
    app.dependency_overrides[get_db] = lambda: admin_session
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test without token
        resp = await ac.get("/api/admin/fare-matrix")
    
    app.dependency_overrides.clear()
    
    assert resp.status_code == 401, resp.text