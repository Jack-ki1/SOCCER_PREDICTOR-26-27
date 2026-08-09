// Shared rendering helpers for the Table, Fixtures, and FPL Lab pages.

async function renderTable(projection) {
  const teams = await getTeams();
  const tbody = document.getElementById('rows');
  if (!tbody) return;
  tbody.innerHTML = projection.map((r, i) => {
    const t = teams[r.club_id];
    return `<tr>
      <td style="color:${i<4?'var(--purple)':i>=17?'var(--claret)':'var(--sub)'}; font-weight:800;">${i + 1}</td>
      <td>${crestHTML(t, 24)} ${t ? t.name : r.club_id.toUpperCase()}</td>
      <td>${formGuideHTML(t ? t.form : null, 18)}</td>
      <td style="font-weight:800;">${r.avg_points.toFixed(0)}</td>
      <td style="color:${r.title_prob > 0.02 ? 'var(--purple)' : 'var(--muted)'}">${pct(r.title_prob)}</td>
      <td style="color:${r.top4_prob > 0.1 ? 'var(--lime)' : 'var(--muted)'}">${pct(r.top4_prob)}</td>
      <td style="color:${r.releg_prob > 0.1 ? 'var(--claret)' : 'var(--muted)'}">${pct(r.releg_prob)}</td>
    </tr>`;
  }).join('');

  renderTitleRaceChart(projection.slice(0, 8), teams);
}

let titleRaceChartInstance = null;
function renderTitleRaceChart(top8, teams) {
  const canvas = document.getElementById('title-race-chart');
  if (!canvas || typeof Chart === 'undefined') return;
  applyChartDefaults();
  const labels = top8.map(r => (teams[r.club_id] || { short: r.club_id.toUpperCase() }).short);
  if (titleRaceChartInstance) titleRaceChartInstance.destroy();
  titleRaceChartInstance = new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        { label: 'Title', data: top8.map(r => r.title_prob * 100), backgroundColor: '#B47DE0' },
        { label: 'Top 4 (excl. title)', data: top8.map(r => (r.top4_prob - r.title_prob) * 100), backgroundColor: '#00FF85' },
      ],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      scales: { x: { stacked: true, ticks: { callback: v => v + '%' } }, y: { stacked: true } },
    },
  });
}

function renderFplLabRows(rows, targetId, sortKey, valueFormatter, teams) {
  const el = document.getElementById(targetId);
  if (!el) return;
  const sorted = [...rows].sort((a, b) => b[sortKey] - a[sortKey]).slice(0, 5);
  el.innerHTML = sorted.map((r, i) => {
    const t = teams ? teams[r.club_id] : null;
    return `<div class="flex justify-between items-center card" style="margin:0 0 8px; padding:10px 14px; ${i === 0 ? 'border-color:var(--lime);' : ''}">
      <span class="flex items-center gap-2">${t ? crestHTML(t, 22) : ''} ${r.club_name} <span class="muted fs-11">${r.venue} vs ${r.opponent}</span></span>
      <span style="font-weight:800;">${valueFormatter(r)}</span>
    </div>`;
  }).join('');
}
