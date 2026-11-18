/* EeSaala Tracker | match-tracker.js */
(async function () {
  Sidebar.render("tracker");
  await Navbar.render({ eyebrow: "05 · Tracking", title: "Match Tracker", matchSelector: true });
  let replay = null, timer = null;

  function recTableShort(recs) {
    if (!recs || !recs.length) return '<tbody><tr><td class="muted">Innings complete.</td></tr></tbody>';
    return `<thead><tr><th>Phase</th><th class="num">Extra</th><th class="num">Revised</th><th class="num">Req RR</th><th>Risk</th></tr></thead>
      <tbody>${recs.map(r => `<tr class="${r.is_primary ? "highlight" : ""}"><td>${U.phaseTag(r.phase)}</td>
      <td class="num ${r.extra_runs > 0 ? "red" : "ok"}">${U.signed(r.extra_runs, 1)}</td><td class="num">${U.num(r.revised_runs, 1)}</td>
      <td class="num">${U.num(r.required_rr, 2)}</td><td>${U.riskBadge(r.risk_level)}</td></tr>`).join("")}</tbody>`;
  }

  function recTable(recs) {
    if (!recs || !recs.length) return '<tbody><tr><td class="muted">Innings complete or no state yet.</td></tr></tbody>';
    return `<thead><tr><th>Phase</th><th class="num">Balls left</th><th class="num">Planned</th><th class="num">Extra</th><th class="num">Revised</th>
      <th class="num">Req RR</th><th class="num">Capacity RR</th><th class="num">Eff</th><th>Risk</th></tr></thead>
      <tbody>${recs.map(r => `<tr class="${r.is_primary ? "highlight" : ""}"><td>${U.phaseTag(r.phase)} ${r.is_primary ? '<span class="badge solid-red">Focus</span>' : ""}</td>
      <td class="num">${r.balls_remaining}</td><td class="num">${U.num(r.planned_runs, 1)}</td><td class="num ${r.extra_runs > 0 ? "red" : "ok"}">${U.signed(r.extra_runs, 1)}</td>
      <td class="num">${U.num(r.revised_runs, 1)}</td><td class="num">${U.num(r.required_rr, 2)}</td><td class="num">${U.num(r.capacity_rr, 2)}</td>
      <td class="num muted">${U.num(r.efficiency, 1)}</td><td>${U.riskBadge(r.risk_level)}</td></tr>`).join("")}</tbody>`;
  }

  function renderState(s) {
    U.$("#scRuns").textContent = `${s.runs}/${s.wickets}`;
    U.$("#scOvers").textContent = `${s.overs ?? s.overs_text} overs · ${EESAALA.PHASE_LABEL[s.current_phase]}`;
    U.html("#scMeta", [["Plan at this point", U.num(s.expected_runs, 1)], ["Deficit", U.signed(s.deficit, 1)], ["Projected total", U.num(s.projected_total, 0)]]
      .map(([l, v]) => `<div class="kpi" style="padding:10px 12px"><div class="kpi-label">${l}</div><div class="kpi-value" style="font-size:22px">${v}</div></div>`).join(""));
    const b = U.$("#statusBanner"); b.className = `status-banner ${s.status}`;
    U.html(b, `<span class="sb-status">${String(s.status).replace("_", " ")}</span><span class="sb-msg">${U.esc(s.message || "")}</span>`);
    U.html("#recTable", recTable(s.recommendations));
  }

  async function loadHistory(mid) {
    const t = await API.tracker(mid);
    U.html("#history", t.history.length ? `<div class="table-wrap"><table class="table compact"><thead><tr><th>Overs</th><th class="num">Score</th><th class="num">Plan</th><th class="num">Deficit</th><th>Status</th></tr></thead>
      <tbody>${t.history.slice().reverse().map(h => `<tr><td>${h.overs_text}</td><td class="num">${h.runs}/${h.wickets}</td><td class="num">${U.num(h.expected_runs, 0)}</td>
      <td class="num">${U.signed(h.deficit, 1)}</td><td>${U.statusBadge(h.status)}</td></tr>`).join("")}</tbody></table></div>` : '<div class="empty">No updates recorded for this match.</div>');
    if (t.latest) {
      try { renderState(await API.trackerRecommendation(mid)); } catch { /* ignore */ }
    }
  }

  async function load() {
    const mid = Navbar.selectedMatch();
    stop();
    try {
      const saved = await API.savedPlan(mid).catch(() => null);
      U.$("#planBadge").textContent = saved ? `${saved.prediction.plan_mode.replace("_", " ")} · target ${U.num(saved.prediction.plan_target, 0)} · #${saved.prediction.prediction_id}` : "Plan created on first update";
      await loadHistory(mid);
      replay = await API.trackerReplay(mid);
      const sl = U.$("#replaySlider"); sl.max = replay.states.length; sl.value = Math.min(6, replay.states.length);
      drawReplay();
    } catch (e) { U.showApiError(e); }
  }

  function drawReplay() {
    if (!replay) return;
    const k = Number(U.$("#replaySlider").value);
    const st = replay.states[k - 1];
    U.$("#replayOver").textContent = `Over ${st.over} · ${st.runs}/${st.wickets}`;
    U.html("#overStrip", replay.states.map((s, i) => `<span class="${s.over_runs >= 12 ? "hi" : ""} ${i === k - 1 ? "cur" : ""}" title="Over ${s.over}">${s.over_runs}</span>`).join(""));
    const actual = replay.states.map((s, i) => i < k ? s.runs : null);
    Charts.draw("replayChart", {
      type: "line",
      data: { labels: Array.from({ length: 20 }, (_, i) => i + 1), datasets: [
        { label: "Pre-match plan", data: replay.planned_worm, borderColor: "#c9a24b", borderDash: [6, 4], pointRadius: 0 },
        { label: "RCB actual", data: actual, borderColor: "#ef1b2d", backgroundColor: Charts.gradient("replayChart", "#ef1b2d", .25), fill: true, pointRadius: 3 },
      ] },
      options: { animation: { duration: 250 }, scales: Charts.axes("Runs", "Over"), plugins: { legend: { position: "bottom" } } },
    });
    U.html("#replayState", `
      <div class="status-banner ${st.status}" style="margin-bottom:12px"><span class="sb-status">${st.status.replace("_", " ")}</span>
        <span class="sb-msg">${U.esc(st.message)}</span></div>
      <div class="kv"><span>Plan mode / target</span><span>${replay.plan_mode.replace("_", " ")} · ${U.num(replay.plan_target, 0)}</span></div>
      <div class="kv"><span>Plan at over ${st.over}</span><span>${U.num(st.expected_runs, 1)}</span></div>
      <div class="kv"><span>Deficit (positive = behind)</span><span>${U.signed(st.deficit, 1)}</span></div>
      <div class="kv"><span>Projected total</span><span>${U.num(st.projected_total, 0)}</span></div>
      <div class="kv"><span>Required rate overall</span><span>${U.num(st.overall_required_rr, 2)}</span></div>
      <div class="table-wrap" style="margin-top:12px"><table class="table compact">${recTableShort(st.recommendations)}</table></div>`);
  }

  function stop() { if (timer) { clearInterval(timer); timer = null; U.$("#playBtn").textContent = "Play"; } }
  U.$("#playBtn").addEventListener("click", () => {
    if (timer) return stop();
    const sl = U.$("#replaySlider");
    if (Number(sl.value) >= Number(sl.max)) sl.value = 1;
    U.$("#playBtn").textContent = "Pause";
    timer = setInterval(() => { if (Number(sl.value) >= Number(sl.max)) return stop(); sl.value = Number(sl.value) + 1; drawReplay(); }, 650);
  });
  U.$("#replaySlider").addEventListener("input", () => { stop(); drawReplay(); });

  U.$("#updateBtn").addEventListener("click", e => U.busy(e.currentTarget, async () => {
    try {
      const s = await API.trackerUpdate({ match_id: Navbar.selectedMatch(), overs: U.$("#inOvers").value.trim(),
        runs: Number(U.$("#inRuns").value), wickets: Number(U.$("#inWkts").value) });
      renderState(s); await loadHistory(Navbar.selectedMatch());
      U.$("#planBadge").textContent = `${s.plan_mode.replace("_", " ")} · target ${U.num(s.plan_target, 0)} · #${s.prediction_id}`;
    } catch (err) { U.toast(err.message, "error"); }
  }));
  U.$("#resetBtn").addEventListener("click", async () => {
    const r = await API.trackerReset(Navbar.selectedMatch()); U.toast(`Cleared ${r.deleted} tracker updates`, "success"); loadHistory(Navbar.selectedMatch());
  });
  document.addEventListener("matchchange", load);
  load();
})();
