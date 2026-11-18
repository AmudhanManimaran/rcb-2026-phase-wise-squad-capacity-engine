/* EeSaala Tracker | navbar.js   Top bar with page title, global match selector and API status. */
const Navbar = (() => {
  let matches = [];

  function selectedMatch() {
    const v = Number(localStorage.getItem(EESAALA.STORAGE_MATCH));
    return Number.isFinite(v) && v > 0 ? v : null;
  }

  async function render({ eyebrow, title, matchSelector = false }) {
    const el = document.getElementById("topbar");
    el.innerHTML = `
      <button class="btn icon ghost menu-btn" id="menuBtn" aria-label="Menu">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M3 12h18M3 18h18"/></svg>
      </button>
      <div class="page-title"><span class="eyebrow">${U.esc(eyebrow)}</span><h1>${U.esc(title)}</h1></div>
      <div class="topbar-right">
        ${matchSelector ? `<select class="select" id="matchSelect" style="min-width:250px" aria-label="Match"></select>` : ""}
        <span class="status-pill" id="apiStatus"><span class="dot"></span>Connecting</span>
      </div>`;
    U.$("#menuBtn").addEventListener("click", () => U.$("#sidebar").classList.toggle("open"));
    health();
    if (matchSelector) await loadMatches();
  }

  async function health() {
    const pill = U.$("#apiStatus");
    try {
      const h = await API.health();
      pill.innerHTML = `<span class="dot ${h.status === "ok" ? "ok" : "bad"}"></span>${h.status === "ok" ? "Engine online" : "Database offline"}`;
    } catch (e) {
      pill.innerHTML = `<span class="dot bad"></span>API offline`;
    }
  }

  async function loadMatches() {
    const sel = U.$("#matchSelect");
    try {
      matches = await API.matches();
    } catch (e) { U.showApiError(e); return; }
    const def = matches.find(m => m.is_validation_case) || matches[matches.length - 1];
    let current = selectedMatch();
    if (!matches.some(m => m.match_id === current)) current = def.match_id;
    sel.innerHTML = matches.map(m => `<option value="${m.match_id}" ${m.match_id === current ? "selected" : ""}>
        M${m.rcb_match_no} · IPL #${m.ipl_match_no} · vs ${m.opponent_code} · ${m.venue_code}${m.is_validation_case ? " · Validation" : ""}</option>`).join("");
    localStorage.setItem(EESAALA.STORAGE_MATCH, current);
    sel.addEventListener("change", () => {
      localStorage.setItem(EESAALA.STORAGE_MATCH, sel.value);
      document.dispatchEvent(new CustomEvent("matchchange", { detail: Number(sel.value) }));
    });
  }

  return { render, selectedMatch, matches: () => matches, matchById: (id) => matches.find(m => m.match_id === id) };
})();
window.Navbar = Navbar;
