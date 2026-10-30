# Bluff Lab

Kuhn poker is the smallest interesting poker game: 3 cards, one bet. Small enough to solve exactly, so this project measures *exactly* how much a perfect opponent would take from any strategy you write down (its "exploitability").
It ships an exact engine (Python and TypeScript, checked against each other to 1e-9 and against OpenSpiel), CFR / CFR+ / MCCFR solvers, a browser app, and an arena that ranks strategies with no luck involved.

```bash
pip install -e ".[dev]" && python -m pytest -q          # engine, solvers, parity, arena
cd web && npm install && npm test && npm run dev        # the app
```
Arena server and deployment: [docs/LAUNCH.md](docs/LAUNCH.md). Every number quoted anywhere must appear in [docs/FACTS.md](docs/FACTS.md). Method: [docs/METHOD.md](docs/METHOD.md). Prior work, credited: [docs/RELATED_WORK.md](docs/RELATED_WORK.md). Security notes: [docs/SECURITY.md](docs/SECURITY.md).

## Honest limitations
- Kuhn poker is a toy game. Nothing here says anything about real poker or trading strategies.
- This is an exact, interactive implementation and a tournament format, not new theory. The equilibrium family is known; here it is verified numerically at sampled points, not proven.
- "Where solvers land" results are simulations and depend on the initialization rule (see METHOD.md).
- The UI has not been tested on all browsers or phones. The arena has not seen real traffic.
