/* EeSaala Tracker | config.js
   API base URL resolution:
   - served by FastAPI (/app/...) -> same origin
   - served by `python -m http.server 5500` or opened from disk -> http://127.0.0.1:8000
   - override: localStorage.setItem('eesaala.api', 'http://host:port') */
(function () {
  const override = localStorage.getItem("eesaala.api");
  const sameOrigin = location.protocol.startsWith("http") && location.pathname.startsWith("/app/");
  window.EESAALA = {
    API_BASE: override || (sameOrigin ? "" : "http://127.0.0.1:8000"),
    APP_NAME: "EeSaala Tracker",
    SEASON: 2026,
    STORAGE_MATCH: "eesaala.match",
    PHASES: ["PP", "MID", "DEATH"],
    PHASE_LABEL: { PP: "Powerplay", MID: "Middle", DEATH: "Death" },
    PHASE_OVERS: { PP: "Overs 1-6", MID: "Overs 7-16", DEATH: "Overs 17-20" },
    PHASE_COLOR: { PP: "#ef1b2d", MID: "#c9a24b", DEATH: "#e9e9ee" },
    CHECKPOINT_PHASE: { 6: "PP", 16: "MID", 20: "DEATH" },
  };
})();
