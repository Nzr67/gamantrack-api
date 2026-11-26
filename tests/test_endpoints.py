import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.database import get_db
from app.models import Stop, Route, Timetable


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        class Scalars:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows
        return Scalars(self._rows)


class FakeSession:
    """Stand-in AsyncSession whose execute() returns canned model rows."""
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return FakeResult(self._rows)

    async def get(self, model, ident):
        for row in self._rows:
            if isinstance(row, model) and getattr(row, "id", None) == ident:
                return row
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def stop_rows():
    return [
        Stop(id=1, stop_name="Fort Railway Station", latitude=6.9319, longitude=79.8475),
        Stop(id=2, stop_name="Maradana Bus Stand", latitude=6.9336, longitude=79.8639),
    ]


@pytest.fixture
def route_rows():
    return [
        Route(id=1, route_number="120", start_name="Fort Railway Station", end_name="Homagama"),
        Route(id=2, route_number="138", start_name="Homagama", end_name="Pettah"),
    ]


@pytest.fixture
def timetable_rows():
    return [
        Timetable(id=1, route_id=1, departure_time="05:30:00", day_type="Weekday", direction="Outbound"),
        Timetable(id=2, route_id=1, departure_time="06:30:00", day_type="Weekday", direction="Outbound"),
    ]


@pytest.fixture
async def client(stop_rows, route_rows, timetable_rows):
    sessions = {
        "stops": FakeSession(stop_rows),
        "routes": FakeSession(route_rows),
        "schedules": FakeSession(timetable_rows),
    }

    async def override_get_db():
        # Yield the session matching the requested table by peeking at the call site is not
        # possible; instead return a session whose rows match whatever the endpoint queries.
        # We route by endpoint path via a closure override set per-test below.
        return sessions["stops"]

    yield sessions, override_get_db


@pytest.mark.asyncio
async def test_list_stops_limit_200(monkeypatch, stop_rows):
    # 5 rows so limit=200 returns all without hitting a page boundary
    rows = [Stop(id=i, stop_name=f"Stop {i}", latitude=6.9, longitude=79.8) for i in range(1, 6)]
    app.dependency_overrides[get_db] = lambda: FakeSession(rows)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/stops/?limit=200")
    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 5
    assert data["limit"] == 200


@pytest.mark.asyncio
async def test_list_routes(route_rows):
    app.dependency_overrides[get_db] = lambda: FakeSession(route_rows)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/routes/")
    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 2
    assert data[0]["route_number"] == "120"


@pytest.mark.asyncio
async def test_list_schedules(timetable_rows):
    app.dependency_overrides[get_db] = lambda: FakeSession(timetable_rows)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/schedules/")
    app.dependency_overrides.clear()
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["items"]) == 2
    assert data["items"][0]["day_type"] == "Weekday"
