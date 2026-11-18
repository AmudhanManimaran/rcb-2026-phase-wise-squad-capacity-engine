/* EeSaala Tracker | analytics.js */
(async function () {
  Sidebar.render("analytics");
  await Navbar.render({ eyebrow: "07 · Insights", title: "Analytics" });
  let ph, vn, pl;
  try { [ph, vn, pl] = await Promise.all([API.phases(), API.venues(), API.players()]); } catch (e) { U.showApiError(e); return; }

  // Phase run-rate trend
  const rcb = ph.innings_phases.filter(r => r.batting_side === "RCB");
  const matches = [...new Set(rcb.map(r => r.rcb_match_no))];
  Charts.draw("rrTrend", { type: "line",
    data: { labels: matches.map(n => `M${n}`), datasets: EESAALA.PHASES.map(p => ({ label: EESAALA.PHASE_LABEL[p], borderColor: EESAALA.PHASE_COLOR[p], spanGaps: true,
      backgroundColor: EESAALA.PHASE_COLOR[p], data: matches.map(n => { const r = rcb.find(x => x.rcb_match_no === n && x.phase === p); return r ? r.phase_run_rate : null; }) })) },
    options: { scales: Charts.axes("Runs per over"), plugins: { legend: { position: "bottom" } } } });

  // Outcome distribution
  const cats = [["dots", "Dot balls", "#3a3a42"], ["rotations", "1s, 2s, 3s", "#8d8d97"], ["fours", "Fours", "#c9a24b"], ["sixes", "Sixes", "#ef1b2d"], ["wickets", "Wickets", "#e9e9ee"]];
  const dist = ph.outcome_distribution;
  Charts.draw("distChart", { type: "bar",
    data: { labels: dist.map(d => EESAALA.PHASE_LABEL[d.phase]), datasets: cats.map(([k, l, c]) => ({ label: l, backgroundColor: c, data: dist.map(d => +(100 * d[k] / d.balls).toFixed(1)) })) },
    options: { scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, max: 100, title: { display: true, text: "% of legal balls" } } }, plugins: { legend: { position: "bottom" } } } });

  // Venue chart (venues RCB visited)
  const used = vn.venues.filter(v => v.matches > 0);
  Charts.draw("venueChart", { type: "bar",
    data: { labels: used.map(v => v.venue_code), datasets: [
      ...EESAALA.PHASES.map(p => ({ label: `${p} prior`, stack: "prior", backgroundColor: Charts.hexA(EESAALA.PHASE_COLOR[p], .35), data: used.map(v => v[`prior_${p.toLowerCase()}_runs`]) })),
      ...EESAALA.PHASES.map(p => ({ label: `${p} observed`, stack: "obs", backgroundColor: EESAALA.PHASE_COLOR[p], data: used.map(v => v[`obs_${p.toLowerCase()}`]) })),
    ] },
    options: { scales: { x: { stacked: true, grid: { display: false } }, y: { stacked: true, title: { display: true, text: "Runs (PP + MID + DEATH)" } } },
      plugins: { legend: { position: "bottom", labels: { font: { size: 10 } } } } } });

  // Contribution
  const top = pl.contribution.slice(0, 12);
  Charts.draw("contribChart", { type: "bar",
    data: { labels: top.map(c => c.short_name), datasets: [{ label: "Share of RCB bat runs %", data: top.map(c => c.share_pct),
      backgroundColor: top.map((_, i) => i < 3 ? "#ef1b2d" : i < 6 ? "#a3001a" : "#5c000c") }] },
    options: { indexAxis: "y", scales: { x: { title: { display: true, text: "%" } }, y: { grid: { display: false } } }, plugins: { legend: { display: false } } } });

  // Opponent table
  const teams = [...new Set(vn.opponent_bowling.map(o => o.team_code))];
  const econs = vn.opponent_bowling.map(o => o.econ_vs_rcb);
  const lo = Math.min(...econs), hi = Math.max(...econs);
  const heat = (e) => { const t = hi > lo ? 1 - (e - lo) / (hi - lo) : .5; return `background:rgba(212,0,30,${(0.08 + 0.5 * t).toFixed(2)})`; };
  U.html("#oppTable", `<thead><tr><th>Team</th>${EESAALA.PHASES.map(p => `<th class="num">${p} econ</th>`).join("")}<th class="num">Wkts</th></tr></thead>
    <tbody>${teams.map(t => { const rs = vn.opponent_bowling.filter(o => o.team_code === t); const by = Object.fromEntries(rs.map(r => [r.phase, r]));
      return `<tr><td><span class="dot" style="background:${rs[0].primary_color};box-shadow:none;margin-right:8px"></span><b>${t}</b></td>
      ${EESAALA.PHASES.map(p => by[p] ? `<td class="num" style="${heat(by[p].econ_vs_rcb)}">${U.num(by[p].econ_vs_rcb, 2)}</td>` : "<td>-</td>").join("")}
      <td class="num">${rs.reduce((a, r) => a + r.wickets, 0)}</td></tr>`; }).join("")}</tbody>`);

  U.html("#venueTable", `<thead><tr><th>Venue</th><th class="num">Matches</th><th class="num">Prior par</th><th class="num">Obs 1st inns</th></tr></thead>
    <tbody>${vn.venues.map(v => `<tr><td><b>${v.venue_code}</b> <small class="muted">${U.esc(v.city)}</small></td><td class="num">${v.matches}</td>
    <td class="num">${U.num(v.prior_first_inn_total, 0)}</td><td class="num">${U.num(v.obs_first_innings, 0)}</td></tr>`).join("")}</tbody>`);

  const bowlers = [...new Set(pl.bowling.map(b => b.player_id))];
  U.html("#bowlTable", `<thead><tr><th>Bowler</th>${EESAALA.PHASES.map(p => `<th class="num">${p} overs</th><th class="num">Econ</th><th class="num">Wkts</th>`).join("")}</tr></thead>
    <tbody>${bowlers.map(id => { const rs = pl.bowling.filter(b => b.player_id === id); const by = Object.fromEntries(rs.map(r => [r.phase, r]));
      return `<tr><td><b>${U.esc(rs[0].player_name)}</b></td>${EESAALA.PHASES.map(p => by[p] ? `<td class="num">${U.oversFromBalls(by[p].legal_balls)}</td><td class="num">${U.num(by[p].economy, 2)}</td><td class="num">${by[p].wickets}</td>` : '<td class="num muted">-</td><td class="num muted">-</td><td class="num muted">-</td>').join("")}</tr>`; }).join("")}</tbody>`);
})();
