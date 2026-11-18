/* EeSaala Tracker | phase-card.js */
const PhaseCard = {
  render(c) {
    const ph = c.phase;
    return `
      <div class="phase-card" style="--phase-color:${EESAALA.PHASE_COLOR[ph]}">
        <div class="ph-head">
          <div><div class="ph-name">${EESAALA.PHASE_LABEL[ph]}</div><div class="ph-overs">${EESAALA.PHASE_OVERS[ph]} · ${c.phase_balls} balls</div></div>
          ${U.phaseTag(ph)}
        </div>
        <div class="ph-big num">${U.num(c.adj_runs, 1)}<small>adjusted runs</small></div>
        <div class="small" style="margin-top:4px">Expected wickets <b class="num" style="color:var(--text)">${U.num(c.adj_wickets, 2)}</b> · raw capacity ${U.num(c.raw_runs, 1)}</div>
        <div class="ph-metrics">
          <div><div class="m-l">Team SR</div><div class="m-v">${U.num(c.team_sr, 1)}</div></div>
          <div><div class="m-l">Out / ball</div><div class="m-v">${U.num(c.team_out_prob, 3)}</div></div>
          <div><div class="m-l">Run rate</div><div class="m-v">${U.num(6 * c.adj_runs / c.phase_balls, 2)}</div></div>
          <div><div class="m-l">Venue VF</div><div class="m-v">${U.num(c.venue_factor, 3)}</div></div>
          <div><div class="m-l">Opp threat</div><div class="m-v">${U.num(c.opp_threat, 3)}</div></div>
          <div><div class="m-l">Extras/ball</div><div class="m-v">${U.num(c.extras_rate, 3)}</div></div>
        </div>
      </div>`;
  },
};
window.PhaseCard = PhaseCard;
