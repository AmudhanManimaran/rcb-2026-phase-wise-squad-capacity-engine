/* EeSaala Tracker | checkpoint-card.js */
const CheckpointCard = {
  render(cp, projection) {
    const proj = projection ? projection.find(p => p.checkpoint_over === cp.checkpoint_over) : null;
    return `
      <div class="checkpoint">
        <span class="cp-num">${cp.checkpoint_over}</span>
        <div class="cp-over">After over ${cp.checkpoint_over} · ${EESAALA.PHASE_LABEL[cp.phase]}</div>
        <div class="cp-score">${U.num(cp.planned_cum_runs, 0)}<span class="w">/${U.num(cp.planned_cum_wkts, 1)}</span></div>
        <div class="small" style="margin-bottom:8px">Planned checkpoint (runs / expected wickets)</div>
        <div class="cp-row"><span>Venue-shaped target</span><b>${U.num(cp.target_cum_runs ?? cp.target_phase_runs, 0)}</b></div>
        <div class="cp-row"><span>Phase target / planned</span><b>${U.num(cp.target_phase_runs, 0)} / ${U.num(cp.planned_phase_runs, 0)}</b></div>
        <div class="cp-row"><span>Intent multiplier</span><b>${U.num(cp.intent, 2)}x</b></div>
        ${proj ? `<div class="cp-row"><span>Capacity projection</span><b>${U.num(proj.projected_runs, 0)}/${U.num(proj.projected_wkts, 1)}</b></div>` : ""}
      </div>`;
  },
};
window.CheckpointCard = CheckpointCard;
