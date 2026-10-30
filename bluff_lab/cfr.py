"""CFR, CFR+ and external-sampling MCCFR on Kuhn poker (own implementation).

Information sets are keyed (player, card, history) with history in
'', 'cb' (player 0) and 'c', 'b' (player 1). Action 0 = pass/fold, 1 = bet/call.
Average strategies are returned as a game.Strategy; seeds are explicit.
"""
from __future__ import annotations

import numpy as np

from .game import CARDS, Seat1, Seat2, Strategy

KEYS = [(p, c, h) for c in CARDS for (p, h) in ((0, ""), (0, "cb"), (1, "c"), (1, "b"))]
_NEXT = {"": ("c", "b"), "c": ("cc", "cb"), "b": ("bf", "bc"), "cb": ("cbf", "cbc")}
_PLAYER = {"": 0, "c": 1, "b": 1, "cb": 0}


def _terminal(h: str, cards) -> int | None:
    w = 1 if cards[0] > cards[1] else -1
    return {"cc": w, "bc": 2 * w, "cbc": 2 * w, "bf": 1, "cbf": -1}.get(h)


def _to_strategy(avg: dict) -> Strategy:
    g = lambda p, h: np.array([avg[(p, c, h)][1] for c in CARDS])
    return Strategy(Seat1(g(0, ""), g(0, "cb")), Seat2(g(1, "c"), g(1, "b")))


def _uniform_if_zero(v: np.ndarray) -> np.ndarray:
    s = v.sum()
    return v / s if s > 0 else np.array([0.5, 0.5])


def _regret_matching(r: np.ndarray) -> np.ndarray:
    p = np.maximum(r, 0.0)
    s = p.sum()
    return p / s if s > 0 else np.array([0.5, 0.5])


def _init_arrays(init_strategy, init_regrets, seed):
    R = {k: np.zeros(2) for k in KEYS}
    if init_regrets:
        rng = np.random.default_rng(seed)
        for k in KEYS:
            R[k] = rng.random(2) * init_regrets
    return R


def run_cfr(iters: int, *, plus: bool = False, alternating: bool | None = None,
            linear: bool | None = None, init_regret_scale: float = 0.0,
            seed: int = 0, checkpoints=None, callback=None) -> Strategy:
    """Vanilla CFR (simultaneous updates, uniform averaging) or CFR+
    (regret floor at 0, alternating updates, linear averaging).
    `alternating` / `linear` default to the value of `plus` but can be set
    independently (OpenSpiel's CFRSolver = alternating, uniform averaging).

    init_regret_scale > 0 seeds each information set with random positive
    regrets (uniform[0,scale)^2), which shifts where the average strategy
    lands inside the equilibrium family. Checkpoints: iterable of iteration
    counts at which callback(t, Strategy) is called."""
    alternating = plus if alternating is None else alternating
    linear = plus if linear is None else linear
    R = _init_arrays(None, init_regret_scale, seed)
    S = {k: np.zeros(2) for k in KEYS}
    cps = set(checkpoints or [])

    def walk(cards, h, pi, strat, dR, dS, t, upd):
        v = _terminal(h, cards)
        if v is not None:
            return v
        pl = _PLAYER[h]; k = (pl, cards[pl], h)
        s = strat[k]; u = np.zeros(2)
        for a in (0, 1):
            q = list(pi); q[pl] *= s[a]
            val = walk(cards, _NEXT[h][a], q, strat, dR, dS, t, upd)
            u[a] = val if pl == 0 else -val
        nu = float(s @ u)
        if upd is None or upd == pl:
            dR[k] += pi[1 - pl] * (u - nu)
            dS[k] += (t if linear else 1.0) * pi[pl] * s
        return nu if pl == 0 else -nu

    for t in range(1, iters + 1):
        for upd in ((0, 1) if alternating else (None,)):
            # strategy is FROZEN for the whole pass; updates are applied after it
            strat = {k: _regret_matching(R[k]) for k in KEYS}
            dR = {k: np.zeros(2) for k in KEYS}; dS = {k: np.zeros(2) for k in KEYS}
            for a in CARDS:
                for b in CARDS:
                    if a != b:
                        walk((a, b), "", [1.0, 1.0], strat, dR, dS, t, upd)
            for k in KEYS:
                R[k] = R[k] + dR[k]
                if plus:
                    R[k] = np.maximum(R[k], 0.0)
                S[k] += dS[k]
        if t in cps and callback:
            callback(t, _to_strategy({k: _uniform_if_zero(S[k]) for k in KEYS}))
    return _to_strategy({k: _uniform_if_zero(S[k]) for k in KEYS})


def run_mccfr(iters: int, *, seed: int = 0, init_regret_scale: float = 0.0,
              checkpoints=None, callback=None) -> Strategy:
    """External-sampling MCCFR: sample the deal and the opponent's actions,
    enumerate the traverser's actions. Uniform averaging on opponent nodes."""
    rng = np.random.default_rng(seed)
    R = _init_arrays(None, init_regret_scale, seed + 10_000)
    S = {k: np.zeros(2) for k in KEYS}
    pairs = [(a, b) for a in CARDS for b in CARDS if a != b]
    cps = set(checkpoints or [])

    def walk(cards, h, trav):
        v = _terminal(h, cards)
        if v is not None:
            return v if trav == 0 else -v
        pl = _PLAYER[h]; k = (pl, cards[pl], h)
        s = _regret_matching(R[k])
        if pl == trav:
            u = np.array([walk(cards, _NEXT[h][a], trav) for a in (0, 1)])
            nu = float(s @ u)
            R[k] += u - nu
            return nu
        S[k] += s
        a = int(rng.random() < s[1])
        return walk(cards, _NEXT[h][a], trav)

    for t in range(1, iters + 1):
        for trav in (0, 1):
            walk(pairs[rng.integers(6)], "", trav)
        if t in cps and callback:
            callback(t, _to_strategy({k: _uniform_if_zero(S[k]) for k in KEYS}))
    return _to_strategy({k: _uniform_if_zero(S[k]) for k in KEYS})
