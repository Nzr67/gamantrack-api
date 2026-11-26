import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.database import get_db


async def override_get_db():
    class MockResult:
        def scalar_one(self):
            return 5

    class MockSession:
        async def execute(self, *args, **kwargs):
            return MockResult()

    yield MockSession()


@pytest.fixture
async def client():
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "routes_seeded" in data