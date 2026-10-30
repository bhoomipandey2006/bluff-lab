import { NAMES, bestResponseP1, bestResponseP2, cfrPlus, equilibrium, exploitability, payoff } from "./engine";

const $ = <T extends HTMLElement>(s: string) => document.querySelector(s) as T;
const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
const _HEART = `<svg viewBox="0 0 7 6" shape-rendering="crispEdges"><path d="M1 0h2v1h-2zM4 0h2v1h-2zM0 1h7v2h-7zM1 3h5v1h-5zM2 4h3v1h-3zM3 5h1v1h-1z"/></svg>`;
const PK = "#111111", PK2 = "#BEB8AD", CREAM = "#F6F4EE";

// ---------- navigation ----------
const SCREENS = ["home", "exploit", "solver", "play", "arena", "family", "learn"];
function go(id: string) {
  document.querySelectorAll(".screen").forEach((s) => s.classList.toggle("on", s.id === id));
  document.querySelectorAll<HTMLElement>("nav [data-go]").forEach((b) => { const on = b.dataset.go === id; b.classList.toggle("on", on); on ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current"); });
  history.replaceState(null, "", id === "home" ? location.pathname : "#" + id); scrollTo(0, 0);
}
document.querySelectorAll<HTMLElement>("[data-go]").forEach((b) => b.addEventListener("click", () => go(b.dataset.go!)));
addEventListener("keydown", (e) => {
  if (["INPUT", "SELECT"].includes((e.target as HTMLElement).tagName)) return;
  const m: Record<string, string> = { "1": "exploit", "2": "solver", "3": "play", "4": "arena", "5": "family", "6": "learn", Escape: "home" }; if (m[e.key]) go(m[e.key]);
});
function burst() { /* intentionally quiet */ }

// ---------- bankroll hearts (HUD) ----------
let bank = 10;
function hud() { const n = Math.max(0, Math.min(10, bank)); $("#hearts").innerHTML = `CHIPS <div class="bar"><i style="width:${n * 10}%"></i></div> \u00d7${bank}`; }
hud();

// ---------- Exploit me ----------
const GROUPS = [
  { t: "You move first: chance to BET", s: "You move first", n: 0 }, { t: "You checked and the opponent bet: chance to CALL", s: "You face a bet after checking", n: 3 },
  { t: "Opponent moves second, you checked: chance to BET", s: "Opponent after your check", n: 6 }, { t: "Opponent faces your bet: chance to CALL", s: "Opponent facing your bet", n: 9 },
];
const LABEL = (i: number) => `${GROUPS[Math.floor(i / 3)].s}, holding ${NAMES[i % 3]}`;
const v: number[] = [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1];
const PRESETS: [string, number[]][] = [["never bluffs", [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]], ["maniac", Array(12).fill(1)], ["calling station", [0, 0, 0, 1, 1, 1, 0, 0, 0, 1, 1, 1]], ["coin flip", Array(12).fill(0.5)], ["equilibrium", equilibrium(1 / 6)]];
const sl = $("#sliders"); const cap = (t: string) => t;
GROUPS.forEach((g) => {
  sl.insertAdjacentHTML("beforeend", `<div class="grp">${cap(g.t)}</div>`);
  for (let c = 0; c < 3; c++) { const i = g.n + c; sl.insertAdjacentHTML("beforeend", `<div class="row"><label for="s${i}">holding ${NAMES[c]}</label><input id="s${i}" type="range" min="0" max="1" step="0.01" value="${v[i]}" style="--p:${v[i] * 100}%"><output id="o${i}">${v[i].toFixed(2)}</output></div>`); }
});
$("#meter").innerHTML = "<i></i>";
$("#presets").innerHTML = PRESETS.map(([n], k) => `<button data-p="${k}">${n}</button>`).join("");
let leakText = "", per100 = 0, wasSafe = false;
function update() {
  const t0 = performance.now(), e = exploitability(v); per100 = e * 100;
  document.querySelectorAll<HTMLElement>("[data-p]").forEach((b) => { const on = PRESETS[+b.dataset.p!][1].every((x, i) => Math.abs(x - v[i]) < 1e-9); b.classList.toggle("on", on); b.setAttribute("aria-pressed", String(on)); });
  $("#expl100").textContent = per100.toFixed(1);
  ($("#meter i") as HTMLElement).style.width = Math.min(100, (per100 / 34) * 100) + "%";
  
  const safe = per100 < 0.5; $("#badge").textContent = safe ? "UNEXPLOITABLE" : ""; if (safe && !wasSafe) burst(); wasSafe = safe;
  let best = { i: 0, drop: -1, to: 0 };
  for (let i = 0; i < 12; i++) for (const a of [0, 1 / 6, 1 / 3]) { const w = v.slice(); w[i] = equilibrium(a)[i]; const d = e - exploitability(w); if (d > best.drop) best = { i, drop: d, to: w[i] }; }
  leakText = safe ? "Nobody can meaningfully exploit this strategy." : `Biggest leak: ${LABEL(best.i)} (you set ${v[best.i].toFixed(2)}). Setting only that to ${best.to.toFixed(2)} cuts your loss from ${per100.toFixed(1)} to ${((e - best.drop) * 100).toFixed(1)} per 100 hands.`;
  $("#leak").textContent = leakText;
  $("#expl1").textContent = `Exploitability ${e.toFixed(4)} chips/hand (NashConv/2), exact, computed in ${(performance.now() - t0).toFixed(2)} ms.`;
  const br = [...bestResponseP1(v.slice(6))[1], ...bestResponseP2(v.slice(0, 6))[1]];
  $("#br").innerHTML = `<table><tr><th>your number &rarr; exploiter's</th>${NAMES.map((n) => `<th>${n}</th>`).join("")}</tr>` + GROUPS.map((g) => `<tr><td>${g.s}</td>${[0, 1, 2].map((c) => { const i = g.n + c; return `<td class="${Math.abs(br[i] - v[i]) > 0.5 ? "hit" : ""}">${v[i].toFixed(2)} &rarr; ${br[i]}</td>`; }).join("")}</tr>`).join("") + "</table>";
}
function setV(a: number[]) { a.forEach((x, i) => { v[i] = x; ($(`#s${i}`) as HTMLInputElement).value = String(x); $(`#s${i}`).style.setProperty("--p", x * 100 + "%"); $(`#o${i}`).textContent = x.toFixed(2); }); update(); }
for (let i = 0; i < 12; i++) $(`#s${i}`).addEventListener("input", (ev) => { v[i] = +(ev.target as HTMLInputElement).value; (ev.target as HTMLElement).style.setProperty("--p", v[i] * 100 + "%"); $(`#o${i}`).textContent = v[i].toFixed(2); update(); });
document.querySelectorAll<HTMLElement>("[data-p]").forEach((b) => b.addEventListener("click", () => setV(PRESETS[+b.dataset.p!][1])));
$("#card").addEventListener("click", () => {
  const c = document.createElement("canvas"); c.width = 1200; c.height = 630; const g = c.getContext("2d")!, F = "'Zen Kaku Gothic New', system-ui, sans-serif";
  g.fillStyle = CREAM; g.fillRect(0, 0, 1200, 630); g.fillStyle = "#777"; g.font = `500 20px ${F}`; g.fillText("B L U F F   L A B   /   K U H N   P O K E R", 70, 90);
  g.fillStyle = PK; g.font = `300 150px ${F}`; g.fillText(per100.toFixed(1), 66, 270);
  g.font = `300 30px ${F}`; g.fillText("chips lost per 100 hands to a perfect opponent", 70, 330);
  g.fillStyle = PK2; g.fillRect(70, 360, 60, 2); g.fillStyle = PK; g.font = `400 24px ${F}`;
  leakText.match(/.{1,62}(\s|$)/g)?.slice(0, 3).forEach((l, k) => g.fillText(l.trim(), 70, 410 + k * 36));
  g.fillStyle = "#777"; g.font = `400 18px ${F}`; g.fillText("exact exploitability, no sampling", 70, 590);
  const a = document.createElement("a"); a.download = "bluff-lab-card.png"; a.href = c.toDataURL("image/png"); a.click();
});
update();

// ---------- bots (checkpoints) + Solver lab ----------
const CK = [10, 100, 1000, 10000]; const bots: Record<number, number[]> = {};
cfrPlus(10000, CK, (t, s) => { bots[t] = s; });
const logTicks = (max: number) => { const o: number[] = []; for (let t = 1; t <= max; t = Math.ceil(t * 1.05) + (t < 20 ? 1 : 0)) o.push(t); o.push(max); return [...new Set(o)]; };
let anim = 0;
$("#run").addEventListener("click", () => {
  cancelAnimationFrame(anim);
  const N = +($("#iters") as HTMLSelectElement).value, ts = logTicks(N), pts: [number, number, number][] = [];
  cfrPlus(N, ts, (t, s) => pts.push([t, Math.max(exploitability(s), 1e-9), s[0]]));
  const cv = $("#chart") as HTMLCanvasElement, g = cv.getContext("2d")!;
  const X = (t: number) => 60 + (Math.log10(t) / Math.log10(N)) * 640, Y = (e: number) => 20 + (-Math.log10(e) / 6) * 300;
  const frame = (k: number) => {
    g.clearRect(0, 0, cv.width, cv.height); g.font = "11px system-ui, sans-serif"; g.lineWidth = 1;
    for (let j = 0; j <= 6; j++) { const y = Y(10 ** -j); g.globalAlpha = 1; g.strokeStyle = PK2; g.beginPath(); g.moveTo(60, y); g.lineTo(700, y); g.stroke(); g.globalAlpha = 1; g.fillStyle = "#777"; g.fillText(`1e-${j}`, 6, y + 4); }
    g.strokeStyle = PK; g.lineWidth = 2; g.beginPath(); pts.slice(0, k + 1).forEach(([t, e], i) => (i ? g.lineTo(X(t), Y(e)) : g.moveTo(X(t), Y(e)))); g.stroke();
    const [t, e, j] = pts[k]; g.fillStyle = PK; g.beginPath(); g.arc(X(t), Y(e), 5, 0, 7); g.fill();
    g.fillStyle = "#777"; g.fillText("iterations (log)", 320, 365); g.fillText("1", 56, 345); g.fillText(String(N), 676, 345);
    $("#needle").style.left = `calc(${Math.min(j, 1) * 100}% - 4px)`;
    $("#live").textContent = `iteration ${t} | exploitability ${e.toExponential(2)} | bluff frequency ${(j * 100).toFixed(1)}%`;
  };
  let k = 0; const per = Math.max(1, Math.ceil(pts.length / 150));
  const tick = () => { k = Math.min(pts.length - 1, k + per); frame(k); if (k < pts.length - 1) anim = requestAnimationFrame(tick); };
  if (reduce) frame(pts.length - 1); else tick();
  const last = pts[pts.length - 1];
  $("#chartcap").textContent = `CFR+ (alternating, linear averaging), ${N} iterations, deterministic uniform start. Exploitability of the average strategy, chips/hand, log-log.`;
  $("#bluff").innerHTML = `Final: exploitability <b>${last[1].toExponential(2)}</b>, bluff frequency <b>${(last[2] * 100).toFixed(1)}%</b>. Any value from 0% to 33.3% (shaded zone) can belong to an exact equilibrium, so where the solver lands depends on where it starts.`;
});
($("#run") as HTMLButtonElement).click();

// ---------- Play ----------
type Hand = { you: number; bot: number; seat: 0 | 1; h: string; done: boolean; log: string[] };
let hand: Hand | null = null, net = 0, played = 0, jHands = 0, jBets = 0;
const NXT: Record<string, [string, string]> = { "": ["c", "b"], c: ["cc", "cb"], b: ["bf", "bc"], cb: ["cbf", "cbc"] };
const HI: Record<string, number> = { "": 0, cb: 1, c: 2, b: 3 }; const turn = (h: string) => (h === "" || h === "cb" ? 0 : 1);
const outcome = (h: string, a: number, b: number) => { const x = a > b ? 1 : -1; return ({ cc: x, bc: 2 * x, cbc: 2 * x, bf: 1, cbf: -1 } as Record<string, number>)[h]; };
const ck = () => +($("#ckpt") as HTMLSelectElement).value;
const res = (H: Hand) => outcome(H.h, H.seat === 0 ? H.you : H.bot, H.seat === 0 ? H.bot : H.you);
function step() {
  const H = hand!; let r = res(H);
  while (r === undefined && turn(H.h) !== H.seat) {
    const facing = H.h === "b" || H.h === "cb", aggr = Math.random() < bots[ck()][HI[H.h] * 3 + H.bot] ? 1 : 0;
    if (H.bot === 0 && !facing) { jHands++; jBets += aggr; }
    H.log.push(facing ? (aggr ? "BOT calls" : "BOT folds") : aggr ? "BOT bets 1" : "BOT checks"); H.h = NXT[H.h][aggr]; r = res(H);
  }
  if (r !== undefined) {
    const mine = H.seat === 0 ? r : -r; net += mine; played++; bank = Math.max(0, bank + mine); H.done = true; hud();
    render(bank === 0 ? "Out of chips. Press Deal to start again." : mine > 0 ? `+${mine} chip${mine > 1 ? "s" : ""}! Bot held ${NAMES[H.bot]}.` : `${mine} chip${mine < -1 ? "s" : ""}. Bot held ${NAMES[H.bot]}.`, mine > 0 ? "win" : "lose");
    if (mine > 0) burst(); return;
  }
  render("", "");
}
function render(msg: string, cls: string) {
  const H = hand!, facing = H.h === "b" || H.h === "cb", t = $("#table"); t.className = "panel " + cls;
  const opts = H.done ? "" : facing ? `<button class="pill" data-a="0">Fold</button> <button class="pill solid" data-a="1">Call</button>` : `<button class="pill" data-a="0">Check</button> <button class="pill solid" data-a="1">Bet 1</button>`;
  t.innerHTML = `<div class="cards"><div class="cd me">${NAMES[H.you]}</div><span>you, Player ${H.seat + 1}</span><div class="cd ${H.done ? "" : "hide"}">${H.done ? NAMES[H.bot] : "?"}</div><span>opponent (${ck()})</span></div><div class="note">${H.log.join(" > ") || "your move"}</div>${opts}<p>${msg}</p>`;
  t.querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { const a = +(b as HTMLElement).dataset.a!; const f = H.h === "b" || H.h === "cb"; H.log.push(f ? (a ? "you call" : "you fold") : a ? "you bet 1" : "you check"); H.h = NXT[H.h][a]; step(); }));
  $("#tally").textContent = `${played} hands, you ${net >= 0 ? "+" : ""}${net} chips. This opponent's exact exploitability: ${exploitability(bots[ck()]).toExponential(2)} chips/hand.` + (jHands ? ` Observed: it bet a Jack ${jBets} of ${jHands} times when it could.` : "");
}
$("#deal").addEventListener("click", () => {
  if (bank === 0) { bank = 10; net = 0; played = 0; jHands = jBets = 0; hud(); }
  const you = Math.floor(Math.random() * 3); let b = Math.floor(Math.random() * 3); while (b === you) b = Math.floor(Math.random() * 3);
  hand = { you, bot: b, seat: Math.random() < 0.5 ? 0 : 1, h: "", done: false, log: [] }; step();
});
$("#ckpt").addEventListener("change", () => { net = played = jHands = jBets = 0; bank = 10; hud(); hand = null; $("#table").innerHTML = ""; $("#tally").textContent = "Switched opponent. Bankroll reset."; });

// ---------- Arena ----------
const API = ((import.meta as unknown as { env?: { VITE_API?: string } }).env?.VITE_API) ?? "";
type Entry = { id: number; nickname: string; house?: boolean; exploitability: number; avg_payoff: number };
const esc = (x: string) => x.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]!);
async function refresh() {
  $("#lbExp").innerHTML = `<p class="note">loading... the free server sleeps when idle, so the first load can take a minute.</p>`;
  try {
    const r = await fetch(`${API}/api/leaderboard`); const d: { entries: Entry[]; matrix: { names: string[]; values: number[][] } | null } = await r.json();
    const tbl = (rows: Entry[], f: (e: Entry) => string, h: string) => rows.length ? `<table><tr><th>#</th><th>name</th><th>${h}</th></tr>${rows.map((e, i) => `<tr><td>${i + 1}</td><td>${esc(e.nickname)}</td><td>${f(e)}</td></tr>`).join("")}</table>` : `<p class="note">No entries yet. Be the first.</p>`;
    $("#lbExp").innerHTML = tbl([...d.entries].sort((a, b) => a.exploitability - b.exploitability), (e) => (e.exploitability * 100).toFixed(2) + " chips / 100 hands", "exploitability");
    $("#lbPay").innerHTML = tbl([...d.entries].sort((a, b) => b.avg_payoff - a.avg_payoff), (e) => (e.avg_payoff >= 0 ? "+" : "") + (e.avg_payoff * 100).toFixed(2) + " chips / 100 hands", "average payoff");
    const m = d.matrix; $("#matrix").innerHTML = m ? `<div class="wrap"><table><tr><th></th>${m.names.map((n) => `<th>${esc(n)}</th>`).join("")}</tr>${m.values.map((row, i) => `<tr><td>${esc(m.names[i])}</td>${row.map((x) => `<td>${x.toFixed(3)}</td>`).join("")}</tr>`).join("")}</table></div>` : `<p class="note">Matrix appears with 2 to 30 entries.</p>`;
  } catch { $("#lbExp").innerHTML = `<p class="note">The arena server is not running. Start it with: uvicorn server.app:app --port 8000</p>`; }
}
$("#submit").addEventListener("click", async () => {
  const msg = $("#subMsg"); msg.textContent = "sending...";
  try {
    const r = await fetch(`${API}/api/submit`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nickname: ($("#nick") as HTMLInputElement).value, v }) });
    msg.textContent = r.ok ? "submitted" : r.status === 409 ? "that nickname is taken" : r.status === 429 ? "slow down, try again in a minute" : "rejected: check the nickname (letters, numbers, _ -, max 20)"; if (r.ok) refresh();
  } catch { msg.textContent = "server not reachable"; }
});
document.querySelectorAll<HTMLElement>('[data-go="arena"]').forEach((b) => b.addEventListener("click", refresh));

const startHash = location.hash.slice(1); if (SCREENS.includes(startHash)) go(startHash);

// ---------- Family explorer ----------
const famVec = (a: number) => [a, 0, Math.min(1, 3 * a), 0, Math.min(1, a + 1 / 3), 1, 1 / 3, 0, 1, 0, 1 / 3, 1];
const alpha = $("#alpha") as HTMLInputElement;
function famUpdate() {
  const a = +alpha.value; alpha.style.setProperty("--p", (a / 0.6) * 100 + "%"); $("#aout").textContent = a.toFixed(3);
  const e = exploitability(famVec(a)) * 100; $("#afx").textContent = e < 1e-6 ? "0.0" : e.toFixed(1);
  $("#atxt").textContent = a <= 1 / 3 + 1e-9 ? `Inside the family. First move: bet Jack ${a.toFixed(2)}, King ${(3 * a).toFixed(2)}. Facing a bet after checking, call with Queen ${(a + 1 / 3).toFixed(2)}. Exploitability is exactly zero.`
    : "Past one third the King bet would have to go above 100%, which is impossible, so the strategy becomes exploitable.";
}
alpha.addEventListener("input", famUpdate); famUpdate();
$("#aload").addEventListener("click", () => { setV(famVec(+alpha.value)); go("exploit"); });
$("#arun").addEventListener("click", () => {
  $("#astat").textContent = "running..."; const trk = $("#track"); trk.querySelectorAll("i").forEach((n) => n.remove());
  setTimeout(() => {
    const res: [number, number][] = [];
    for (let k = 0; k < 40; k++) { const s = cfrPlus(3000, [], undefined, 5); res.push([s[0], exploitability(s)]); }
    res.forEach(([a]) => { const d = document.createElement("i"); d.style.left = Math.min(100, (a / 0.4) * 100) + "%"; d.style.top = 20 + Math.random() * 60 + "%"; trk.appendChild(d); });
    const as = res.map((r) => r[0]).sort((x, y) => x - y), worst = Math.max(...res.map((r) => r[1]));
    $("#astat").textContent = `min ${as[0].toFixed(3)}, median ${as[20].toFixed(3)}, max ${as[39].toFixed(3)}, worst exploitability ${worst.toExponential(1)}`;
    $("#acap").textContent = "Simulated: 40 runs of CFR+, 3000 iterations each, random initial regrets in [0, 5), Math.random so it changes every click. The shaded zone is the exact family, 0 to one third. Runs are near-equilibria, so a few can sit a hair outside it.";
  }, 30);
});
// ---------- Learn ----------
const eqv = equilibrium(1 / 6); $("#lnValue").textContent = Math.abs(payoff(eqv.slice(0, 6), eqv.slice(6)) * 100).toFixed(1);
const NEVER = [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 1]; $("#lnHonest").textContent = (exploitability(NEVER) * 100).toFixed(1);
$("#lnTry").addEventListener("click", () => { setV(NEVER); go("exploit"); });
