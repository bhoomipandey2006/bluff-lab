# Method

Every figure in this repository is produced by a script in `scripts/` from a fixed seed. Numbers live in `docs/FACTS.md`, which is generated, never hand-edited.

## Game
Kuhn poker: deck J < Q < K, each player antes 1 and gets one card, Player 1 acts first. Twelve information sets, so a strategy is 12 probabilities of the aggressive action (bet or call). Order of the 12-vector used everywhere (Python and, later, TypeScript):

| index | information set | probability of |
|---|---|---|
| 0-2 | P1 first move, card J, Q, K | bet |
| 3-5 | P1 after check-bet, card J, Q, K | call |
| 6-8 | P2 after check, card J, Q, K | bet |
| 9-11 | P2 after bet, card J, Q, K | call |

## Exact quantities (no sampling)
- **Payoff** `payoff(s1, s2)`: expected chips to Player 1, enumerating the 6 equally likely deals and the whole tree (`bluff_lab/game.py`).
- **Best response**: closed-form backward induction per information set (call/fold decisions are made per information set, aggregated over the opponent's cards, not per deal). Verified against brute force over all 2^6 pure strategies.
- **NashConv** = BR1(s2) - BR2(s1), expressed in Player 1's payoff. **Exploitability** = NashConv / 2 (OpenSpiel's convention for two-player zero-sum). Both are functions of the **joint** policy; both seats must be supplied.
- **Seat-averaged head-to-head** `head_to_head(a, b)` = (payoff(a.p1, b.p2) - payoff(b.p1, a.p2)) / 2, exactly antisymmetric.
- **For a single human-entered 12-vector**, "exploitability" is the exploitability of that vector used in both seats, i.e. the average of what a best-responding opponent gains in each seat.

## Equilibrium family (hypothesis, tested numerically)
For alpha in [0, 1/3]: P1 bets J w.p. alpha, never bets Q, bets K w.p. 3 alpha; after check-bet calls K always, Q w.p. alpha + 1/3, J never. P2 after check bets K always, J w.p. 1/3, never Q; after bet calls K always, Q w.p. 1/3, J never. The tests confirm value -1/18 and exploitability < 1e-9 for the alphas tested and positive exploitability just outside the range. The statement "P2's equilibrium is unique" is **not** claimed by this repository; it is only consistent with what the solvers produce.

## Solvers (own implementations, `bluff_lab/cfr.py`)
- **Vanilla CFR**: simultaneous updates, regret matching, uniform averaging weighted by own reach. The strategy is frozen for a whole pass and updates are applied after it.
- **CFR+**: regrets floored at 0, alternating updates, linear averaging (weight t).
- **Alternating vanilla CFR**: as OpenSpiel's `CFRSolver`.
- **External-sampling MCCFR**: sample the deal, enumerate the traverser's actions, sample the opponent's, uniform averaging at opponent nodes. Simulated: results vary with the seed.
- All three CFR variants match OpenSpiel (`tests/test_openspiel.py`) at T = 10, 100, 1000 to relative 1e-6.
- **Initial regrets**: `init_regret_scale` adds uniform[0, scale)^2 regrets per information set before iteration 1. This is the *only* knob used to test where solvers land in the family. Other starting rules (initial strategy, warm starts) may behave differently; this is not explored yet.

## Reproduce
`make test` runs the full suite (needs `pip install -e .[dev]`; the OpenSpiel tests skip if `open_spiel` is absent). `make figures` runs `scripts/experiments.py`, `scripts/field_demo.py`, `scripts/make_figures.py`, `scripts/make_facts.py`.
