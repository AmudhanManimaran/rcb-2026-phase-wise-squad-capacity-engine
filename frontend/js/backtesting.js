/* EeSaala Tracker | backtesting.js */
(async function () {
  Sidebar.render("backtest");
  await Navbar.render({ eyebrow: "06 · Validation", title: "Backtesting" });
  let data = null, cp = 20;

  async function load() {
    try { [data] = await Promise.all([API.backtestResults()]); } catch (e) { U.showApiError(e); return; }
    if (!data.run) { U.html("#btKpis", '<div class="empty" style="grid-column:1/-1">No backtest yet. Click Run backtest.</div>'); return; }
    const r = data.run;
    U.html("#btKpis", [
      ["MAE over 20", U.num(r.mae_20, 1), "runs", "red"], ["MAE over 16", U.num(r.mae_16, 1), "runs"], ["MAE over 6", U.num(r.mae_6, 1), "runs"],
      ["MAPE over 20", U.pct(r.mape_20, 1), `bias ${U.signed(r.bias_20, 1)} runs`], ["Hit rate", U.pct(r.hit_rate, 0), "all evaluable checkpoints"],
      ["Validation error", U.num(r.validation_abs_err, 1), `IPL Match 67 · ${r.param_set || ""} params`],
    ].map(([l, v, f, cls]) => `<div class="kpi ${cls || ""}"><div class="kpi-label">${l}</div><div class="kpi-value">${v}</div><div class="kpi-foot">${f}</div></div>`).join(""));

    U.html("#summaryTable", `<thead><tr><th>Checkpoint</th><th class="num">n</th><th class="num">MAE</th><th class="num">MAPE</th><th class="num">Bias</th><th class="num">Hit</th></tr></thead>
      <tbody>${data.summary.map(s => `<tr><td>Over ${s.checkpoint_over}</td><td class="num">${s.evaluated}</td><td class="num">${U.num(s.mae, 1)}</td>
      <td class="num">${U.pct(s.mape, 1)}</td><td class="num">${U.signed(s.bias, 1)}</td><td class="num">${U.pct(s.hit_rate, 0)}</td></tr>`).join("")}</tbody>`);

    const counts = {}; data.matches.forEach(m => counts[m.classification] = (counts[m.classification] || 0) + 1);
    const palette = ["#ef1b2d", "#c9a24b", "#e9e9ee", "#7a0010", "#6aa9ff", "#2fbf71", "#8d8d97", "#e6a23c"];
    Charts.draw("classChart", { type: "doughnut",
      data: { labels: Object.keys(counts), datasets: [{ data: Object.values(counts), backgroundColor: palette, borderColor: "#121215", borderWidth: 3 }] },
      options: { cutout: "62%", plugins: { legend: { position: "right" } } } });

    const cell = (c) => !c ? "<td>-</td>" : `<td class="num ${c.evaluable ? "" : "muted"}">${U.num(c.predicted_runs, 0)} / <b>${c.actual_runs}</b>
      <small class="${c.within_tolerance ? "ok" : c.evaluable ? "red" : "muted"}">${c.evaluable ? U.signed(c.predicted_runs - c.actual_runs, 0) : "n/a"}</small></td>`;
    U.html("#matchTable", `<thead><tr><th>Match</th><th>Date</th><th>Opp</th><th>Venue</th><th>Innings</th><th class="num">Over 6</th><th class="num">Over 16</th><th class="num">Over 20</th><th class="num">Wkts 20</th><th>Classification</th></tr></thead>
      <tbody>${data.matches.map(m => `<tr class="${m.is_validation_case ? "highlight" : ""}"><td><b>M${m.rcb_match_no}</b> <small class="muted">#${m.ipl_match_no}</small>${m.is_validation_case ? ' <span class="badge gold">VAL</span>' : ""}</td>
      <td>${U.date(m.match_date)}</td><td>${m.opponent_code}</td><td>${m.venue_code}</td><td>${m.rcb_batting_first ? "Bat 1st" : "Chase"}</td>
      ${cell(m.cp6)}${cell(m.cp16)}${cell(m.cp20)}<td class="num">${m.cp20 ? `${U.num(m.cp20.predicted_wkts, 1)} / ${m.cp20.actual_wkts}` : "-"}</td><td>${U.classBadge(m.classification)}</td></tr>`).join("")}</tbody>`);

    U.html("#runTable", `<thead><tr><th>Run</th><th>Params</th><th class="num">MAE 6</th><th class="num">MAE 16</th><th class="num">MAE 20</th><th class="num">Hit</th></tr></thead>
      <tbody>${data.runs.map(x => `<tr><td>#${x.backtest_run_id} <small class="muted">${String(x.created_at).slice(0, 16).replace("T", " ")}</small></td><td>${x.param_set || "-"}</td>
      <td class="num">${U.num(x.mae_6, 1)}</td><td class="num">${U.num(x.mae_16, 1)}</td><td class="num">${U.num(x.mae_20, 1)}</td><td class="num">${U.pct(x.hit_rate, 0)}</td></tr>`).join("")}</tbody>`);
    drawChart();
    loadParams();
  }

  function drawChart() {
    const ms = data.matches, key = `cp${cp}`;
    Charts.draw("btChart", { type: "bar",
      data: { labels: ms.map(m => `M${m.rcb_match_no} ${m.opponent_code}`), datasets: [
        { type: "line", label: "Projected", data: ms.map(m => m[key] ? m[key].predicted_runs : null), borderColor: "#c9a24b", backgroundColor: "#c9a24b", borderDash: [6, 4], pointStyle: "rectRot", pointRadius: 5 },
        { label: "Actual", data: ms.map(m => m[key] ? m[key].actual_runs : null),
          backgroundColor: ms.map(m => !m[key] || !m[key].evaluable ? "#3a3a42" : m[key].within_tolerance ? "#ef1b2d" : "#7a0010") },
      ] },
      options: { scales: Charts.axes("Runs"), plugins: { legend: { position: "bottom" },
        tooltip: { callbacks: { afterBody: (items) => { const m = ms[items[0].dataIndex][key]; return m && !m.evaluable ? "Chase finished before this checkpoint" : ""; } } } } } });
  }

  async function loadParams() {
    const ps = await API.parameters();
    U.html("#paramTable", `<thead><tr><th>Set</th><th class="num">Half-life</th><th class="num">k</th><th class="num">&alpha;</th><th class="num">&beta;</th><th class="num">w</th><th class="num">&lambda;</th><th class="num">Objective</th><th></th></tr></thead>
      <tbody>${ps.map(p => `<tr class="${p.is_active ? "highlight" : ""}"><td>#${p.param_id} ${p.param_set}</td><td class="num">${U.num(p.half_life_days, 0)}</td><td class="num">${U.num(p.shrinkage_k, 0)}</td>
      <td class="num">${U.num(p.opp_alpha, 2)}</td><td class="num">${U.num(p.venue_beta, 2)}</td><td class="num">${U.num(p.wicket_penalty, 1)}</td><td class="num">${U.num(p.target_lambda, 2)}</td>
      <td class="num">${U.num(p.objective_mae, 2)}</td><td>${p.is_active ? '<span class="badge solid-red">Active</span>' : `<button class="btn sm" data-activate="${p.param_id}">Activate</button>`}</td></tr>`).join("")}</tbody>`);
    U.$$("[data-activate]").forEach(b => b.addEventListener("click", async () => {
      await API.activateParams(Number(b.dataset.activate)); U.toast("Parameter set activated. Re-run the backtest to apply it.", "success"); loadParams();
    }));
  }

  U.$$("#cpSeg button").forEach(b => b.addEventListener("click", () => {
    U.$$("#cpSeg button").forEach(x => x.classList.remove("on")); b.classList.add("on"); cp = Number(b.dataset.cp); if (data) drawChart(); }));
  U.$("#runBtn").addEventListener("click", e => U.busy(e.currentTarget, async () => {
    try { const r = await API.runBacktest(); U.toast(`Backtest #${r.backtest_run_id}: MAE@20 ${U.num(r.summary.mae_20, 1)}`, "success"); await load(); }
    catch (err) { U.toast(err.message, "error"); } }));
  U.$("#calBtn").addEventListener("click", e => U.busy(e.currentTarget, async () => {
    U.toast("Calibration grid search running (about 30 seconds)");
    try { const r = await API.calibrate(); U.toast(`Calibrated: half-life ${r.best.half_life_days}, k ${r.best.shrinkage_k}. Running backtest...`, "success");
      await API.runBacktest(); await load(); }
    catch (err) { U.toast(err.message, "error"); } }));
  load();
})();
