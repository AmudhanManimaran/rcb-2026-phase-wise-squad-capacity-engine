/* EeSaala Tracker | sidebar.js   Brand mark and primary navigation. */
const Sidebar = (() => {
  const ICONS = {
    dashboard: '<path d="M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z"/>',
    squad: '<path d="M16 11a4 4 0 1 0-8 0M4 21v-1a6 6 0 0 1 6-6h4a6 6 0 0 1 6 6v1"/><circle cx="12" cy="7" r="4"/>',
    capacity: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    planner: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    tracker: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    backtest: '<path d="M9 12l2 2 4-4"/><path d="M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/>',
    analytics: '<path d="M21 12A9 9 0 1 1 12 3v9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
  };
  const ITEMS = [
    ["dashboard", "Dashboard", "dashboard.html"],
    ["squad", "Squad Intelligence", "squad.html"],
    ["capacity", "Phase Capacity", "phase-capacity.html"],
    ["planner", "Target Planner", "target-planner.html"],
    ["tracker", "Match Tracker", "match-tracker.html"],
    ["backtest", "Backtesting", "backtesting.html"],
    ["analytics", "Analytics", "analytics.html"],
  ];
  const MARK = `
  <svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
    <defs>
      <linearGradient id="bmG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ff2a3c"/><stop offset="1" stop-color="#7a0010"/></linearGradient>
      <linearGradient id="bmK" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#1c1c20"/><stop offset="1" stop-color="#050506"/></linearGradient>
    </defs>
    <path d="M32 3l25 8v19c0 15-10.5 25.5-25 31C17.5 55.5 7 45 7 30V11z" fill="url(#bmG)"/>
    <path d="M32 9l19 6v15c0 11.8-8 20.3-19 25-11-4.7-19-13.2-19-25V15z" fill="url(#bmK)"/>
    <path d="M19 37l13-8 13 8M19 44l13-8 13 8" stroke="#ef1b2d" stroke-width="3" fill="none" stroke-linejoin="round"/>
    <text x="32" y="27" text-anchor="middle" font-family="Oswald, Arial Narrow, sans-serif" font-weight="700" font-size="15" fill="#fff" letter-spacing="1">ES</text>
    <circle cx="32" cy="13.5" r="1.8" fill="#c9a24b"/>
  </svg>`;

  function render(active) {
    const el = document.getElementById("sidebar");
    if (!el) return;
    el.innerHTML = `
      <a class="brand" href="../index.html" style="text-decoration:none;color:inherit">
        ${MARK}
        <div class="brand-text">
          <div class="brand-name">EeSaala<span> Tracker</span></div>
          <div class="brand-sub">RCB Phase Intelligence</div>
        </div>
      </a>
      <div class="nav-label">Modules</div>
      <nav class="nav">
        ${ITEMS.map(([key, label, href], i) => `
          <a href="${href}" class="${key === active ? "active" : ""}">
            <svg class="nav-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONS[key]}</svg>
            ${label}<span class="nav-num">0${i + 1}</span>
          </a>`).join("")}
      </nav>
      <div class="sidebar-foot">
        <div class="motto">Ee Sala Cup <b>Namde</b></div>
        <div style="margin-top:6px">IPL 2026</div>
        <div><a href="${EESAALA.API_BASE || ""}/docs" target="_blank" rel="noopener">API documentation</a></div>
      </div>`;
  }
  return { render, MARK };
})();
window.Sidebar = Sidebar;
