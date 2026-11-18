/* EeSaala Tracker | player-card.js */
const PlayerCard = {
  render(p, maxSr = 220) {
    const bars = EESAALA.PHASES.map(ph => {
      const d = p.phases[ph] || {};
      const w = Math.min(100, (Number(d.sr || 0) / maxSr) * 100);
      return `<div class="bar-row"><span>${ph}</span><div class="bar-track"><div class="bar-fill ${ph}" style="width:${w}%"></div></div><span class="bv">${U.num(d.sr, 0)}</span></div>`;
    }).join("");
    const bowling = p.wickets || p.economy ? `${p.wickets} wkts · ${U.num(p.economy, 2)} econ` : "Does not bowl";
    return `
      <article class="player-card" data-player="${p.player_id}">
        <span class="pc-num">${p.preferred_slot}</span>
        <div class="pc-top">
          <div class="avatar">${U.initials(p.player_name)}</div>
          <div>
            <div class="pc-name">${U.esc(p.player_name)}${p.is_captain ? ' <span class="gold">(C)</span>' : ""}</div>
            <div class="pc-meta">${U.esc(p.batting_style)}${p.bowling_style ? " · " + U.esc(p.bowling_style) : ""}</div>
          </div>
        </div>
        <div class="pc-badges">
          ${U.roleBadge(p.role)}
          ${p.is_overseas ? '<span class="badge info">Overseas</span>' : ""}
          ${p.in_xi_for_match ? '<span class="badge solid-red">In XI</span>' : ""}
          ${p.cold_start ? '<span class="badge gold" title="No 2026 batting history before this match; profile equals the synthetic prior">Cold start</span>' : ""}
        </div>
        <div class="pc-stats">
          <div><div class="l">Mat</div><div class="v">${p.matches}</div></div>
          <div><div class="l">Runs</div><div class="v">${p.runs}</div></div>
          <div><div class="l">SR</div><div class="v">${U.num(p.strike_rate, 0)}</div></div>
          <div><div class="l">Avg</div><div class="v">${U.num(p.average, 0)}</div></div>
        </div>
        <div class="bars" title="Recency-weighted phase strike rate (pre-match)">${bars}</div>
        <div class="small" style="margin-top:10px">${bowling}</div>
      </article>`;
  },
};
window.PlayerCard = PlayerCard;
