"""Exact round-robin of hand-written heuristics + equilibrium family members.
PREVIEW of the Arena (Milestone 5). The strategies are hand-written by the
developer, NOT human data. Output: figures/field_demo.json"""
import json, sys, itertools
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bluff_lab import Strategy, equilibrium, strategy_exploitability
from bluff_lab.game import head_to_head

HAND = {  # 12 numbers: P1 first[J,Q,K], P1 after_cb[J,Q,K], P2 after_check[J,Q,K], P2 after_bet[J,Q,K]
    "Calling station": [0,0,0, 1,1,1, 0,0,0, 1,1,1],
    "Maniac":          [1]*12,
    "Honest (no bluff)": [0,0,1, 0,1,1, 0,0,1, 0,1,1],
    "Tight-passive":   [0,0,1, 0,0,1, 0,0,1, 0,0,1],
    "Bluff-happy":     [1,0,1, 0,1,1, 1,0,1, 0,1,1],
    "Coin flip":       [.5]*12,
}
def field(alpha):
    f = {"Equilibrium": equilibrium(alpha)}
    f.update({k: Strategy.from_vector(v) for k, v in HAND.items()})
    return f

def analyse(f):
    names = list(f)
    M = np.array([[head_to_head(f[a], f[b]) for b in names] for a in names])
    avg = (M.sum(1)) / (len(names) - 1)
    ex = np.array([strategy_exploitability(f[n]) for n in names])
    order = list(np.argsort(-avg))
    cyc = []
    for i, j, k in itertools.permutations(range(len(names)), 3):
        if i < j and i < k and M[i, j] > 1e-9 and M[j, k] > 1e-9 and M[k, i] > 1e-9:
            cyc.append([names[i], names[j], names[k]])
    return dict(names=names, matrix=M.tolist(), avg_vs_field=avg.tolist(), exploitability=ex.tolist(),
                rank_by_field=[names[i] for i in order], cycles=cyc,
                equilibrium_min_vs_field=float(M[0, 1:].min()))

out = {"main_alpha": 1 / 6, "main": analyse(field(1 / 6)), "robustness": {}}
for a in (0, 0.05, 1 / 6, 0.25, 1 / 3):
    r = analyse(field(a)); out["robustness"][f"{a:.4f}"] = {
        "equilibrium_rank_by_field": r["rank_by_field"].index("Equilibrium") + 1, "n": len(r["names"]),
        "equilibrium_avg": r["avg_vs_field"][0], "top": r["rank_by_field"][0]}
Path("figures").mkdir(exist_ok=True)
Path("figures/field_demo.json").write_text(json.dumps(out, indent=1))
m = out["main"]
for n, a, e in zip(m["names"], m["avg_vs_field"], m["exploitability"]):
    print(f"{n:20s} avg vs field {a:+.4f}   exploitability {e:.4f}")
print("rank by field:", m["rank_by_field"]); print("cycles:", m["cycles"][:5])
print("equilibrium worst result vs any field member:", m["equilibrium_min_vs_field"])
print(json.dumps(out["robustness"], indent=1))
