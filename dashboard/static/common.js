// Shared utilities used by every page's inline script.

async function apiGet(path) {
  const res = await fetch(`/api/v1${path}`);
  if (!res.ok) throw new Error(`API ${path} returned ${res.status}`);
  return res.json();
}

async function apiPost(path, body) {
  const res = await fetch(`/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!res.ok) throw new Error(`API ${path} returned ${res.status}`);
  return res.json();
}

function pct(v) {
  return `${Math.round(v * 100)}%`;
}

// --- Shared team cache — every page that needs crest colours/names fetches
// this once instead of re-requesting /api/v1/teams repeatedly. ---
let _teamsCache = null;
async function getTeams() {
  if (_teamsCache) return _teamsCache;
  const data = await apiGet("/teams");
  _teamsCache = {};
  data.teams.forEach((t) => { _teamsCache[t.id] = t; });
  return _teamsCache;
}

// --- Crest: a colour-filled shield with the club's short code, matching
// the React prototype's <Crest> component (clip-path shield in styles.css). ---
function crestHTML(team, size = 28) {
  if (!team) return "";
  return `<span class="crest" style="width:${size}px; height:${size}px; background:${team.color}; font-size:${size * 0.32}px;">${team.short}</span>`;
}

// --- Form guide: coloured W/D/L circles, lime=win, claret=loss, muted=draw. ---
function formGuideHTML(form, size = 20) {
  if (!form || !form.length) return `<span class="muted fs-11">New to the division</span>`;
  return `<div class="flex gap-2">${form.map(r => {
    const bg = r === "W" ? "var(--lime)" : r === "D" ? "var(--muted)" : "var(--claret)";
    const fg = r === "W" ? "var(--purple-dark)" : "#fff";
    return `<span style="display:inline-flex; align-items:center; justify-content:center; width:${size}px; height:${size}px; border-radius:50%; background:${bg}; color:${fg}; font-weight:800; font-size:${size * 0.5}px;">${r}</span>`;
  }).join("")}</div>`;
}

// --- Segmented 1X2 probability bar, team-coloured. ---
function probBarHTML(pHome, pDraw, pAway, homeColor, awayColor) {
  return `
    <div style="width:100%; height:12px; border-radius:8px; overflow:hidden; display:flex; border:1px solid var(--border);">
      <div style="width:${pHome * 100}%; background:${homeColor};"></div>
      <div style="width:${pDraw * 100}%; background:var(--muted);"></div>
      <div style="width:${pAway * 100}%; background:${awayColor};"></div>
    </div>`;
}

// --- Chart.js dark-theme defaults, applied once per page that draws charts. ---
function applyChartDefaults() {
  if (typeof Chart === "undefined") return;
  Chart.defaults.color = "#B7A6CC";
  Chart.defaults.borderColor = "#33224E";
  Chart.defaults.font.family = "-apple-system, 'Segoe UI', Inter, sans-serif";
}

// --- Staged loader: shows a sequence of status messages with a filling
// progress bar, mirroring the React prototype's "Run Prediction" UX. ---
function runStagedLoader(containerId, steps, stepMs, onDone) {
  const el = document.getElementById(containerId);
  let i = 0;
  el.style.display = "block";
  el.innerHTML = stagedLoaderHTML(steps[0], 1, steps.length);
  const iv = setInterval(() => {
    i++;
    if (i >= steps.length) {
      clearInterval(iv);
      onDone();
      return;
    }
    el.innerHTML = stagedLoaderHTML(steps[i], i + 1, steps.length);
  }, stepMs);
}

function stagedLoaderHTML(label, step, total) {
  const width = Math.round((step / total) * 100);
  return `
    <div class="card" style="text-align:center; margin:0;">
      <div class="fs-12" style="color:var(--purple); font-weight:700;">${label}</div>
      <div style="width:100%; height:8px; border-radius:6px; background:var(--surface-alt); overflow:hidden; margin-top:10px;">
        <div style="width:${width}%; height:100%; background:linear-gradient(90deg, var(--lime), var(--cyan)); transition:width 300ms ease;"></div>
      </div>
    </div>`;
}
