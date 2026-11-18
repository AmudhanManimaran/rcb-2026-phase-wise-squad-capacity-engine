/* EeSaala Tracker | utils.js   Formatting and DOM helpers. */
const U = {
  $(sel, root = document) { return root.querySelector(sel); },
  $$(sel, root = document) { return [...root.querySelectorAll(sel)]; },
  esc(v) { return String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); },
  num(v, d = 0) { if (v === null || v === undefined || Number.isNaN(Number(v))) return "-"; return Number(v).toFixed(d); },
  pct(v, d = 0) { if (v === null || v === undefined) return "-"; return (Number(v) * 100).toFixed(d) + "%"; },
  signed(v, d = 0) { if (v === null || v === undefined) return "-"; const n = Number(v); return (n > 0 ? "+" : "") + n.toFixed(d); },
  date(s) { if (!s) return "-"; const d = new Date(s + "T00:00:00"); return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" }); },
  initials(name) { return String(name).split(/\s+/).map(w => w[0]).join("").slice(0, 2).toUpperCase(); },
  score(r, w) { return r === null || r === undefined ? "-" : `${r}/${w}`; },
  oversFromBalls(b) { return b === null || b === undefined ? "-" : `${Math.floor(b / 6)}.${b % 6}`; },
  html(el, markup) { if (typeof el === "string") el = U.$(el); if (el) el.innerHTML = markup; return el; },
  setText(sel, v) { const el = U.$(sel); if (el) el.textContent = v; },
  statusBadge(s) {
    const map = { AHEAD: "ok", ON_TRACK: "gold", BEHIND: "warn", CRITICAL: "bad" };
    return `<span class="badge ${map[s] || ""}">${U.esc(String(s).replace("_", " "))}</span>`;
  },
  riskBadge(r) { const m = { LOW: "ok", MEDIUM: "warn", HIGH: "bad" }; return `<span class="badge ${m[r] || ""}">${U.esc(r)}</span>`; },
  classBadge(c) {
    if (!c) return "";
    const tone = /Accurate/.test(c) ? "ok" : /Over-performance/.test(c) ? "info" : /Chase/.test(c) ? "gold" : /Moderate/.test(c) ? "warn" : "bad";
    return `<span class="badge ${tone}">${U.esc(c)}</span>`;
  },
  roleBadge(role) { const m = { BAT: "Batter", WK: "Keeper", AR: "All-rounder", BOWL: "Bowler" }; return `<span class="badge">${m[role] || role}</span>`; },
  phaseTag(p) { return `<span class="phase-tag ${p}">${p}</span>`; },
  toast(msg, type = "info") {
    let box = U.$("#toasts");
    if (!box) { box = document.createElement("div"); box.id = "toasts"; box.className = "toasts"; document.body.appendChild(box); }
    const t = document.createElement("div");
    t.className = `toast ${type}`; t.textContent = msg; box.appendChild(t);
    setTimeout(() => { t.style.opacity = "0"; t.style.transition = "opacity .3s"; setTimeout(() => t.remove(), 300); }, 4200);
  },
  async busy(btn, fn) {
    const label = btn.innerHTML; btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> Working`;
    try { return await fn(); } finally { btn.disabled = false; btn.innerHTML = label; }
  },
  showApiError(err) {
    const box = U.$("#apiError"); if (!box) return;
    box.classList.add("show");
    box.innerHTML = `<b>Backend unavailable.</b> ${U.esc(err.message || err)}<br>
      Start the API with <code>uvicorn backend.main:app --reload</code> from the project root and make sure PostgreSQL is running
      (API base: <code>${U.esc(EESAALA.API_BASE || location.origin)}</code>).`;
  },
};
window.U = U;
