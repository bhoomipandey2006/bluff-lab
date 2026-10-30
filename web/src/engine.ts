// TypeScript port of bluff_lab/game.py and CFR+ (bluff_lab/cfr.py). Same 12-vector order:
// [0-2] P1 first bet J,Q,K | [3-5] P1 call after check-bet | [6-8] P2 bet after check | [9-11] P2 call after bet
export type Half = number[];
export const CARDS = [0, 1, 2];
export const NAMES = ["J", "Q", "K"];
const w = (a: number, b: number) => (a > b ? 1 : -1);
const others = (c: number) => CARDS.filter((x) => x !== c);

export function payoff(p1: Half, p2: Half): number {
  let t = 0;
  for (const a of CARDS) for (const b of others(a)) {
    const x = w(a, b);
    const bet = p1[a] * ((1 - p2[3 + b]) + p2[3 + b] * 2 * x);
    const cb = -(1 - p1[3 + a]) + p1[3 + a] * 2 * x;
    t += bet + (1 - p1[a]) * ((1 - p2[b]) * x + p2[b] * cb);
  }
  return t / 6;
}
export function bestResponseP1(p2: Half): [number, Half] {
  const f = [0, 0, 0], c = [0, 0, 0];
  for (const a of CARDS) {
    let call = 0, fold = 0, bet = 0, chk = 0;
    for (const b of others(a)) {
      call += p2[b] * 2 * w(a, b); fold -= p2[b];
      bet += (1 - p2[3 + b]) + p2[3 + b] * 2 * w(a, b); chk += (1 - p2[b]) * w(a, b);
    }
    c[a] = call >= fold ? 1 : 0; chk += Math.max(call, fold); f[a] = bet >= chk ? 1 : 0;
  }
  const h = [...f, ...c]; return [payoff(h, p2), h];
}
export function bestResponseP2(p1: Half): [number, Half] {
  const ac = [0, 0, 0], ab = [0, 0, 0];
  for (const b of CARDS) {
    let call = 0, fold = 0, chk = 0, bet = 0;
    for (const a of others(b)) {
      call += p1[a] * 2 * w(a, b); fold += p1[a]; chk += (1 - p1[a]) * w(a, b);
      bet += (1 - p1[a]) * (-(1 - p1[3 + a]) + p1[3 + a] * 2 * w(a, b));
    }
    ab[b] = call <= fold ? 1 : 0; ac[b] = bet <= chk ? 1 : 0;
  }
  const h = [...ac, ...ab]; return [payoff(p1, h), h];
}
/** Exploitability = NashConv/2 of a 12-vector played in both seats (joint policy). */
export function exploitability(v: number[]): number {
  const p1 = v.slice(0, 6), p2 = v.slice(6);
  return (bestResponseP1(p2)[0] - bestResponseP2(p1)[0]) / 2;
}
export const equilibrium = (a: number): number[] => [a, 0, 3 * a, 0, a + 1 / 3, 1, 1 / 3, 0, 1, 0, 1 / 3, 1];

// ---- CFR+ (regret floor, alternating updates, linear averaging); strategy frozen per pass ----
const NEXT: Record<string, [string, string]> = { "": ["c", "b"], c: ["cc", "cb"], b: ["bf", "bc"], cb: ["cbf", "cbc"] };
const PL: Record<string, number> = { "": 0, c: 1, b: 1, cb: 0 };
const HI: Record<string, number> = { "": 0, cb: 1, c: 2, b: 3 };
function term(h: string, a: number, b: number): number | null {
  const x = w(a, b);
  switch (h) { case "cc": return x; case "bc": case "cbc": return 2 * x; case "bf": return 1; case "cbf": return -1; }
  return null;
}
const rm = (r: number[]) => { const p = [Math.max(r[0], 0), Math.max(r[1], 0)], s = p[0] + p[1]; return s > 0 ? [p[0] / s, p[1] / s] : [0.5, 0.5]; };

/** initScale > 0 seeds each information set with random regrets in [0, initScale) using Math.random: a SIMULATION, not reproducible. 0 = exact parity with Python. */
export function cfrPlus(iters: number, checkpoints: number[] = [], cb?: (t: number, v: number[]) => void, initScale = 0): number[] {
  const R = Array.from({ length: 12 }, () => [initScale ? Math.random() * initScale : 0, initScale ? Math.random() * initScale : 0]), S = Array.from({ length: 12 }, () => [0, 0]);
  const cps = new Set(checkpoints);
  const avg = () => S.map((s) => { const t = s[0] + s[1]; return t > 0 ? s[1] / t : 0.5; });
  const walk = (a: number, b: number, h: string, p0: number, p1: number, st: number[][], dR: number[][], dS: number[][], t: number, upd: number): number => {
    const tv = term(h, a, b); if (tv !== null) return tv;
    const pl = PL[h], id = HI[h] * 3 + (pl ? b : a), s = st[id], u = [0, 0];
    for (let k = 0; k < 2; k++) {
      const val = walk(a, b, NEXT[h][k as 0 | 1], pl ? p0 : p0 * s[k], pl ? p1 * s[k] : p1, st, dR, dS, t, upd);
      u[k] = pl ? -val : val;
    }
    const nu = s[0] * u[0] + s[1] * u[1];
    if (upd === pl) {
      const opp = pl ? p0 : p1, own = pl ? p1 : p0;
      dR[id][0] += opp * (u[0] - nu); dR[id][1] += opp * (u[1] - nu);
      dS[id][0] += t * own * s[0]; dS[id][1] += t * own * s[1];
    }
    return pl ? -nu : nu;
  };
  for (let t = 1; t <= iters; t++) {
    for (const upd of [0, 1]) {
      const st = R.map(rm), dR = R.map(() => [0, 0]), dS = R.map(() => [0, 0]);
      for (const a of CARDS) for (const b of others(a)) walk(a, b, "", 1, 1, st, dR, dS, t, upd);
      for (let k = 0; k < 12; k++) { R[k][0] = Math.max(R[k][0] + dR[k][0], 0); R[k][1] = Math.max(R[k][1] + dR[k][1], 0); S[k][0] += dS[k][0]; S[k][1] += dS[k][1]; }
    }
    if (cb && cps.has(t)) cb(t, avg());
  }
  return avg();
}
