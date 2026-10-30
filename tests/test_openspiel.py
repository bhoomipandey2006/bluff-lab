"""Cross-check exact exploitability, payoff and CFR against OpenSpiel.
Gotcha: exploitability needs the JOINT policy; both seats are merged here."""
import numpy as np
import pytest

pyspiel = pytest.importorskip("pyspiel")
from open_spiel.python import policy as ospolicy
from open_spiel.python.algorithms import cfr as oscfr
from open_spiel.python.algorithms import exploitability as osexpl
from open_spiel.python.algorithms import expected_game_score

from bluff_lab import Strategy, equilibrium, payoff, run_cfr, strategy_exploitability

GAME = pyspiel.load_game("kuhn_poker")


def to_openspiel(s: Strategy):
    pol = ospolicy.TabularPolicy(GAME)
    for card in range(3):
        for key, p in ((f"{card}", s.p1.first[card]), (f"{card}pb", s.p1.after_cb[card]),
                       (f"{card}p", s.p2.after_check[card]), (f"{card}b", s.p2.after_bet[card])):
            # player 1's info states are "<card>p" / "<card>b"; player 0's are "<card>" / "<card>pb"
            pass
    for card in range(3):
        for st, p in ((f"{card}", s.p1.first[card]), (f"{card}pb", s.p1.after_cb[card])):
            pol.policy_for_key(st)[:] = [1 - p, p]
        for st, p in ((f"{card}p", s.p2.after_check[card]), (f"{card}b", s.p2.after_bet[card])):
            pol.policy_for_key(st)[:] = [1 - p, p]
    return pol


def test_random_strategies_match_openspiel_exploitability_and_value():
    rng = np.random.default_rng(0)
    for _ in range(25):
        s = Strategy.from_vector(rng.random(12))
        pol = to_openspiel(s)
        assert strategy_exploitability(s) == pytest.approx(osexpl.exploitability(GAME, pol), abs=1e-9)
        v = expected_game_score.policy_value(GAME.new_initial_state(), [pol, pol])[0]
        assert payoff(s.p1, s.p2) == pytest.approx(v, abs=1e-9)


def test_equilibrium_family_is_zero_exploitability_in_openspiel():
    for a in (0, 0.1, 1 / 3):
        assert osexpl.exploitability(GAME, to_openspiel(equilibrium(a))) == pytest.approx(0, abs=1e-9)


# (mine kwargs, OpenSpiel flags). OpenSpiel's CFRSolver is the ALTERNATING variant;
# the simultaneous textbook variant is built from its private base class.
CONFIGS = {
    "simultaneous": (dict(plus=False), dict(alternating_updates=False, linear_averaging=False, regret_matching_plus=False)),
    "alternating": (dict(plus=False, alternating=True), dict(alternating_updates=True, linear_averaging=False, regret_matching_plus=False)),
    "cfr_plus": (dict(plus=True), dict(alternating_updates=True, linear_averaging=True, regret_matching_plus=True)),
}


@pytest.mark.parametrize("name", list(CONFIGS))
@pytest.mark.parametrize("T", [10, 100, 1000])
def test_cfr_variants_match_openspiel(name, T):
    mine_kw, os_kw = CONFIGS[name]
    solver = oscfr._CFRSolver(GAME, **os_kw)
    for _ in range(T):
        solver.evaluate_and_update_policy()
    ref = osexpl.exploitability(GAME, solver.average_policy())
    mine = strategy_exploitability(run_cfr(T, **mine_kw))
    assert mine == pytest.approx(ref, rel=1e-6, abs=1e-9)
