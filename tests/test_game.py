import numpy as np
import pytest
from bluff_lab import (GAME_VALUE_P1, Seat1, Strategy, best_response_p1,
                       best_response_p2, equilibrium, exploitability, payoff,
                       strategy_exploitability)
from bluff_lab.game import all_pure_seat1, all_pure_seat2, head_to_head

ALPHAS = [0, 0.05, 1 / 6, 0.25, 1 / 3]


def rand_strategy(rng):
    return Strategy.from_vector(rng.random(12))


@pytest.mark.parametrize("a", ALPHAS)
def test_equilibrium_value_and_exploitability(a):
    s = equilibrium(a)
    assert payoff(s.p1, s.p2) == pytest.approx(GAME_VALUE_P1, abs=1e-9)
    assert strategy_exploitability(s) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("a", [0.34, 0.4, 0.5, 0.9])
def test_outside_family_is_exploitable(a):
    # alpha > 1/3: bet-with-K saturates at 1, Q-call prob = alpha+1/3 (still <= 1)
    s1 = Seat1(np.array([a, 0, min(1, 3 * a)]), np.array([0, min(1, a + 1 / 3), 1]))
    s2 = equilibrium(1 / 6).p2
    assert exploitability(s1, s2) > 1e-4


def test_best_response_matches_bruteforce():
    rng = np.random.default_rng(123)
    for _ in range(200):
        s = rand_strategy(rng)
        bf1 = max(payoff(p, s.p2) for p in all_pure_seat1())
        bf2 = min(payoff(s.p1, p) for p in all_pure_seat2())
        assert best_response_p1(s.p2)[0] == pytest.approx(bf1, abs=1e-12)
        assert best_response_p2(s.p1)[0] == pytest.approx(bf2, abs=1e-12)


def test_equilibrium_guarantees_game_value_against_anyone():
    rng = np.random.default_rng(7)
    eq = equilibrium(0.2)
    for _ in range(500):
        s = rand_strategy(rng)
        assert payoff(eq.p1, s.p2) >= GAME_VALUE_P1 - 1e-12      # seat 1 floor
        assert payoff(s.p1, eq.p2) <= GAME_VALUE_P1 + 1e-12      # seat 2 floor


def test_exploitability_nonnegative_fuzz():
    rng = np.random.default_rng(1)
    for _ in range(500):
        assert strategy_exploitability(rand_strategy(rng)) >= -1e-12


def test_head_to_head_antisymmetric_and_nash_never_loses():
    rng = np.random.default_rng(2)
    eq = equilibrium(1 / 6)
    for _ in range(200):
        a, b = rand_strategy(rng), rand_strategy(rng)
        assert head_to_head(a, b) == pytest.approx(-head_to_head(b, a), abs=1e-12)
        assert head_to_head(eq, a) >= -1e-12
    assert head_to_head(eq, eq) == pytest.approx(0, abs=1e-12)


def test_invalid_vectors_rejected():
    with pytest.raises(ValueError):
        Strategy.from_vector([0.5] * 11)
    with pytest.raises(ValueError):
        Strategy.from_vector([1.1] + [0.5] * 11)
