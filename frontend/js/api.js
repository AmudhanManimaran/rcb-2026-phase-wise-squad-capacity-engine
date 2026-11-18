/* EeSaala Tracker | api.js   Thin fetch wrapper around the FastAPI backend. */
const API = (() => {
  async function request(path, { method = "GET", body } = {}) {
    const opts = { method, headers: { Accept: "application/json" } };
    if (body !== undefined) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    let res;
    try { res = await fetch(EESAALA.API_BASE + path, opts); }
    catch (e) { const err = new Error(`Cannot reach ${EESAALA.API_BASE || location.origin}${path}`); err.network = true; throw err; }
    const text = await res.text();
    const data = text ? JSON.parse(text) : null;
    if (!res.ok) {
      const detail = data && data.detail ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg).join("; ") : data.detail) : res.statusText;
      const err = new Error(detail); err.status = res.status; throw err;
    }
    return data;
  }
  return {
    health: () => request("/api/health"),
    dashboard: () => request("/api/dashboard"),
    squad: (asOf) => request("/api/squad" + (asOf ? `?as_of_match_id=${asOf}` : "")),
    player: (id) => request(`/api/squad/${id}`),
    matches: () => request("/api/matches"),
    match: (id) => request(`/api/matches/${id}`),
    capacity: (id, xi) => xi ? request(`/api/matches/${id}/capacity`, { method: "POST", body: { xi_player_ids: xi } })
                             : request(`/api/matches/${id}/capacity`),
    plan: (body) => request("/api/targets/plan", { method: "POST", body }),
    savedPlan: (id) => request(`/api/targets/${id}`),
    trackerUpdate: (body) => request("/api/tracker/update", { method: "POST", body }),
    tracker: (id) => request(`/api/tracker/${id}`),
    trackerRecommendation: (id) => request(`/api/tracker/${id}/recommendation`),
    trackerReplay: (id) => request(`/api/tracker/${id}/replay`),
    trackerReset: (id) => request(`/api/tracker/${id}`, { method: "DELETE" }),
    runBacktest: () => request("/api/backtest/run", { method: "POST" }),
    calibrate: () => request("/api/backtest/calibrate", { method: "POST" }),
    parameters: () => request("/api/backtest/parameters"),
    activateParams: (id) => request(`/api/backtest/parameters/${id}/activate`, { method: "POST" }),
    backtestResults: () => request("/api/backtest/results"),
    backtestMatch: (id) => request(`/api/backtest/${id}`),
    phases: () => request("/api/analytics/phases"),
    venues: () => request("/api/analytics/venues"),
    players: () => request("/api/analytics/players"),
    formulas: () => request("/api/capacity/formulas"),
  };
})();
window.API = API;
