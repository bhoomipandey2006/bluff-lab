"""Produce every number/figure input for Milestones 1-2 -> figures/results.json.
Run:  python scripts/experiments.py            (about 8 min on 1 CPU)
All randomness is seeded; the git commit and dirty flag are recorded."""
import json, subprocess, sys, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bluff_lab import run_cfr, run_mccfr, strategy_exploitability, payoff, GAME_VALUE_P1

OUT = Path(__file__).resolve().parents[1] / "figures" / "results.json"
git = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True).stdout.strip()
res = {"commit": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain", "--", "bluff_lab")),
       "python": sys.version.split()[0], "numpy": np.__version__}

# ---- A. convergence curves -------------------------------------------------
def geometric(T, step=1.02):
    out, t = set(range(1, 101)), 100.0
    while t < T:
        t *= step; out.add(int(round(t)))
    out.add(T); return sorted(x for x in out if x <= T)

T_CFR, T_MC, N_MC = 20_000, 200_000, 10
conv = {}
for name, kw in {"CFR (simultaneous)": dict(plus=False), "CFR (alternating)": dict(plus=False, alternating=True),
                 "CFR+": dict(plus=True)}.items():
    ts = list(range(1, T_CFR + 1)); ex = []
    t0 = time.time()
    run_cfr(T_CFR, checkpoints=ts, callback=lambda t, s: ex.append(strategy_exploitability(s)), **kw)
    conv[name] = {"t": ts, "expl": ex, "seconds": round(time.time() - t0, 1)}
    print(name, "done", flush=True)
cps = geometric(T_MC)
runs = []
for sd in range(N_MC):
    ex = []
    run_mccfr(T_MC, seed=sd, checkpoints=cps, callback=lambda t, s: ex.append(strategy_exploitability(s)))
    runs.append(ex); print("mccfr seed", sd, flush=True)
conv["MCCFR (external sampling)"] = {"t": cps, "runs": runs, "seeds": list(range(N_MC))}
res["convergence"] = conv

# ---- B. where solvers land in the equilibrium family ----------------------
def landing(run, seeds, scale, **kw):
    pts = []
    for sd in seeds:
        s = run(seed=sd, init_regret_scale=scale, **kw)
        v = s.to_vector()
        pts.append({"seed": sd, "alpha": float(v[0]), "k_bet_minus_3alpha": float(v[2] - 3 * v[0]),
                    "q_call_minus_alpha_plus_third": float(v[4] - (v[0] + 1 / 3)),
                    "expl": float(strategy_exploitability(s)), "value": float(payoff(s.p1, s.p2))})
    return pts
fam = {}
SEEDS = list(range(40))
for scale in (0, 5, 50):
    seeds = [0] if scale == 0 else SEEDS
    fam[f"CFR T=3000 scale={scale}"] = landing(lambda **k: run_cfr(3000, **k), seeds, scale)
    fam[f"CFR+ T=3000 scale={scale}"] = landing(lambda **k: run_cfr(3000, plus=True, **k), seeds, scale)
    fam[f"MCCFR T=50000 scale={scale}"] = landing(lambda **k: run_mccfr(50_000, **k), seeds, scale)
    print("family scale", scale, "done", flush=True)
res["family"] = fam
res["game_value"] = GAME_VALUE_P1
OUT.parent.mkdir(exist_ok=True); OUT.write_text(json.dumps(res))
print("wrote", OUT)
