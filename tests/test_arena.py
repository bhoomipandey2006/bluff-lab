import numpy as np
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from bluff_lab import Strategy, equilibrium, strategy_exploitability
from bluff_lab.game import head_to_head
from server import app as arena


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("ARENA_DB", str(tmp_path / "t.db")); arena._hits.clear()
    return TestClient(arena.app)


def sub(c, name, v): return c.post("/api/submit", json={"nickname": name, "v": list(map(float, v))})


def test_scores_are_recomputed_exactly_and_matrix_is_antisymmetric(client):
    rng = np.random.default_rng(5); vs = {f"p{i}": rng.random(12) for i in range(4)}; vs["eq"] = equilibrium(1 / 6).to_vector()
    for k, v in vs.items(): assert sub(client, k, v).status_code == 200
    d = client.get("/api/leaderboard").json()
    S = {k: Strategy.from_vector(v) for k, v in vs.items()}; S.update({k: Strategy.from_vector(v) for k, v in arena.HOUSE.items()})
    assert len(d["entries"]) == len(S) and d["n"] == 5 and sum(e["house"] for e in d["entries"]) == len(arena.HOUSE)
    for e in d["entries"]:
        s = S[e["nickname"]]; others = [head_to_head(s, t) for k, t in S.items() if k != e["nickname"]]
        assert e["exploitability"] == pytest.approx(strategy_exploitability(s), abs=1e-12)
        assert e["avg_payoff"] == pytest.approx(sum(others) / len(others), abs=1e-12)
    M = np.array(d["matrix"]["values"]); assert np.allclose(M, -M.T, atol=1e-12)
    assert min(M[d["matrix"]["names"].index("eq")]) >= -1e-12  # equilibrium never loses a match


def test_house_strategies_present_when_empty_and_not_deletable(client, monkeypatch):
    d = client.get("/api/leaderboard").json()
    assert d["n"] == 0 and len(d["entries"]) == len(arena.HOUSE) and all(e["house"] for e in d["entries"]) and d["matrix"] is not None
    monkeypatch.setenv("ADMIN_TOKEN", "t")
    assert client.delete("/api/admin/-1", headers={"x-admin-token": "t"}).json()["deleted"] == 0


@pytest.mark.parametrize("name,v", [("ok", [0.5] * 11), ("ok", [0.5] * 13), ("ok", [1.5] + [0.5] * 11), ("ok", [-0.1] + [0.5] * 11),
                                    ("", [0.5] * 12), ("x" * 21, [0.5] * 12), ("<script>", [0.5] * 12), ("a/b", [0.5] * 12)])
def test_invalid_input_rejected(client, name, v):
    assert sub(client, name, v).status_code == 422


def test_nan_and_non_numbers_rejected(client):
    assert client.post("/api/submit", data='{"nickname":"a","v":[NaN,0,0,0,0,0,0,0,0,0,0,0]}', headers={"content-type": "application/json"}).status_code == 422
    assert client.post("/api/submit", json={"nickname": "a", "v": ["__import__('os')"] * 12}).status_code == 422


def test_duplicate_nickname_conflict_and_rate_limit(client):
    assert sub(client, "dup", [0.5] * 12).status_code == 200 and sub(client, "dup", [0.5] * 12).status_code == 409
    codes = [sub(client, f"n{i}", [0.5] * 12).status_code for i in range(15)]
    assert 429 in codes


def test_admin_delete_requires_token(client, monkeypatch):
    sub(client, "gone", [0.5] * 12); eid = client.get("/api/leaderboard").json()["entries"][0]["id"]
    assert client.delete(f"/api/admin/{eid}").status_code == 403
    monkeypatch.setenv("ADMIN_TOKEN", "secret")
    assert client.delete(f"/api/admin/{eid}", headers={"x-admin-token": "wrong"}).status_code == 403
    assert client.delete(f"/api/admin/{eid}", headers={"x-admin-token": "secret"}).json()["deleted"] == 1
    assert client.get("/api/leaderboard").json()["n"] == 0


def test_entry_cap_and_cache_invalidation(client, monkeypatch):
    monkeypatch.setattr(arena, "MAX_ENTRIES", 2); monkeypatch.setattr(arena, "RATE_LIMIT", 100)
    assert sub(client, "a", [0.5] * 12).status_code == 200 and client.get("/api/leaderboard").json()["n"] == 1
    assert sub(client, "b", [0.2] * 12).status_code == 200 and client.get("/api/leaderboard").json()["n"] == 2
    assert sub(client, "c", [0.9] * 12).status_code == 503


def test_cors_header_only_for_configured_origin(tmp_path, monkeypatch):
    import importlib
    monkeypatch.setenv("ARENA_DB", str(tmp_path / "c.db")); monkeypatch.setenv("ALLOWED_ORIGINS", "https://site.example")
    m = importlib.reload(arena); c = TestClient(m.app)
    assert c.get("/api/leaderboard", headers={"Origin": "https://site.example"}).headers.get("access-control-allow-origin") == "https://site.example"
    assert "access-control-allow-origin" not in c.get("/api/leaderboard", headers={"Origin": "https://evil.example"}).headers
    monkeypatch.delenv("ALLOWED_ORIGINS"); importlib.reload(arena)
