/* EeSaala Tracker | target-planner.js */
(async function () {
  Sidebar.render("planner");
  await Navbar.render({ eyebrow: "04 · Planning", title: "Target Planner", matchSelector: true });
  const state = { mode: "AUTO", xiMode: "fixture", custom: [], squad: [] };

  function normalize(p) {
    if (p.prediction) {      // saved prediction from the database
      const h = p.prediction; let acc = 0;
      return {
        prediction_id: h.prediction_id, run_type: h.run_type, mode: h.plan_mode, t_base: h.t_base, bsi: h.bsi, t_rec: h.t_recommended,
        plan_target: h.plan_target, cost: h.plan_cost, capacity_total: h.capacity_total, history: h.history_matches, custom: h.custom_xi,
        checkpoints: p.checkpoints.map(c => ({ ...c, target_cum_runs: (acc += c.target_phase_runs) })),
        projection: p.checkpoints.map(c => ({ checkpoint_over: c.checkpoint_over, projected_runs: c.projected_runs, projected_wkts: c.projected_wkts })),
        capacity: p.capacity,
      };
    }
    return {
      prediction_id: p.prediction_id, run_type: "ADHOC", mode: p.plan_mode, t_base: p.target.t_base, bsi: p.target.bsi,
      t_rec: p.target.t_recommended, plan_target: p.plan_target, cost: p.plan.total_cost, capacity_total: p.capacity_total,
      history: p.history_matches, custom: p.custom_xi, checkpoints: p.plan.checkpoints, projection: p.projection, capacity: p.capacity,
    };
  }

  function render(n) {
    const m = Navbar.matchById(Navbar.selectedMatch()) || {};
    U.html("#targetKpis", [
      ["Recommended target", U.num(n.t_rec, 0), `T_base ${U.num(n.t_base, 1)} x (2 - BSI)`, "red"],
      ["Plan target", U.num(n.plan_target, 0), n.mode === "CHASE" ? "runs required (chase)" : "batting first"],
      ["Bowling strength index", U.num(n.bsi, 3), n.bsi > 1 ? "attack stronger than league" : "attack weaker than league"],
      ["XI capacity", U.num(n.capacity_total, 1), `${n.history} matches of history · cost ${U.num(n.cost, 1)}`],
    ].map(([l, v, f, cls]) => `<div class="kpi ${cls || ""}"><div class="kpi-label">${l}</div><div class="kpi-value">${v}</div><div class="kpi-foot">${f}</div></div>`).join(""));
    U.html("#checkpoints", n.checkpoints.map(c => CheckpointCard.render(c, n.projection)).join(""));

    const cap = Object.fromEntries(n.capacity.map(c => [c.phase, c.adj_runs]));
    Charts.draw("planChart", {
      type: "bar",
      data: { labels: EESAALA.PHASES.map(p => EESAALA.PHASE_LABEL[p]),
        datasets: [
          { label: "Venue-shaped target", data: n.checkpoints.map(c => c.target_phase_runs), backgroundColor: "#3a3a42" },
          { label: "DP plan", data: n.checkpoints.map(c => c.planned_phase_runs), backgroundColor: "#ef1b2d" },
          { label: "Adjusted capacity", data: EESAALA.PHASES.map(p => cap[p]), backgroundColor: "#c9a24b" },
        ] },
      options: { scales: Charts.axes("Runs"), plugins: { legend: { position: "bottom" } } },
    });
    const overs = { PP: 6, MID: 10, DEATH: 4 };
    const worm = (vals) => { const out = []; let a = 0; EESAALA.PHASES.forEach((p, i) => { for (let k = 0; k < overs[p]; k++) { a += vals[i] / overs[p]; out.push(+a.toFixed(1)); } }); return out; };
    Charts.draw("wormChart", {
      type: "line",
      data: { labels: Array.from({ length: 20 }, (_, i) => i + 1),
        datasets: [
          { label: "DP plan", data: worm(n.checkpoints.map(c => c.planned_phase_runs)), borderColor: "#ef1b2d", backgroundColor: Charts.gradient("wormChart", "#ef1b2d", .25), fill: true, pointRadius: 0 },
          { label: "Target", data: worm(n.checkpoints.map(c => c.target_phase_runs)), borderColor: "#8d8d97", borderDash: [5, 4], pointRadius: 0 },
          { label: "Capacity", data: worm(EESAALA.PHASES.map(p => cap[p])), borderColor: "#c9a24b", pointRadius: 0 },
        ] },
      options: { scales: { ...Charts.axes("Runs", "Over"), x: { grid: { display: false }, ticks: { maxRotation: 0 }, title: { display: true, text: "Over" } } }, plugins: { legend: { position: "bottom" } } },
    });
  }

  function renderXi() {
    const byId = Object.fromEntries(state.squad.map(p => [p.player_id, p]));
    const chosen = state.custom.map(id => byId[id]).filter(Boolean);
    const rest = state.squad.filter(p => !state.custom.includes(p.player_id)).sort((a, b) => a.preferred_slot - b.preferred_slot);
    const os = chosen.filter(p => p.is_overseas).length;
    U.$("#xiCount").textContent = `${chosen.length} / 11 · ${os} OS`;
    U.$("#xiCount").className = `badge ${chosen.length === 11 && os <= 4 ? "ok" : "warn"}`;
    U.html("#xiList", [...chosen.map((p, i) => item(p, i + 1, true)), ...rest.map(p => item(p, "", false))].join(""));
    U.$$("#xiList [data-act]").forEach(b => b.addEventListener("click", () => {
      const id = Number(b.dataset.id), i = state.custom.indexOf(id);
      if (b.dataset.act === "toggle") { if (i >= 0) state.custom.splice(i, 1); else if (state.custom.length < 11) state.custom.push(id); else U.toast("XI already has 11 players", "error"); }
      if (b.dataset.act === "up" && i > 0) [state.custom[i - 1], state.custom[i]] = [state.custom[i], state.custom[i - 1]];
      if (b.dataset.act === "down" && i >= 0 && i < state.custom.length - 1) [state.custom[i + 1], state.custom[i]] = [state.custom[i], state.custom[i + 1]];
      renderXi();
    }));
    function item(p, ord, on) {
      return `<div class="xi-item ${on ? "on" : ""}"><span class="xi-ord">${ord || ""}</span>
        <span>${U.esc(p.player_name)} <small class="muted">${p.role}${p.is_overseas ? " · OS" : ""}</small></span>
        <span class="xi-actions">${on ? `<button data-act="up" data-id="${p.player_id}" title="Move up">&uarr;</button><button data-act="down" data-id="${p.player_id}" title="Move down">&darr;</button>` : ""}
        <button data-act="toggle" data-id="${p.player_id}" title="${on ? "Remove" : "Add"}">${on ? "&minus;" : "+"}</button></span></div>`;
    }
  }

  async function loadMatch() {
    const mid = Navbar.selectedMatch();
    try {
      const [sq, md] = await Promise.all([API.squad(mid), API.match(mid)]);
      state.squad = sq.players;
      state.custom = md.selection.filter(s => s.batting_order).sort((a, b) => a.batting_order - b.batting_order).map(s => s.player_id);
      U.$("#chaseTarget").placeholder = md.match.rcb_batting_first ? "RCB bats first in fixture" : `Fixture: ${md.match.opp_runs + 1}`;
      renderXi();
      const saved = await API.savedPlan(mid).catch(() => null);
      if (saved) render(normalize(saved)); else await generate();
    } catch (e) { U.showApiError(e); }
  }

  async function generate() {
    const body = { match_id: Navbar.selectedMatch(), wicket_penalty: Number(U.$("#wpen").value) };
    if (state.mode !== "AUTO") body.plan_mode = state.mode;
    const ct = Number(U.$("#chaseTarget").value);
    if (state.mode === "CHASE" && ct > 0) body.chase_target = ct;
    if (state.xiMode === "custom") {
      if (state.custom.length !== 11) { U.toast("Select exactly 11 players for a custom XI", "error"); return; }
      body.xi_player_ids = state.custom;
    }
    const res = await API.plan(body);
    render(normalize(res));
    U.toast(`Plan saved (prediction #${res.prediction_id})`, "success");
  }

  // controls
  try {
    const cfg = await (await fetch(EESAALA.API_BASE + "/api/capacity/config")).json();
    U.$("#wpen").value = cfg.active_params.wicket_penalty;
  } catch { U.$("#wpen").value = 4; }
  const syncW = () => U.$("#wpenVal").textContent = Number(U.$("#wpen").value).toFixed(1);
  U.$("#wpen").addEventListener("input", syncW); syncW();
  U.$$("#modeSeg button").forEach(b => b.addEventListener("click", () => {
    U.$$("#modeSeg button").forEach(x => x.classList.remove("on")); b.classList.add("on"); state.mode = b.dataset.mode;
    U.$("#chaseField").style.opacity = state.mode === "CHASE" ? 1 : .5;
  }));
  U.$("#chaseField").style.opacity = .5;
  U.$$("#xiModeSeg button").forEach(b => b.addEventListener("click", () => {
    U.$$("#xiModeSeg button").forEach(x => x.classList.remove("on")); b.classList.add("on"); state.xiMode = b.dataset.x;
    U.$("#xiCard").classList.toggle("hidden", state.xiMode !== "custom");
  }));
  U.$("#planBtn").addEventListener("click", e => U.busy(e.currentTarget, () => generate().catch(err => U.toast(err.message, "error"))));
  document.addEventListener("matchchange", loadMatch);
  loadMatch();
})();
