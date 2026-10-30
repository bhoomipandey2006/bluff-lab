"""Exact Kuhn poker engine: payoffs, best response, exploitability.

Cards are 0=J, 1=Q, 2=K. A behavioural strategy for one seat is two arrays of
three probabilities of the aggressive action (bet or call):

    Player 1:  first[c]       = P(bet  | card c, first move)
               after_cb[c]    = P(call | card c, after check-bet)
    Player 2:  after_check[c] = P(bet  | card c, P1 checked)
               after_bet[c]   = P(call | card c, P1 bet)

A full 12-number strategy holds both seats. All payoffs are for Player 1, in
chips, averaged over the 6 equally likely deals. No sampling in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import product

import numpy as np

CARDS = (0, 1, 2)
CARD_NAMES = ("J", "Q", "K")
GAME_VALUE_P1 = -1.0 / 18.0
_PAIRS = [(a, b) for a in CARDS for b in CARDS if a != b]  # the 6 deals


@dataclass(frozen=True)
class Seat1:
    first: np.ndarray
    after_cb: np.ndarray


@dataclass(frozen=True)
class Seat2:
    after_check: np.ndarray
    after_bet: np.ndarray


@dataclass(frozen=True)
class Strategy:
    """Both seats; these are the 12 numbers a person edits in the UI."""
    p1: Seat1
    p2: Seat2

    @staticmethod
    def from_vector(x) -> "Strategy":
        x = np.asarray(x, dtype=float)
        if x.shape != (12,) or not np.all((x >= 0) & (x <= 1)):
            raise ValueError("need 12 probabilities in [0, 1]")
        return Strategy(Seat1(x[0:3].copy(), x[3:6].copy()),
                        Seat2(x[6:9].copy(), x[9:12].copy()))

    def to_vector(self) -> np.ndarray:
        return np.concatenate([self.p1.first, self.p1.after_cb,
                               self.p2.after_check, self.p2.after_bet])


def _w(a: int, b: int) -> int:
    return 1 if a > b else -1


def payoff(s1: Seat1, s2: Seat2) -> float:
    """Exact expected payoff to Player 1."""
    tot = 0.0
    for a, b in _PAIRS:
        w = _w(a, b)
        bet = s1.first[a] * ((1 - s2.after_bet[b]) + s2.after_bet[b] * 2 * w)
        after_cb = (1 - s1.after_cb[a]) * -1 + s1.after_cb[a] * 2 * w
        chk = (1 - s1.first[a]) * ((1 - s2.after_check[b]) * w
                                   + s2.after_check[b] * after_cb)
        tot += bet + chk
    return tot / 6.0


def best_response_p1(s2: Seat2) -> tuple[float, Seat1]:
    """Exact best response of Player 1 to a fixed Player 2 policy."""
    first = np.zeros(3); after_cb = np.zeros(3)
    for a in CARDS:
        opp = [b for b in CARDS if b != a]
        # facing a P2 bet after our check: call iff EV(call) >= EV(fold)
        call = sum(s2.after_check[b] * 2 * _w(a, b) for b in opp)
        fold = sum(s2.after_check[b] * -1 for b in opp)
        after_cb[a] = 1.0 if call >= fold else 0.0
        bet_v = sum((1 - s2.after_bet[b]) + s2.after_bet[b] * 2 * _w(a, b)
                    for b in opp)
        chk_v = sum((1 - s2.after_check[b]) * _w(a, b) for b in opp) + max(call, fold)
        first[a] = 1.0 if bet_v >= chk_v else 0.0
    s1 = Seat1(first, after_cb)
    return payoff(s1, s2), s1


def best_response_p2(s1: Seat1) -> tuple[float, Seat2]:
    """Exact best response of Player 2; returns (payoff to P1, policy)."""
    after_check = np.zeros(3); after_bet = np.zeros(3)
    for b in CARDS:
        opp = [a for a in CARDS if a != b]
        call = sum(s1.first[a] * 2 * _w(a, b) for a in opp)   # P1's payoff
        fold = sum(s1.first[a] * 1 for a in opp)
        after_bet[b] = 1.0 if call <= fold else 0.0          # P2 minimises
        chk = sum((1 - s1.first[a]) * _w(a, b) for a in opp)
        bet = sum((1 - s1.first[a]) * ((1 - s1.after_cb[a]) * -1
                                       + s1.after_cb[a] * 2 * _w(a, b)) for a in opp)
        after_check[b] = 1.0 if bet <= chk else 0.0
    s2 = Seat2(after_check, after_bet)
    return payoff(s1, s2), s2


def nash_conv(s1: Seat1, s2: Seat2) -> float:
    """Sum of both players' best-response gains = BR1(s2) - BR2(s1)."""
    return best_response_p1(s2)[0] - best_response_p2(s1)[0]


def exploitability(s1: Seat1, s2: Seat2) -> float:
    """NashConv / 2 (OpenSpiel's convention). A function of the JOINT policy."""
    return nash_conv(s1, s2) / 2.0


def strategy_exploitability(s: Strategy) -> float:
    return exploitability(s.p1, s.p2)


def all_pure_seat1():
    for v in product((0.0, 1.0), repeat=6):
        yield Seat1(np.array(v[:3]), np.array(v[3:]))


def all_pure_seat2():
    for v in product((0.0, 1.0), repeat=6):
        yield Seat2(np.array(v[:3]), np.array(v[3:]))


def equilibrium(alpha: float) -> Strategy:
    """Hypothesised equilibrium family (verified numerically in tests/).

    P1: bet J w.p. alpha, never bet Q, bet K w.p. 3*alpha; after check-bet call
    K always, Q w.p. alpha+1/3, J never. P2: after check bet K always and J w.p.
    1/3; after bet call K always, Q w.p. 1/3."""
    s1 = Seat1(np.array([alpha, 0.0, 3 * alpha]), np.array([0.0, alpha + 1 / 3, 1.0]))
    s2 = Seat2(np.array([1 / 3, 0.0, 1.0]), np.array([0.0, 1 / 3, 1.0]))
    return Strategy(s1, s2)


def head_to_head(a: Strategy, b: Strategy) -> float:
    """Seat-averaged expected payoff of a against b (chips per hand).

    a sits in seat 1 against b's seat 2, then they swap; the two are averaged.
    Exactly antisymmetric: head_to_head(a, b) == -head_to_head(b, a)."""
    return 0.5 * (payoff(a.p1, b.p2) - payoff(b.p1, a.p2))
