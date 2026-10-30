"""Draw all figures from figures/results.json and figures/field_demo.json."""
import json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from bluff_lab import Seat1, equilibrium, exploitability

BG, LAV, TEAL, NAVY, ACC = "#F4F4F9", "#B9A6E8", "#5BC0BE", "#1B1F3B", "#FFB86B"
plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "axes.edgecolor": NAVY, "axes.labelcolor": NAVY, "text.color": NAVY, "xtick.color": NAVY,
    "ytick.color": NAVY, "font.size": 12, "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans"})
R = json.loads((ROOT / "figures/results.json").read_text())
F = json.loads((ROOT / "figures/field_demo.json").read_text())
foot = f"commit {R['commit'][:7]}"
def cap(fig, text): fig.text(0.01, 0.005, text + f"  |  {foot}", fontsize=8, color=NAVY, alpha=.8)

# 1. convergence
fig, ax = plt.subplots(figsize=(8, 5))
C = R["convergence"]
for name, col in (("CFR (simultaneous)", LAV), ("CFR (alternating)", NAVY), ("CFR+", TEAL)):
    ax.loglog(C[name]["t"], np.maximum(C[name]["expl"], 1e-12), color=col, lw=1.4, label=name)
mc = C["MCCFR (external sampling)"]; runs = np.array(mc["runs"])
ax.loglog(mc["t"], np.median(runs, 0), color=ACC, lw=2, label="MCCFR median of 10 seeds")
ax.fill_between(mc["t"], runs.min(0), runs.max(0), color=ACC, alpha=.25, lw=0)
for thr in (1e-2, 1e-3): ax.axhline(thr, color=NAVY, lw=.6, ls=":")
ax.set_ylim(1e-6, 1); ax.set_xlabel("iterations"); ax.set_ylabel("exploitability (chips / hand)")
ax.set_title("Exploitability of the average strategy"); ax.legend(frameon=False, fontsize=9)
cap(fig, "Exact exploitability = NashConv/2. CFR up to 20,000 iterations; MCCFR up to 200,000, seeds 0-9.")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / "figures/fig1_convergence.png", dpi=200); plt.close(fig)

# 2. landing positions in the family
fig, ax = plt.subplots(figsize=(8, 4.8))
cfgs = [k for k in R["family"] if "scale=0" not in k]
for i, k in enumerate(cfgs):
    a = np.array([p["alpha"] for p in R["family"][k]])
    ax.scatter(a, np.full(len(a), i) + np.random.default_rng(i).uniform(-.18, .18, len(a)), s=14,
               color=TEAL if "CFR+" in k else LAV if k.startswith("CFR ") else ACC, alpha=.85, lw=0)
for k in R["family"]:
    if "scale=0" in k:
        ax.axvline(R["family"][k][0]["alpha"], color=NAVY, lw=.5, ls=":")
ax.axvspan(0, 1/3, color=LAV, alpha=.12, lw=0)
ax.set_yticks(range(len(cfgs))); ax.set_yticklabels(cfgs, fontsize=8); ax.set_xlim(-.01, 1/3 + .01)
ax.set_xlabel("bluff frequency alpha (P1 bets with J)")
ax.set_title("Where solvers land inside the equilibrium family")
cap(fig, "Shaded: alpha in [0, 1/3]. 40 seeds/row, random initial regrets; approximate equilibria (see FACTS). Dotted: uniform-start runs.")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / "figures/fig2_family_landing.png", dpi=200); plt.close(fig)

# 3. exploitability along alpha, extended past 1/3 (probabilities clipped to [0,1])
al = np.linspace(0, .6, 241); ex = []
eq = equilibrium(1 / 6)
for a in al:
    s1 = Seat1(np.array([a, 0, min(1, 3 * a)]), np.array([0, min(1, a + 1 / 3), 1]))
    ex.append(exploitability(s1, eq.p2))
fig, ax = plt.subplots(figsize=(8, 4.6))
ax.plot(al, ex, color=NAVY, lw=2); ax.axvspan(0, 1/3, color=TEAL, alpha=.15, lw=0)
ax.scatter([1/6], [0], color=ACC, s=60, zorder=5, label="alpha = 1/6")
ax.set_xlabel("alpha of Player 1's strategy"); ax.set_ylabel("exploitability (chips / hand)")
ax.set_title("Zero exploitability across the whole family, then it rises")
ax.legend(frameon=False)
cap(fig, "Exact. P1 = family(alpha) with probabilities clipped to [0,1]; P2 = equilibrium. Computed on a 241-point grid.")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / "figures/fig3_family_exploitability.png", dpi=200); plt.close(fig)

# 4. field matrix
m = F["main"]; M = np.array(m["matrix"]); n = len(m["names"])
fig, ax = plt.subplots(figsize=(8.5, 6.4))
lim = np.abs(M).max()
im = ax.imshow(M, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("x", [LAV, BG, TEAL]), vmin=-lim, vmax=lim)
ax.set_xticks(range(n)); ax.set_yticks(range(n)); ax.set_xticklabels(m["names"], rotation=40, ha="right", fontsize=9)
ax.set_yticklabels(m["names"], fontsize=9)
for i in range(n):
    for j in range(n): ax.text(j, i, f"{M[i,j]:+.2f}", ha="center", va="center", fontsize=8, color=NAVY)
ax.set_title("Exact head-to-head, chips per hand (row vs column)")
cap(fig, "Seat-averaged exact payoffs, no sampling. Hand-written heuristics, not human data. Equilibrium: alpha = 1/6.")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / "figures/fig4_field_matrix.png", dpi=200); plt.close(fig)

# 5. rank by exploitability vs by field payoff
order = np.argsort(m["avg_vs_field"])
fig, ax = plt.subplots(figsize=(8, 4.6))
cols = [ACC if m["names"][i] == "Equilibrium" else TEAL for i in order]
ax.barh([m["names"][i] for i in order], np.array(m["avg_vs_field"])[order], color=cols)
ax.axvline(0, color=NAVY, lw=.8); ax.set_xlabel("average payoff vs the other six (chips / hand)")
ax.set_title("Zero exploitability, but not first")
cap(fig, "Exact. Hand-written field; ranking depends on the field (see FACTS: equilibrium rank over alpha).")
fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(ROOT / "figures/fig5_rank_by_payoff.png", dpi=200); plt.close(fig)
print("figures written")
