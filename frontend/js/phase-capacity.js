/* EeSaala Tracker | phase-capacity.js */
(async function () {
  Sidebar.render("capacity");
  await Navbar.render({ eyebrow: "03 · Capacity engine", title: "Phase Capacity", matchSelector: true });

  API.formulas().then(fs => U.html("#formulaList", fs.filter(f => f.number <= 14).map(f => `
    <div class="kv" style="align-items:center;gap:12px"><span><b class="num red">F${String(f.number).padStart(2, "0")}</b> ${U.esc(f.name)}</span>
    <span class="formula" style="font-size:11px">${U.esc(f.expression)}</span></div>`).join(""))).catch(() => {});

  async function load() {
    const mid = Navbar.selectedMatch();
    let c;
    try { c = await API.capacity(mid); } catch (e) { U.showApiError(e); return; }
    const m = Navbar.matchById(mid) || {};
    U.html("#capKpis", [
      ["XI capacity", U.num(c.capacity_total, 1), "adjusted runs in 20 overs", "red"],
      ["Expected wickets", U.num(c.capacity_wickets, 2), "sum of phase E[W]"],
      ["History used", c.history_matches, `completed RCB matches before ${U.date(c.history_cutoff)}`],
      ["Opponent / venue", `${c.opponent.team_code} · ${c.venue.venue_code}`, U.esc(c.venue.venue_name)],
    ].map(([l, v, f, cls]) => `<div class="kpi ${cls || ""}"><div class="kpi-label">${l}</div><div class="kpi-value">${v}</div><div class="kpi-foot">${f}</div></div>`).join(""));
    U.html("#phaseCards", c.capacity.map(PhaseCard.render).join(""));

    // contributions: share * SR/100 * balls
    const players = [...new Map(c.player_profiles.map(p => [p.player_id, p])).values()];
    const balls = { PP: 36, MID: 60, DEATH: 24 };
    Charts.draw("contribChart", {
      type: "bar",
      data: { labels: players.map(p => `${p.batting_order}. ${p.short_name}`),
        datasets: EESAALA.PHASES.map(ph => ({ label: EESAALA.PHASE_LABEL[ph], backgroundColor: EESAALA.PHASE_COLOR[ph],
          data: players.map(p => { const r = c.player_profiles.find(x => x.player_id === p.player_id && x.phase === ph); return r ? +(r.ball_share * r.sr / 100 * balls[ph]).toFixed(2) : 0; }) })) },
      options: { indexAxis: "y", scales: { x: { stacked: true, title: { display: true, text: "Expected runs" } }, y: { stacked: true, grid: { display: false } } },
                 plugins: { legend: { position: "bottom" } } },
    });

    U.$("#venueBadge").textContent = `${c.venue.venue_code} · par ${U.num(c.venue.venue_par, 0)}`;
    U.html("#venueBody", `<div class="table-wrap"><table class="table compact"><thead><tr><th>Phase</th><th class="num">Venue</th><th class="num">League</th><th class="num">VF</th><th class="num">s_p</th><th class="num">n</th></tr></thead>
      <tbody>${c.venue.phases.map(v => `<tr><td>${U.phaseTag(v.phase)}</td><td class="num">${U.num(v.venue_avg, 1)}</td><td class="num">${U.num(v.league_avg, 1)}</td>
      <td class="num">${U.num(v.venue_factor, 3)}</td><td class="num">${U.pct(v.phase_share, 1)}</td><td class="num">${v.sample_innings}</td></tr>`).join("")}</tbody></table></div>`);
    U.$("#oppBadge").textContent = c.opponent.team_name;
    U.html("#oppBody", `<div class="table-wrap"><table class="table compact"><thead><tr><th>Phase</th><th class="num">Opp econ</th><th class="num">League</th><th class="num">Threat</th><th class="num">Overs</th></tr></thead>
      <tbody>${c.opponent.phases.map(o => `<tr><td>${U.phaseTag(o.phase)}</td><td class="num">${U.num(o.opp_econ, 2)}</td><td class="num">${U.num(o.league_econ, 2)}</td>
      <td class="num ${o.opp_threat < 1 ? "red" : "ok"}">${U.num(o.opp_threat, 3)}</td><td class="num">${U.num(o.sample_overs, 1)}</td></tr>`).join("")}</tbody></table></div>
      <p class="small" style="margin-top:10px">Threat below 1.000 means the opponent concedes less than the league in that phase.</p>`);

    U.$("#profileNote").textContent = `Pre-match estimates · k = ${c.params.shrinkage_k} pseudo-balls · half-life ${c.params.half_life_days} days`;
    const rows = players.map(p => {
      const by = Object.fromEntries(c.player_profiles.filter(x => x.player_id === p.player_id).map(x => [x.phase, x]));
      return `<tr><td class="num">${p.batting_order}</td><td><b>${U.esc(p.player_name)}</b> ${p.cold_start ? '<span class="badge gold">Cold start</span>' : ""}</td>
        ${EESAALA.PHASES.map(ph => `<td class="num">${U.num(by[ph].sr, 1)}</td><td class="num muted">${U.num(by[ph].out_prob, 3)}</td><td class="num">${U.pct(by[ph].ball_share, 1)}</td>`).join("")}
        <td class="num">${by.PP.raw_balls + by.MID.raw_balls + by.DEATH.raw_balls}</td></tr>`;
    }).join("");
    U.html("#profileTable", `<thead><tr><th>#</th><th>Player</th>${EESAALA.PHASES.map(ph => `<th class="num">${ph} SR</th><th class="num">Out</th><th class="num">Share</th>`).join("")}<th class="num">Balls seen</th></tr></thead><tbody>${rows}</tbody>`);
  }
  document.addEventListener("matchchange", load);
  load();
})();
