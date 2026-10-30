import { describe, expect, it } from "vitest";
import golden from "./golden.json";
import { bestResponseP1, bestResponseP2, cfrPlus, equilibrium, exploitability, payoff } from "../src/engine";

const TOL = 1e-9;
describe("Python <-> TypeScript parity (golden vectors from scripts/golden.py)", () => {
  it("payoff, best responses and exploitability agree to 1e-9", () => {
    for (const c of golden.cases) {
      const p1 = c.v.slice(0, 6), p2 = c.v.slice(6);
      expect(Math.abs(payoff(p1, p2) - c.payoff)).toBeLessThan(TOL);
      expect(Math.abs(bestResponseP1(p2)[0] - c.br1)).toBeLessThan(TOL);
      expect(Math.abs(bestResponseP2(p1)[0] - c.br2)).toBeLessThan(TOL);
      expect(Math.abs(exploitability(c.v) - c.expl)).toBeLessThan(TOL);
    }
  });
  it("CFR+ average strategies agree to 1e-9 at T = 10, 200, 1000", () => {
    for (const [T, want] of Object.entries(golden.cfr_plus)) {
      const got = cfrPlus(Number(T));
      (want as number[]).forEach((x, i) => expect(Math.abs(got[i] - x)).toBeLessThan(TOL));
    }
  });
  it("equilibrium family: exploitability 0 and value -1/18", () => {
    for (const a of [0, 0.1, 1 / 6, 1 / 3]) {
      const v = equilibrium(a);
      expect(exploitability(v)).toBeLessThan(1e-12);
      expect(payoff(v.slice(0, 6), v.slice(6))).toBeCloseTo(-1 / 18, 12);
    }
  });
  it("speed (reported, not a pass/fail claim): exploitability and 10,000 CFR+ iterations", () => {
    let t0 = performance.now(); for (let i = 0; i < 1000; i++) exploitability(golden.cases[i % 40].v);
    const perCall = (performance.now() - t0) / 1000;
    t0 = performance.now(); cfrPlus(10000); const cfrMs = performance.now() - t0;
    console.log(`BENCH node: exploitability ${perCall.toFixed(4)} ms/call, 10000 CFR+ iterations ${cfrMs.toFixed(0)} ms`);
    expect(perCall).toBeLessThan(5);
  });
});
