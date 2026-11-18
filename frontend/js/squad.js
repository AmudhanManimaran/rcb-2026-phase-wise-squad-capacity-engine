/* EeSaala Tracker | squad.js */
(async function () {
  Sidebar.render("squad");
  await Navbar.render({ eyebrow: "02 · Personnel", title: "RCB Squad Intelligence", matchSelector: true });
  let squad = null, role = "ALL", xiOnly = false, query = "";

  async function load() {
    try { squad = await API.squad(Navbar.selectedMatch()); } catch (e) { U.showApiError(e); return; }
    const ps = squad.players;
    const m = Navbar.matchById(squad.as_of_match_id);
    U.html("#squadKpis", [
      ["Squad size", ps.length, `${ps.filter(p => p.is_overseas).length} overseas`],
      ["Profiles as of", `M${squad.as_of_rcb_match_no}`, m ? `before RCB vs ${m.opponent_code}, ${U.date(m.match_date)}` : ""],
      ["Recency half-life", `${U.num(squad.half_life_days, 0)}<span class="unit">days</span>`, "w = 2^(-age / half-life)"],
      ["Cold-start players", ps.filter(p => p.cold_start).length, "no 2026 balls faced before this match"],
    ].map(([l, v, f], i) => `<div class="kpi ${i === 0 ? "red" : ""}"><div class="kpi-label">${l}</div><div class="kpi-value">${v}</div><div class="kpi-foot">${f}</div></div>`).join(""));
    render();
  }

  function render() {
    if (!squad) return;
    const list = squad.players
      .filter(p => role === "ALL" || p.role === role)
      .filter(p => !xiOnly || p.in_xi_for_match)
      .filter(p => !query || p.player_name.toLowerCase().includes(query))
      .sort((a, b) => (b.in_xi_for_match - a.in_xi_for_match) || (a.preferred_slot - b.preferred_slot) || (b.runs - a.runs));
    U.html("#squadGrid", list.map(p => PlayerCard.render(p)).join("") || '<div class="empty" style="grid-column:1/-1">No players match the filter.</div>');
    U.$$(".player-card").forEach(c => c.addEventListener("click", () => openPlayer(Number(c.dataset.player))));
  }

  async function openPlayer(id) {
    U.$("#overlay").classList.add("open"); U.$("#drawer").classList.add("open");
    U.html("#drawerBody", '<div class="skeleton" style="height:400px"></div>');
    let d;
    try { d = await API.player(id); } catch (e) { U.toast(e.message, "error"); return; }
    const p = d.player;
    U.html("#drawerBody", `
      <div class="row" style="gap:16px;margin-bottom:18px">
        <div class="avatar" style="width:64px;height:64px;font-size:24px">${U.initials(p.player_name)}</div>
        <div><h2>${U.esc(p.player_name)}${p.is_captain ? ' <span class="gold">(C)</span>' : ""}</h2>
          <div class="row" style="margin-top:6px">${U.roleBadge(p.role)}${p.is_overseas ? '<span class="badge info">Overseas</span>' : ""}
          <span class="badge">${U.esc(p.batting_style)}</span>${p.bowling_style ? `<span class="badge">${U.esc(p.bowling_style)}</span>` : ""}
          <span class="badge gold">Synthetic profile</span></div></div>
      </div>
      <div class="card" style="margin-bottom:16px">
        <div class="card-head"><h3>Phase SR trajectory (pre-match estimates)</h3><span class="small">half-life ${U.num(d.half_life_days, 0)} days</span></div>
        <div class="chart-box sm"><canvas id="formChart"></canvas></div>
      </div>
      <div class="grid g-2" style="margin-bottom:16px">
        <div class="card"><div class="card-head"><h3>Priors</h3></div>
          ${EESAALA.PHASES.map(ph => `<div class="kv"><span>${EESAALA.PHASE_LABEL[ph]} SR / OutProb</span><span>${U.num(p["prior_sr_" + ph.toLowerCase()], 0)} / ${U.num(p["prior_out_" + ph.toLowerCase()], 3)}</span></div>`).join("")}
          ${EESAALA.PHASES.map(ph => p["prior_econ_" + ph.toLowerCase()] ? `<div class="kv"><span>${EESAALA.PHASE_LABEL[ph]} economy prior</span><span>${U.num(p["prior_econ_" + ph.toLowerCase()], 2)}</span></div>` : "").join("")}
        </div>
        <div class="card"><div class="card-head"><h3>Season by phase</h3></div>
          ${d.phase_stats.length ? d.phase_stats.map(s => `<div class="kv"><span>${U.phaseTag(s.phase)} ${s.balls_faced} balls</span><span>${s.runs} runs · SR ${U.num(s.strike_rate, 1)}</span></div>`).join("") : '<div class="small">Has not batted in 2026.</div>'}
          ${d.bowling_phase_stats.map(s => `<div class="kv"><span>${U.phaseTag(s.phase)} bowling</span><span>${s.wickets} wkts · econ ${U.num(s.economy, 2)}</span></div>`).join("")}
        </div>
      </div>
      <div class="card"><div class="card-head"><h3>Match log</h3></div>
        <div class="table-wrap"><table class="table">
          <thead><tr><th>Match</th><th>Opp</th><th>Role</th><th class="num">Runs</th><th class="num">Balls</th><th class="num">SR</th></tr></thead>
          <tbody>${d.innings.map(r => `<tr><td>M${r.rcb_match_no}</td><td>${r.opponent_code}</td>
            <td>${r.is_impact_player ? '<span class="badge gold">Impact</span>' : `#${r.batting_order}`}</td>
            <td class="num">${r.balls ? r.runs + (r.dismissed ? "" : "*") : "-"}</td><td class="num">${r.balls || "-"}</td>
            <td class="num">${r.balls ? U.num(100 * r.runs / r.balls, 1) : "-"}</td></tr>`).join("") || '<tr><td colspan="6" class="muted">Not selected in 2026.</td></tr>'}</tbody>
        </table></div>
      </div>`);
    Charts.draw("formChart", {
      type: "line",
      data: { labels: d.form.map(f => `M${f.rcb_match_no}`),
        datasets: EESAALA.PHASES.map(ph => ({ label: EESAALA.PHASE_LABEL[ph], data: d.form.map(f => f["sr_" + ph.toLowerCase()]),
          borderColor: EESAALA.PHASE_COLOR[ph], backgroundColor: EESAALA.PHASE_COLOR[ph], pointRadius: 2 })) },
      options: { scales: { x: { grid: { display: false } }, y: { title: { display: true, text: "Strike rate" } } }, plugins: { legend: { position: "bottom" } } },
    });
  }

  const close = () => { U.$("#overlay").classList.remove("open"); U.$("#drawer").classList.remove("open"); };
  U.$("#overlay").addEventListener("click", close);
  U.$("#drawerClose").addEventListener("click", close);
  document.addEventListener("keydown", e => { if (e.key === "Escape") close(); });
  U.$$("#roleSeg button").forEach(b => b.addEventListener("click", () => {
    U.$$("#roleSeg button").forEach(x => x.classList.remove("on")); b.classList.add("on"); role = b.dataset.role; render(); }));
  U.$$("#xiSeg button").forEach(b => b.addEventListener("click", () => {
    U.$$("#xiSeg button").forEach(x => x.classList.remove("on")); b.classList.add("on"); xiOnly = b.dataset.xi === "xi"; render(); }));
  U.$("#search").addEventListener("input", e => { query = e.target.value.trim().toLowerCase(); render(); });
  document.addEventListener("matchchange", load);
  load();
})();
