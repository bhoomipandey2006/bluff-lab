"""Arena backend. Accepts ONLY a nickname and 12 numbers, recomputes everything exactly.
No code upload, no execution of user input, no personal data stored (IPs live in memory for rate limiting only)."""
from __future__ import annotations

import os
import re
import sqlite3
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from bluff_lab import Strategy, equilibrium, strategy_exploitability
from bluff_lab.game import head_to_head

DB = lambda: os.environ.get("ARENA_DB", "arena.db")  # noqa: E731
NICK = re.compile(r"^[A-Za-z0-9_\- ]{1,20}$")
MAX_ENTRIES = 200          # hard cap on stored entries: scoring is O(n^2), so this bounds CPU per refresh
MATRIX_MAX = 30            # show the full matrix up to this many entries
RATE_LIMIT, RATE_WINDOW = 10, 60.0
_hits: dict[str, deque] = defaultdict(deque)

app = FastAPI(title="Bluff Lab Arena")
_origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if _origins:  # needed when the static site and the API live on different hosts
    app.add_middleware(CORSMiddleware, allow_origins=_origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
_cache: dict = {"key": None, "val": None}

# Always-present, clearly labelled house strategies. Computed on the fly, never stored, so the board is
# never empty even when a free host wipes the database. Same hand-written field as scripts/field_demo.py.
HOUSE: dict[str, list[float]] = {
    "House: equilibrium (1/6)": [float(x) for x in equilibrium(1 / 6).to_vector()],
    "House: never bluffs": [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1],
    "House: tight-passive": [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1],
    "House: bluff-happy": [1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
    "House: calling station": [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1],
    "House: maniac": [1.0] * 12,
    "House: coin flip": [0.5] * 12,
}


@app.exception_handler(RequestValidationError)
async def _invalid(_: Request, exc: RequestValidationError):
    # never echo submitted values back (NaN is not valid JSON and would crash the response)
    return JSONResponse(status_code=422, content={"detail": [{"loc": [str(x) for x in e["loc"]], "msg": "invalid value"} for e in exc.errors()]})


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB())
    c.execute("CREATE TABLE IF NOT EXISTS entries (id INTEGER PRIMARY KEY AUTOINCREMENT, nickname TEXT UNIQUE NOT NULL, v TEXT NOT NULL, created REAL NOT NULL)")
    return c


class Submission(BaseModel):
    nickname: str
    v: list[float] = Field(min_length=12, max_length=12)

    @field_validator("nickname")
    @classmethod
    def _nick(cls, x: str) -> str:
        x = x.strip()
        if not NICK.match(x):
            raise ValueError("nickname: 1-20 chars, letters, digits, space, _ or -")
        return x

    @field_validator("v")
    @classmethod
    def _v(cls, xs: list[float]) -> list[float]:
        if not all(0.0 <= x <= 1.0 for x in xs):  # NaN fails both comparisons
            raise ValueError("all 12 numbers must be in [0, 1]")
        return xs


def _limited(ip: str) -> bool:
    now, q = time.time(), _hits[ip]
    if len(_hits) > 10_000:  # bound memory under many distinct IPs
        _hits.clear(); q = _hits[ip]
    while q and now - q[0] > RATE_WINDOW:
        q.popleft()
    if len(q) >= RATE_LIMIT:
        return True
    q.append(now)
    return False


@app.get("/")
def root():
    return {"service": "Bluff Lab arena", "status": "running", "leaderboard": "/api/leaderboard", "open the app at": "http://localhost:5173"}


@app.post("/api/submit")
def submit(sub: Submission, request: Request):
    if _limited(request.client.host if request.client else "?"):
        raise HTTPException(429, "rate limit")
    c = conn()
    if c.execute("SELECT COUNT(*) FROM entries").fetchone()[0] >= MAX_ENTRIES:
        c.close(); raise HTTPException(503, "arena full")
    try:
        c.execute("INSERT INTO entries (nickname, v, created) VALUES (?, ?, ?)", (sub.nickname, ",".join(repr(float(x)) for x in sub.v), time.time()))
        c.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "nickname taken") from None
    finally:
        c.close()
    return {"ok": True}


@app.get("/api/leaderboard")
def leaderboard():
    c = conn()
    rows = c.execute("SELECT id, nickname, v FROM entries ORDER BY id LIMIT ?", (MAX_ENTRIES,)).fetchall()
    c.close()
    key = (DB(), tuple((r[0], r[2]) for r in rows))  # recompute only when entries change
    if _cache["key"] == key:
        return _cache["val"]
    users = [(r[0], r[1], [float(x) for x in r[2].split(",")], False) for r in rows]
    field = users + [(-(i + 1), name, v, True) for i, (name, v) in enumerate(HOUSE.items())]
    strats = [Strategy.from_vector(f[2]) for f in field]
    entries = []
    for i, f in enumerate(field):
        others = [head_to_head(strats[i], t) for j, t in enumerate(strats) if j != i]
        entries.append({"id": f[0], "nickname": f[1], "house": f[3], "exploitability": strategy_exploitability(strats[i]),
                        "avg_payoff": sum(others) / len(others)})
    matrix = None
    if 2 <= len(field) <= MATRIX_MAX:
        matrix = {"names": [f[1] for f in field], "values": [[head_to_head(x, y) for y in strats] for x in strats]}
    out = {"entries": entries, "matrix": matrix, "n": len(users)}
    _cache["key"], _cache["val"] = key, out
    return out


@app.delete("/api/admin/{entry_id}")
def admin_delete(entry_id: int, x_admin_token: str | None = Header(default=None)):
    token = os.environ.get("ADMIN_TOKEN")
    if not token or x_admin_token != token:
        raise HTTPException(403, "forbidden")
    c = conn(); cur = c.execute("DELETE FROM entries WHERE id = ?", (entry_id,)); c.commit(); c.close()
    return {"deleted": cur.rowcount}
