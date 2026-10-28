from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException
from fastapi.testclient import TestClient
import pytest

from bnpl_cashflow.api.app import create_app
from bnpl_cashflow.api.sessions import DemoSessions
from tests.api.test_profiles import document


ORIGIN = "https://gitoddity.github.io"


def session_headers(client):
    response = client.post("/api/session")
    assert response.status_code == 201
    return {"X-DueMap-Session": response.json()["token"]}


def test_visitors_are_isolated_and_downloads_can_be_reimported(tmp_path):
    with TestClient(create_app(tmp_path / "unused.sqlite3", demo=True, allowed_origins=[ORIGIN])) as client:
        alice, bob = session_headers(client), session_headers(client)
        source = document()
        assert client.post("/api/profiles/import", headers=alice, json=source).status_code == 201
        assert client.get("/api/profiles", headers=bob).json() == []
        for endpoint in ("cards", "plans", "plans/overview", "projection", "export"):
            assert client.get(f"/api/profiles/personal/{endpoint}", headers=bob).status_code == 404
        assert client.patch("/api/profiles/personal/cards/card1", headers=bob, json={"name": "Stolen"}).status_code == 404
        assert client.delete("/api/profiles/personal/plans/plan1", headers=bob).status_code == 404
        download = client.get("/api/profiles/personal/export", headers=alice)
        assert download.status_code == 200
        assert "attachment" in download.headers["content-disposition"]
        assert download.headers["cache-control"] == "no-store"
        assert client.post("/api/profiles/import", headers=bob, json=download.json()).status_code == 201
        assert client.get("/api/profiles/personal/export", headers=bob).json() == download.json()
        # The same imported IDs/names can coexist in different visitors' workspaces.
        assert len(client.get("/api/profiles", headers=alice).json()) == 1
    assert not list(tmp_path.iterdir())


def test_missing_expired_and_restarted_sessions_do_not_expose_local_profiles(tmp_path):
    now = [0.0]
    sessions = DemoSessions(ttl_seconds=30, clock=lambda: now[0])
    with TestClient(create_app(tmp_path / "unused.sqlite3", demo=True, allowed_origins=[ORIGIN], sessions=sessions)) as client:
        assert client.get("/api/profiles").status_code == 401
        headers = session_headers(client)
        client.post("/api/profiles/import", headers=headers, json=document())
        now[0] = 31
        expired = client.get("/api/profiles", headers=headers)
        assert expired.status_code == 410
        assert "import your downloaded profile" in expired.json()["detail"]
        assert sessions.sessions == {}
        fresh = session_headers(client)
        assert client.get("/api/profiles", headers=fresh).json() == []
    with TestClient(create_app(demo=True, allowed_origins=[ORIGIN])) as restarted:
        assert restarted.get("/api/profiles", headers=fresh).status_code == 410


def test_sessions_are_bounded_and_idle_memory_is_released():
    now = [0.0]
    sessions = DemoSessions(ttl_seconds=30, max_sessions=1, clock=lambda: now[0])
    token = sessions.create()
    with sessions.use(token) as store:
        store.create("Personal")
        now[0] = 31
        sessions.expire()
        assert token in sessions.sessions  # An active request must not lose its database.
        with pytest.raises(HTTPException) as error:
            sessions.create()
        assert error.value.status_code == 503
    now[0] = 62
    sessions.expire()
    assert not sessions.sessions
    assert sessions.create() != token
    sessions.close()


def test_concurrent_session_requests_preserve_mutations():
    sessions = DemoSessions()
    token = sessions.create()

    def create(index):
        with sessions.use(token) as store:
            store.create(f"Profile {index}")

    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(create, range(12)))
        with sessions.use(token) as store:
            assert len(store.list()) == 12
    finally:
        sessions.close()


def test_cors_preflight_allows_only_the_configured_frontend():
    with TestClient(create_app(demo=True, allowed_origins=[ORIGIN])) as client:
        headers = {"Origin": ORIGIN, "Access-Control-Request-Method": "POST",
                   "Access-Control-Request-Headers": "content-type,x-duemap-session"}
        response = client.options("/api/profiles", headers=headers)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == ORIGIN
        blocked = client.options("/api/profiles", headers={**headers, "Origin": "https://other.example"})
        assert blocked.status_code == 400
        assert "access-control-allow-origin" not in blocked.headers
        assert client.get("/api/health").json() == {"status": "ok"}
