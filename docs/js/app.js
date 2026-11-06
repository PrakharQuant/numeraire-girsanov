// ---------- shared helpers ----------
const $ = (id) => document.getElementById(id);
const fmt = (x, d = 2) => Number(x).toFixed(d);

function normPdf(x) { return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI); }
// erf-based normal CDF (Abramowitz-Stegun 7.1.26, ~1e-7 accuracy)
function normCdf(x) {
  const s = x >= 0 ? 1 : -1; x = Math.abs(x) / Math.SQRT2;
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - ((((1.061405429 * t - 1.453152027) * t + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return 0.5 * (1 + s * y);
}
function bs(S, K, r, sig, T) {
  const sq = sig * Math.sqrt(T);
  const d1 = (Math.log(S / K) + (r + 0.5 * sig * sig) * T) / sq;
  const d2 = d1 - sq;
  return { d1, d2, Nd1: normCdf(d1), Nd2: normCdf(d2), call: S * normCdf(d1) - K * Math.exp(-r * T) * normCdf(d2) };
}

let DATA = null;
fetch("js/data.json").then(r => r.json()).then(d => { DATA = d; initWidgets(d); })
  .catch(e => console.warn("data.json not loaded; widgets use defaults", e));

// theme toggle
(function () {
  const btn = $("themeBtn");
  const saved = localStorage.getItem("ng-theme");
  if (saved) document.documentElement.dataset.theme = saved;
  else if (matchMedia("(prefers-color-scheme: dark)").matches) document.documentElement.dataset.theme = "dark";
  btn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem("ng-theme", next);
    if (window.__redrawBell) window.__redrawBell();
  });
})();

// ---------- Widget 1: scenario reweighting (Ch.4/5) ----------
function initRewidget(w) {
  const up = $("rwUp"), dn = $("rwDn"), qb = $("rwQ"), K = $("rwK");
  up.value = w.up; dn.value = w.down; qb.value = 50; K.value = 100;
  function draw() {
    const U = +up.value, D = +dn.value, qraw = +qb.value / 100, k = +K.value, S0 = 100;
    // bank chance that makes the stock flat (risk-neutral q) — always used for pricing
    const q = Math.min(0.999, Math.max(0.001, (S0 - D) / (U - D)));
    // stock-numeraire probabilities: p_i' = p_i * S_i / S0
    const pu = q * U / S0, pd = (1 - q) * D / S0;
    $("rwSumNote").textContent = `check: ${fmt(pu)} + ${fmt(pd)} = ${fmt(pu + pd)} (must be 1) · flat q = ${fmt(q)} (slider shows raw belief ${fmt(qraw)} — beliefs don't price anything)`;
    $("rwQBankUp").textContent = fmt(q);
    $("rwQBankDn").textContent = fmt(1 - q);
    $("rwQStockUp").textContent = fmt(pu);
    $("rwQStockDn").textContent = fmt(pd);
    $("rwAvgBank").textContent = fmt(q * U + (1 - q) * D);
    $("rwAvgStock").textContent = fmt(pu * U + pd * D);
    const payoffU = Math.max(U - k, 0), payoffD = Math.max(D - k, 0);
    const bankPrice = q * payoffU + (1 - q) * payoffD;
    const stockPrice = (payoffU / U) * pu * S0 + (payoffD / D) * pd * S0;
    $("rwBankPrice").textContent = fmt(bankPrice);
    $("rwStockPrice").textContent = fmt(stockPrice);
    $("rwMatch").textContent = Math.abs(bankPrice - stockPrice) < 1e-9 ? "✔ identical — price doesn't care which unit you use" : "⚠ differs (should never happen with valid inputs)";
  }
  [up, dn, qb, K].forEach(el => el.addEventListener("input", draw));
  draw();
}

// ---------- Widget 2: bell curve (Ch.6) ----------
function initBell(w) {
  const cv = $("bellCanvas"), ctx = cv.getContext("2d");
  const S = $("blS"), K = $("blK"), r = $("blR"), sg = $("blSig"), T = $("blT");
  S.value = w.S; K.value = w.K; r.value = 0; sg.value = 20; T.value = 1;
  function cssVar(name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
  function draw() {
    const P = bs(+S.value, +K.value, +r.value / 100, +sg.value / 100, +T.value);
    $("blNd2").textContent = fmt(P.Nd2, 3);
    $("blNd1").textContent = fmt(P.Nd1, 3);
    $("blCall").textContent = fmt(P.call, 3);
    $("blD1").textContent = fmt(P.d1, 3);
    $("blD2").textContent = fmt(P.d2, 3);
    const W = cv.width = cv.clientWidth * 2, H = cv.height = 420;
    ctx.clearRect(0, 0, W, H);
    const ink = cssVar("--ink") || "#333", acc = cssVar("--accent") || "#2563eb", acc2 = cssVar("--accent2") || "#7c3aed";
    const lo = -4, hi = 4, xOf = z => (z - lo) / (hi - lo) * W;
    const base = H - 30, scale = H * 0.55;
    function curve(mu, color, dash) {
      ctx.beginPath(); ctx.setLineDash(dash || []);
      for (let px = 0; px <= W; px += 4) {
        const z = lo + px / W * (hi - lo);
        const y = base - normPdf(z - mu) * scale;
        px === 0 ? ctx.moveTo(px, y) : ctx.lineTo(px, y);
      }
      ctx.strokeStyle = color; ctx.lineWidth = 3; ctx.stroke(); ctx.setLineDash([]);
    }
    // shaded N(d2) area under curve centred at m2 (log-price measure, bank numeraire)
    const m2 = ((+r.value / 100) - 0.5 * (+sg.value / 100) ** 2) * (+T.value) / (+sg.value / 100 * Math.sqrt(+T.value));
    const shift = +sg.value / 100 * Math.sqrt(+T.value); // sigma*sqrt(T) in z units
    // fill region right of d2 under the first bell
    ctx.save(); ctx.beginPath();
    for (let px = xOf(P.d2); px <= W; px += 3) {
      const z = lo + px / W * (hi - lo);
      ctx.lineTo(px, base - normPdf(z - m2) * scale);
    }
    ctx.lineTo(W, base); ctx.lineTo(xOf(P.d2), base); ctx.closePath();
    ctx.fillStyle = acc + "44"; ctx.fill(); ctx.restore();
    curve(m2, acc, []);            // bank-measure log-price distribution
    curve(m2 + shift, acc2, [8, 6]); // shifted = stock-measure (N(d1))
    // markers
    ctx.strokeStyle = ink; ctx.lineWidth = 2;
    [[P.d2, acc], [P.d1, acc2]].forEach(([zz, c]) => {
      ctx.beginPath(); ctx.setLineDash([4, 4]); ctx.moveTo(xOf(zz), base); ctx.lineTo(xOf(zz), 20); ctx.strokeStyle = c; ctx.stroke(); ctx.setLineDash([]);
    });
    ctx.font = `${H * 0.05}px sans-serif`; ctx.fillStyle = ink;
    ctx.fillText(`shaded area = N(d₂) = ${fmt(P.Nd2, 3)}`, 12, 24);
    ctx.fillStyle = acc2;
    ctx.fillText(`dashed curve shifted right by σ√T = ${fmt(shift, 2)} → N(d₁) = ${fmt(P.Nd1, 3)}`, 12, 44);
  }
  [S, K, r, sg, T].forEach(el => el.addEventListener("input", draw));
  window.__redrawBell = draw;
  new ResizeObserver(draw).observe(cv);
  draw();
}

function initWidgets(d) {
  try { initRewidget(d.widgets.reweight); } catch (e) { console.error(e); }
  try { initBell(d.widgets.bell); } catch (e) { console.error(e); }
}
