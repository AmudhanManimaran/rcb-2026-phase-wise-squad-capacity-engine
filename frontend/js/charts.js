/* EeSaala Tracker | charts.js   Chart.js theme and factories. */
const Charts = (() => {
  const registry = {};
  function theme() {
    if (!window.Chart) return;
    Chart.defaults.color = "#a3a3ad";
    Chart.defaults.font.family = "Inter, 'Segoe UI', system-ui, sans-serif";
    Chart.defaults.font.size = 11.5;
    Chart.defaults.borderColor = "rgba(255,255,255,0.06)";
    Chart.defaults.plugins.legend.labels.boxWidth = 10;
    Chart.defaults.plugins.legend.labels.boxHeight = 10;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.tooltip.backgroundColor = "#18181c";
    Chart.defaults.plugins.tooltip.borderColor = "#2f2f37";
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.titleFont = { family: "Oswald", size: 13, weight: "600" };
    Chart.defaults.elements.bar.borderRadius = 5;
    Chart.defaults.elements.line.tension = 0.3;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.maintainAspectRatio = false;
  }
  function draw(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return null;
    if (!window.Chart) { canvas.parentElement.innerHTML = '<div class="empty">Chart library not loaded.</div>'; return null; }
    if (registry[id]) registry[id].destroy();
    registry[id] = new Chart(canvas.getContext("2d"), config);
    return registry[id];
  }
  function gradient(id, color, alpha = 0.35) {
    const c = document.getElementById(id); if (!c) return color;
    const g = c.getContext("2d").createLinearGradient(0, 0, 0, c.clientHeight || 300);
    g.addColorStop(0, hexA(color, alpha)); g.addColorStop(1, hexA(color, 0));
    return g;
  }
  function hexA(hex, a) {
    const h = hex.replace("#", ""); const n = parseInt(h, 16);
    return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
  }
  const axes = (yTitle, xTitle) => ({
    x: { grid: { display: false }, title: { display: !!xTitle, text: xTitle } },
    y: { beginAtZero: true, title: { display: !!yTitle, text: yTitle }, grid: { color: "rgba(255,255,255,0.05)" } },
  });
  theme();
  return { draw, gradient, hexA, axes, registry };
})();
window.Charts = Charts;
