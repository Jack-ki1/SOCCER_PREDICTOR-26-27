// Renders the all-20-clubs ratings grid on the Analytics page.

// Lightens a hex colour if it's too dark to read against the dark UI background
// (Newcastle #241F20, Fulham #1A1A1A are both close to black) — only used for
// bar fills, never for crests (which already have white text + shadow for contrast).
function readableBarColor(hex) {
  const r = parseInt(hex.slice(1, 3), 16), g = parseInt(hex.slice(3, 5), 16), b = parseInt(hex.slice(5, 7), 16);
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  if (luminance > 0.18) return hex;
  const lighten = (c) => Math.round(c + (255 - c) * 0.55);
  return `rgb(${lighten(r)}, ${lighten(g)}, ${lighten(b)})`;
}

function ratingBar(label, value, color) {
  return `
    <div class="flex items-center gap-2" style="margin-bottom:6px;">
      <span class="muted fs-11" style="width:70px; flex-shrink:0;">${label}</span>
      <div style="flex:1; height:6px; background:var(--surface-alt); border-radius:4px; overflow:hidden;">
        <div style="width:${value}%; height:100%; background:${readableBarColor(color)};"></div>
      </div>
    </div>`;
}

function renderTeamGrid(teams) {
  const grid = document.getElementById('team-grid');
  if (!grid) return;
  grid.innerHTML = teams.map(t => `
    <div class="card" style="margin:0;">
      <div class="flex items-center gap-2 mb-2">
        <span class="crest" style="background:${t.color};">${t.short}</span>
        <div>
          <div style="font-weight:800; font-size:13px;">${t.name}</div>
          <div class="muted fs-11">${t.tag}</div>
        </div>
      </div>
      ${ratingBar('Attack', t.attack, t.color)}
      ${ratingBar('Defence', t.defense, t.color)}
      ${ratingBar('Home edge', t.home_adv, t.color)}
      <div class="mt-2">${formGuideHTML(t.form, 18)}</div>
    </div>
  `).join('');
}
