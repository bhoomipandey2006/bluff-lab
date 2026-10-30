# Bluff Lab

**How beatable is your poker strategy? Not "how did it do last night", but exactly how many chips a perfect opponent would take from it.**

Bluff Lab is a small poker laboratory built on Kuhn poker: three cards (Jack, Queen, King), one round of betting. It is the smallest poker game that still has bluffing in it, and small enough that a computer can solve it exactly instead of estimating. You write down a strategy as twelve numbers, and the lab tells you precisely how much it leaks, shows you the counter-strategy that exploits it, lets you watch a solver learn to bluff, and ranks strategies against each other with no luck involved.

## What you can do

| Screen         | What happens                                                                                                                                                                                                                                                                                                                                       |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Exploit me** | Twelve sliders, one per situation (how often do you bet or call with each card?). A perfect opponent's winnings from you appear instantly, in chips per 100 hands, along with the exact counter-strategy and your single biggest leak. Presets: never bluffs, maniac, calling station, coin flip, equilibrium. A share card downloads as an image. |
| **Solver lab** | Watch CFR+ teach itself to play, with exploitability dropping on a log chart and a meter showing how often it bluffs as it learns.                                                                                                                                                                                                                 |
| **Play**       | Real hands against opponents trained for 10, 100, 1,000 and 10,000 iterations, with a chip bankroll. After each hand you see the opponent's exact exploitability.                                                                                                                                                                                  |
| **Arena**      | Submit a nickname and your twelve numbers. The server scores every pair exactly (no dice, every possible deal) and ranks you two ways: by exploitability and by average payoff against the field. Full head-to-head matrix included.                                                                                                               |
| **Family**     | Slide the first player's bluff rate and watch exploitability stay at zero from 0 up to one third, then rise. Or start 40 solvers from random points and see where they land.                                                                                                                                                                       |
| **Learn**      | The rules, regret matching, exploitability and why bluffing appears, in two minutes.                                                                                                                                                                                                                                                               |

## What you find when you play with it

**There is no single correct bluff rate.** With its worst card, the first player can bluff anywhere from 0% to one third of the time and still be unexploitable, as long as the rest of the strategy moves with it (the King is bet three times as often as the Jack is bluffed). Checked exactly at points across the range, not simulated. Past one third the King bet would have to exceed 100%, so the strategy becomes exploitable.

**The unbeatable player doesn't win tournaments.** In an exact round-robin of seven strategies (an equilibrium player plus six I wrote by hand), the equilibrium player at bluff rate 1/6 finishes third, and across the five bluff rates tested it never finishes first. The winner is a simple player who never bluffs, and who is exploitable for 16.7 chips per 100 hands. Perfect play can't be beaten, but it also can't punish opponents who aren't trying to beat it. Payoff measures the field; exploitability measures the strategy. (The six rivals are hand-written strategies, not human data. The script is `scripts/field_demo.py`.)

**Moving first is a disadvantage.** With perfect play from both sides the first player loses 1/18 of a chip per hand, about 5.6 chips per 100.

## How it works

- A **strategy** is twelve probabilities: for each of three cards, how often you bet on the first move, call after checking and being bet into, bet after the first player checks, and call a bet.
- **Exploitability** is how much a best-responding opponent gains against the strategy. It is computed exactly by walking all six deals and the whole game tree, and reported as NashConv / 2 (OpenSpiel's convention) in chips per hand.
- **Solvers** (written from scratch in `bluff_lab/cfr.py`): vanilla CFR, CFR+, and external-sampling MCCFR. They improve by regret matching: after each deal, shift probability toward the options you regret not choosing, then average your play over time.
- **Checked three ways.** The Python engine is compared against Google DeepMind's OpenSpiel (exploitability, payoff, and all three CFR variants), against brute force over every pure strategy, and against a TypeScript port that must match to 1e-9 on golden test vectors.
- **A bug the checks caught.** My first CFR updated regrets in the middle of an iteration, so later deals saw a half-updated strategy. The OpenSpiel comparison flagged it (exploitability 0.0065 against 0.00094 at 1,000 iterations). I fixed the code, not the test.

## Run it

You need Python 3.11+ and Node 20+.

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install numpy pytest matplotlib ruff fastapi httpx uvicorn
pip install -e .
python -m pytest -q          # the OpenSpiel comparisons skip on native Windows
```

**Mac / Linux**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest -q          # includes the OpenSpiel comparisons
```

**The app** (two terminals; the second is only needed for the Arena)

```bash
cd web && npm install && npm test && npm run dev     # http://localhost:5173
uvicorn server.app:app --port 8000                   # from the repo root, venv active
```

## What's in the repo

| Path                | What                                                                                                   |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| `bluff_lab/game.py` | Exact engine: payoff, best response, exploitability, equilibrium family, head-to-head                  |
| `bluff_lab/cfr.py`  | CFR, CFR+, external-sampling MCCFR                                                                     |
| `web/`              | The app (TypeScript + Vite) and its parity tests                                                       |
| `server/app.py`     | Arena API (FastAPI + SQLite): takes twelve numbers, recomputes everything itself, never runs user code |
| `scripts/`          | Experiments, figures, golden vectors, and the generator for `docs/FACTS.md`                            |
| `docs/FACTS.md`     | Every number quoted anywhere, with the script, seed and commit that produced it                        |
| `docs/METHOD.md`    | Definitions, conventions, exactly how each figure is made                                              |
| `docs/LAUNCH.md`    | Deploying the site and the Arena                                                                       |
| `docs/SECURITY.md`  | Review of the Arena server                                                                             |

## Credits

CFR on Kuhn poker is a classic exercise, and this project stands on a lot of prior work, listed in [docs/RELATED_WORK.md](docs/RELATED_WORK.md). OpenSpiel is used only to cross-check, never copied from. MIT licensed, see [LICENSE](LICENSE); citation details in [CITATION.cff](CITATION.cff).

_Scope: Kuhn poker is a toy game, and the equilibrium facts above are well known. What's new here is the exact, interactive way to see them and a tournament format with no luck in it._
