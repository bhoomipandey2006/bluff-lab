# Related work (to my knowledge; not exhaustive)

Found in a limited web search on 2026-10-29. This project does not claim novelty; it is an exact, interactive implementation and a tournament format. URLs marked TODO must be filled in and checked by the owner before release.

- labml.ai annotated CFR implementation: https://nn.labml.ai/cfr
- Google DeepMind OpenSpiel (Kuhn and Leduc poker, CFR, external- and outcome-sampling MCCFR, exact exploitability and best response): TODO verify URL. Used here only for cross-checking (`tests/test_openspiel.py`).
- cfrx (JAX CFR): TODO URL. A C implementation of CFR, CFR+, MCCFR and DCFR with Kuhn exploitability: TODO URL. open-pure-cfr: TODO URL. Several hobby repositories with GUIs against CFR bots.
- A course challenge with the same exercise (self-play CFR, plot exploitability, play against checkpoints): TODO URL.
- Prisner, *Game Theory Through Examples*: a class tournament where each student submits a Kuhn robot as a few probabilities.
- Browser-playable CFR bots for other games (a Deep CFR Truco demo) and live bot arenas for Texas Hold'em (dev.fun Heads-Up Ladder).
- "Strength Is Not Soundness: Measuring the Exploitability of LLM Policies in Imperfect-Information Games" (NeurIPS 2026): measures exact exploitability of commercial LLMs on Kuhn poker. Read before any LLM work. TODO URL.
- A survey noting the structure of Kuhn equilibria (one-parameter family for Player 1, unique Player 2 strategy, value -1/18): TODO citation. Here the family is verified numerically, uniqueness is not.
- OpenSpiel issue-tracker gotcha: exploitability is a property of the joint policy; merge both seats first. Followed in `tests/test_openspiel.py`.

Possible gaps tested, not asserted: exact-payoff arena with no sampling luck; instant exact exploitability plus best response for a person's own 12 numbers; an explorer showing the bluff frequency is not unique; all of it in the browser.
