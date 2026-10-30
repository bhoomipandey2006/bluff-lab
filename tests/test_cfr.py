import numpy as np
import pytest
from bluff_lab import GAME_VALUE_P1, payoff, run_cfr, run_mccfr, strategy_exploitability


def curve(run, ts, **kw):
    out = []
    run(max(ts), checkpoints=ts, callback=lambda t, s: out.append(strategy_exploitability(s)), **kw)
    return np.array(out)


def check_decreasing(c, ts):
    slope = np.polyfit(np.log(ts), np.log(c), 1)[0]
    assert slope < -0.3, slope          # clearly decreasing on log-log axes
    assert c[-1] < c[0] / 5


TS = [10, 30, 100, 300, 1000]


def test_cfr_converges():
    c = curve(run_cfr, TS); check_decreasing(c, TS)


def test_cfr_plus_converges():
    c = curve(run_cfr, TS, plus=True); check_decreasing(c, TS)


def test_mccfr_converges_on_average_over_seeds():
    ts = [100, 300, 1000, 3000, 10000]
    c = np.mean([curve(run_mccfr, ts, seed=s) for s in range(5)], axis=0)
    check_decreasing(c, ts)


def test_cfr_value_close_to_minus_one_eighteenth():
    s = run_cfr(5000)
    assert payoff(s.p1, s.p2) == pytest.approx(GAME_VALUE_P1, abs=1e-3)


def test_outputs_are_probabilities_and_seeded():
    for run in (lambda: run_cfr(200), lambda: run_cfr(200, plus=True),
                lambda: run_mccfr(2000, seed=3), lambda: run_cfr(200, init_regret_scale=5, seed=4)):
        v = run().to_vector()
        assert v.shape == (12,) and np.all(v >= 0) and np.all(v <= 1)
    assert np.array_equal(run_mccfr(500, seed=9).to_vector(), run_mccfr(500, seed=9).to_vector())
