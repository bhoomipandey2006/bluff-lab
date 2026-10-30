"""Golden vectors for Python<->TypeScript parity. Output: web/test/golden.json"""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bluff_lab import Strategy, best_response_p1, best_response_p2, equilibrium, payoff, run_cfr, strategy_exploitability

rng = np.random.default_rng(2026)
cases = []
vs = [rng.random(12) for _ in range(40)] + [equilibrium(a).to_vector() for a in (0, 1/6, 1/3)] \
     + [np.array(x, float) for x in ([0]*12, [1]*12, [.5]*12)]
for v in vs:
    s = Strategy.from_vector(v)
    cases.append({"v": v.tolist(), "payoff": payoff(s.p1, s.p2), "expl": strategy_exploitability(s),
                  "br1": best_response_p1(s.p2)[0], "br2": best_response_p2(s.p1)[0]})
cfr = {str(T): run_cfr(T, plus=True).to_vector().tolist() for T in (10, 200, 1000)}
Path("web/test/golden.json").write_text(json.dumps({"cases": cases, "cfr_plus": cfr}))
print(len(cases), "cases")
