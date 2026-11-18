/* EeSaala Tracker | dashboard.js */
(async function () {
  Sidebar.render("dashboard");
  await Navbar.render({ eyebrow: "01 · Season overview", title: "Dashboard" });
  let d;
  try { d = await API.dashboard(); } catch (e) { U.showApiError(e); return; }

  const s = d.season, run = d.backtest.run || {};
  U.html("#heroStats", [
    ["Record", `${s.wins}-${s.losses}`], ["Points", s.points], ["Avg score", U.num(s.avg_score, 0)], ["Highest", s.highest],
  ].map(([l, v]) => `<div class="hero-stat"><div class="l">${l}</div><div class="v">${v}</div></div>`).join(""));

  const p = d.active_params;
  U.html("#kpis", [
    ["Matches", s.played, "RCB league fixtures", "red"],
    ["MAE at 20 overs", U.num(run.mae_20, 1), "runs, walk-forward", ""],
    ["MAE at 6 overs", U.num(run.mae_6, 1), "runs, powerplay checkpoint", ""],
    ["Checkpoint hit rate", U.pct(run.hit_rate, 0), "within tolerance", ""],
    ["Recency half-life", `${U.num(p.half_life_days, 0)}<span class="unit">days</span>`, `${p.param_set} parameter set`, ""],
    ["Wicket penalty w", U.num(p.wicket_penalty, 1), `target weight &lambda; = ${U.num(p.target_lambda, 2)}`, ""],
  ].map(([l, v, f, cls]) => `<div class="kpi ${cls}"><div class="kpi-label">${l}</div><div class="kpi-value">${v}</div><div class="kpi-foot">${f}</div></div>`).join(""));

  U.html("#resultsStrip", d.matches.map(m => `
    <div class="result-tile ${m.result_code || ""} ${m.is_validation_case ? "val" : ""}" title="IPL #${m.ipl_match_no} · ${U.esc(m.venue_name)} · ${U.esc(m.result_margin || "")}">
      <div class="rt-no">M${m.rcb_match_no}</div>
      <div class="rt-res">${m.result_code || "-"}</div>
      <div class="rt-opp" style="--team:${m.opponent_color === "#1B2133" ? "#9aa3b8" : m.opponent_color}">${m.opponent_code}</div>
      <div class="rt-score">${U.score(m.rcb_runs, m.rcb_wickets)}</div>
    </div>`).join(""));

  // Projected vs actual at 20
  const bm = d.backtest.matches || [];
  Charts.draw("predActualChart", {
    type: "line",
    data: {
      labels: bm.map(m => `M${m.rcb_match_no} ${m.opponent_code}`),
      datasets: [
        { label: "Projected (pre-match)", data: bm.map(m => m.cp20 ? m.cp20.predicted_runs : null), borderColor: "#c9a24b",
          backgroundColor: "#c9a24b", borderDash: [6, 4], pointStyle: "rectRot", pointRadius: 5 },
        { label: "Actual", data: bm.map(m => m.cp20 && m.cp20.evaluable ? m.cp20.actual_runs : null), borderColor: "#ef1b2d",
          backgroundColor: "#ef1b2d", pointRadius: 5, spanGaps: true },
        { label: "Actual (chase completed early)", data: bm.map(m => m.cp20 && !m.cp20.evaluable ? m.cp20.actual_runs : null),
          borderColor: "#5d5d66", backgroundColor: "#5d5d66", showLine: false, pointRadius: 5, pointStyle: "triangle" },
      ],
    },
    options: { scales: { ...Charts.axes("Runs"), y: { suggestedMin: 100, title: { display: true, text: "Runs" } } },
               plugins: { legend: { position: "bottom" } } },
  });

  // Validation card
  const v = d.validation;
  if (v && v.match) {
    const cps = {}; (v.results || []).forEach(r => cps[r.checkpoint_over] = r);
    const pred = v.prediction.prediction;
    U.html("#validationBody", `
      <div class="row between" style="margin-bottom:12px">
        <div><div style="font-family:var(--font-display);font-size:20px">RCB vs ${U.esc(v.match.opponent_code)}</div>
          <div class="small">${U.esc(v.match.venue_name)} · ${U.date(v.match.match_date)} · history: ${pred.history_matches} matches</div></div>
        ${U.classBadge(cps[20] ? cps[20].classification : "")}
      </div>
      <div class="vs-grid">${[6, 16, 20].map(o => { const r = cps[o] || {}; return `
        <div class="vs-cell"><div class="over">OVER ${o}</div>
          <div class="pa"><span class="p">${U.num(r.predicted_runs, 0)}</span><span class="a">${r.evaluable ? r.actual_runs : "-"}</span></div>
          <div class="lbls"><span>Proj</span><span>Actual</span></div>
          <div class="small" style="margin-top:4px">Error ${r.evaluable ? U.signed(r.predicted_runs - r.actual_runs, 1) : "n/a"}</div></div>`; }).join("")}</div>
      <div class="divider"></div>
      <div class="kv"><span>Recommended first-innings target</span><span>${U.num(pred.t_recommended, 0)}</span></div>
      <div class="kv"><span>XI capacity (adjusted)</span><span>${U.num(pred.capacity_total, 1)}</span></div>
      <div class="kv"><span>Bowling strength index</span><span>${U.num(pred.bsi, 3)}</span></div>
      <div class="kv"><span>Actual result</span><span>${U.score(v.match.rcb_runs, v.match.rcb_wickets)} · ${U.esc(v.match.winner)} won</span></div>
      <a class="btn sm" style="margin-top:12px" href="backtesting.html">Open full evaluation</a>`);
  } else {
    U.html("#validationBody", `<div class="empty">Run a backtest to evaluate the validation case.</div>`);
  }

  // Phase averages
  const ph = EESAALA.PHASES;
  const rcbAvg = Object.fromEntries(d.phase_averages.map(r => [r.phase, r.avg_runs]));
  const oppAvg = Object.fromEntries(d.opponent_phase_averages.map(r => [r.phase, r.avg_runs]));
  Charts.draw("phaseAvgChart", {
    type: "bar",
    data: { labels: ph.map(x => EESAALA.PHASE_LABEL[x]),
      datasets: [{ label: "RCB", data: ph.map(x => rcbAvg[x]), backgroundColor: "#ef1b2d" },
                 { label: "Opponents", data: ph.map(x => oppAvg[x]), backgroundColor: "#3a3a42" }] },
    options: { scales: Charts.axes("Runs"), plugins: { legend: { position: "bottom" } } },
  });

  const summ = d.backtest.summary || [];
  Charts.draw("maeChart", {
    type: "bar",
    data: { labels: summ.map(r => `Over ${r.checkpoint_over}`),
      datasets: [{ label: "MAE (runs)", data: summ.map(r => r.mae), backgroundColor: "#c9a24b", yAxisID: "y" },
                 { label: "Hit rate %", data: summ.map(r => r.hit_rate * 100), type: "line", borderColor: "#ef1b2d", backgroundColor: "#ef1b2d", yAxisID: "y1" }] },
    options: { scales: { x: { grid: { display: false } }, y: { beginAtZero: true, title: { display: true, text: "MAE" } },
      y1: { position: "right", min: 0, max: 100, grid: { display: false }, title: { display: true, text: "Hit %" } } },
      plugins: { legend: { position: "bottom" } } },
  });

  U.html("#topBatters", (d.top_batters || []).map((b, i) => `
    <div class="kv" style="padding:10px 0"><span><b class="num" style="color:var(--red-bright);margin-right:10px">${i + 1}</b>${U.esc(b.player_name)}</span>
    <span>${b.runs} <small class="muted">runs · SR ${U.num(b.sr, 1)}</small></span></div>`).join("") || '<div class="empty">No data</div>');
})();
