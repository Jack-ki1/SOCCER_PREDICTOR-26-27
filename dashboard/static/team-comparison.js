/**
 * Team Comparison Tool
 * Interactive team comparison with visual radar charts and statistics
 */

class TeamComparison {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.selectedTeams = new Set();
    this.maxTeams = 4;
    this.chartInstance = null;

    this.init();
  }

  init() {
    this.setupTeamSelector();
    this.setupComparisonGrid();
    this.setupRadarChart();
    this.setupStatistics();
    this.setupHeadToHead();
  }

  setupTeamSelector() {
    const teamSelector = this.container.querySelector('.team-selector');
    if (!teamSelector) return;

    const teamOptions = teamSelector.querySelectorAll('.team-option');
    teamOptions.forEach(option => {
      option.addEventListener('click', () => this.toggleTeam(option));
    });
  }

  setupComparisonGrid() {
    this.comparisonGrid = this.container.querySelector('.comparison-grid');
    if (!this.comparisonGrid) return;

    this.comparisonGrid.innerHTML = this.createEmptyState();
  }

  setupRadarChart() {
    const canvas = this.container.querySelector('#team-radar-chart');
    if (!canvas) return;

    // Initialize Chart.js radar chart
    if (typeof Chart !== 'undefined') {
      this.chartInstance = new Chart(canvas, {
        type: 'radar',
        data: {
          labels: ['Attack', 'Defense', 'Home Advantage', 'Form', 'Discipline'],
          datasets: []
        },
        options: {
          responsive: true,
          scales: {
            r: {
              beginAtZero: true,
              max: 100,
              ticks: {
                backdropColor: 'transparent',
                color: '#9ca3af'
              },
              grid: {
                color: 'rgba(255, 255, 255, 0.1)'
              },
              pointLabels: {
                color: '#f3f4f6',
                font: {
                  size: 12
                }
              }
            }
          },
          plugins: {
            legend: {
              labels: {
                color: '#f3f4f6'
              }
            }
          }
        }
      });
    }
  }

  setupStatistics() {
    this.statisticsContainer = this.container.querySelector('.team-statistics');
    if (!this.statisticsContainer) return;

    this.statisticsContainer.innerHTML = this.createEmptyStatistics();
  }

  setupHeadToHead() {
    this.headToHeadContainer = this.container.querySelector('.head-to-head');
    if (!this.headToHeadContainer) return;

    this.headToHeadContainer.innerHTML = this.createEmptyHeadToHead();
  }

  toggleTeam(option) {
    const teamId = option.dataset.teamId;
    const teamName = option.dataset.teamName;
    const teamColor = option.dataset.teamColor;

    if (this.selectedTeams.has(teamId)) {
      this.selectedTeams.delete(teamId);
      option.classList.remove('selected');
    } else {
      if (this.selectedTeams.size >= this.maxTeams) {
        this.showMaxTeamsWarning();
        return;
      }
      this.selectedTeams.add(teamId);
      option.classList.add('selected');
    }

    this.updateComparison();
  }

  async updateComparison() {
    if (this.selectedTeams.size === 0) {
      this.comparisonGrid.innerHTML = this.createEmptyState();
      this.statisticsContainer.innerHTML = this.createEmptyStatistics();
      this.headToHeadContainer.innerHTML = this.createEmptyHeadToHead();
      this.updateRadarChart([]);
      return;
    }

    const teamIds = Array.from(this.selectedTeams);
    const teamData = await this.fetchTeamData(teamIds);

    this.comparisonGrid.innerHTML = this.createComparisonCards(teamData);
    this.statisticsContainer.innerHTML = this.createStatisticsTable(teamData);
    this.updateRadarChart(teamData);
    
    if (teamIds.length === 2) {
      const h2hData = await this.fetchHeadToHead(teamIds[0], teamIds[1]);
      this.headToHeadContainer.innerHTML = this.createHeadToHeadDisplay(h2hData);
    } else {
      this.headToHeadContainer.innerHTML = this.createEmptyHeadToHead();
    }
  }

  async fetchTeamData(teamIds) {
    // This would fetch actual team data from the API
    // For now, return mock data
    return teamIds.map(id => ({
      id,
      name: id.toUpperCase(),
      short: id.substring(0, 3).toUpperCase(),
      color: this.getTeamColor(id),
      attack: Math.floor(Math.random() * 30) + 70,
      defense: Math.floor(Math.random() * 30) + 70,
      homeAdvantage: Math.floor(Math.random() * 20) + 50,
      form: Math.floor(Math.random() * 20) + 70,
      discipline: Math.floor(Math.random() * 20) + 60,
      points: Math.floor(Math.random() * 30) + 50,
      goalsFor: Math.floor(Math.random() * 40) + 40,
      goalsAgainst: Math.floor(Math.random() * 30) + 30,
      wins: Math.floor(Math.random() * 15) + 10,
      draws: Math.floor(Math.random() * 10) + 5,
      losses: Math.floor(Math.random() * 10) + 5
    }));
  }

  async fetchHeadToHead(teamId1, teamId2) {
    // This would fetch actual head-to-head data from the API
    return {
      team1: teamId1.toUpperCase(),
      team2: teamId2.toUpperCase(),
      matches: 10,
      team1Wins: 4,
      draws: 3,
      team2Wins: 3,
      team1Goals: 15,
      team2Goals: 12,
      lastFiveMatches: [
        { home: teamId1, away: teamId2, score: '2-1', result: 'home' },
        { home: teamId2, away: teamId1, score: '1-1', result: 'draw' },
        { home: teamId1, away: teamId2, score: '3-0', result: 'home' },
        { home: teamId2, away: teamId1, score: '2-2', result: 'draw' },
        { home: teamId1, away: teamId2, score: '1-2', result: 'away' }
      ]
    };
  }

  getTeamColor(teamId) {
    const colors = {
      'ars': '#EF0107',
      'mci': '#6CABDD',
      'liv': '#C8102E',
      'che': '#034694',
      'mun': '#DA291C',
      'tot': '#132257',
      'avl': '#670E36'
    };
    return colors[teamId] || '#6b21a8';
  }

  createComparisonCards(teamData) {
    return `
      <div class="comparison-cards animate-fade-in">
        ${teamData.map(team => `
          <div class="comparison-card" style="border-color: ${team.color}">
            <div class="comparison-card-header">
              <span class="crest" style="width: 40px; height: 40px; background: ${team.color};">${team.short}</span>
              <div>
                <div class="comparison-team-name">${team.name}</div>
                <div class="comparison-team-stats">${team.points} pts</div>
              </div>
            </div>
            <div class="comparison-card-body">
              <div class="comparison-stat-row">
                <span class="comparison-stat-label">Attack</span>
                <div class="comparison-stat-bar">
                  <div class="comparison-stat-fill" style="width: ${team.attack}%; background: ${team.color};"></div>
                </div>
                <span class="comparison-stat-value">${team.attack}</span>
              </div>
              <div class="comparison-stat-row">
                <span class="comparison-stat-label">Defense</span>
                <div class="comparison-stat-bar">
                  <div class="comparison-stat-fill" style="width: ${team.defense}%; background: ${team.color};"></div>
                </div>
                <span class="comparison-stat-value">${team.defense}</span>
              </div>
              <div class="comparison-stat-row">
                <span class="comparison-stat-label">Form</span>
                <div class="comparison-stat-bar">
                  <div class="comparison-stat-fill" style="width: ${team.form}%; background: ${team.color};"></div>
                </div>
                <span class="comparison-stat-value">${team.form}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  createStatisticsTable(teamData) {
    return `
      <div class="statistics-table animate-fade-in">
        <table>
          <thead>
            <tr>
              <th>Team</th>
              <th>Pts</th>
              <th>W</th>
              <th>D</th>
              <th>L</th>
              <th>GF</th>
              <th>GA</th>
              <th>GD</th>
            </tr>
          </thead>
          <tbody>
            ${teamData.map(team => `
              <tr>
                <td>
                  <span class="crest" style="width: 20px; height: 20px; background: ${team.color};">${team.short}</span>
                  ${team.name}
                </td>
                <td style="font-weight: 700;">${team.points}</td>
                <td>${team.wins}</td>
                <td>${team.draws}</td>
                <td>${team.losses}</td>
                <td>${team.goalsFor}</td>
                <td>${team.goalsAgainst}</td>
                <td style="font-weight: 700; color: ${team.goalsFor - team.goalsAgainst >= 0 ? 'var(--pl-green)' : 'var(--pl-red)'}">
                  ${team.goalsFor - team.goalsAgainst > 0 ? '+' : ''}${team.goalsFor - team.goalsAgainst}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  updateRadarChart(teamData) {
    if (!this.chartInstance) return;

    this.chartInstance.data.datasets = teamData.map(team => ({
      label: team.name,
      data: [team.attack, team.defense, team.homeAdvantage, team.form, team.discipline],
      backgroundColor: team.color + '33',
      borderColor: team.color,
      borderWidth: 2,
      pointBackgroundColor: team.color,
      pointBorderColor: '#fff',
      pointHoverBackgroundColor: '#fff',
      pointHoverBorderColor: team.color
    }));

    this.chartInstance.update();
  }

  createHeadToHeadDisplay(h2hData) {
    return `
      <div class="head-to-head-display animate-fade-in">
        <div class="h2h-header">
          <div class="h2h-teams">
            <span class="crest" style="width: 24px; height: 24px; background: ${this.getTeamColor(h2hData.team1)};">${h2hData.team1.substring(0, 3)}</span>
            <span>vs</span>
            <span class="crest" style="width: 24px; height: 24px; background: ${this.getTeamColor(h2hData.team2)};">${h2hData.team2.substring(0, 3)}</span>
          </div>
          <div class="h2h-record">
            <span class="h2h-record-item">${h2hData.team1Wins}W</span>
            <span class="h2h-record-item">${h2hData.draws}D</span>
            <span class="h2h-record-item">${h2hData.team2Wins}W</span>
          </div>
        </div>
        <div class="h2h-stats">
          <div class="h2h-stat">
            <span class="h2h-stat-label">Matches</span>
            <span class="h2h-stat-value">${h2hData.matches}</span>
          </div>
          <div class="h2h-stat">
            <span class="h2h-stat-label">${h2hData.team1} Goals</span>
            <span class="h2h-stat-value">${h2hData.team1Goals}</span>
          </div>
          <div class="h2h-stat">
            <span class="h2h-stat-label">${h2hData.team2} Goals</span>
            <span class="h2h-stat-value">${h2hData.team2Goals}</span>
          </div>
        </div>
        <div class="h2h-recent">
          <div class="h2h-recent-title">Last 5 Meetings</div>
          <div class="h2h-recent-matches">
            ${h2hData.lastFiveMatches.map(match => `
              <div class="h2h-recent-match">
                <span class="h2h-match-team">${match.home.substring(0, 3)}</span>
                <span class="h2h-match-score ${match.result === 'home' ? 'h2h-match-score--home' : match.result === 'away' ? 'h2h-match-score--away' : ''}">${match.score}</span>
                <span class="h2h-match-team">${match.away.substring(0, 3)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
  }

  createEmptyState() {
    return `
      <div class="empty-state">
        <div class="empty-state-icon">📊</div>
        <div class="empty-state-title">Select teams to compare</div>
        <div class="empty-state-description">Choose up to ${this.maxTeams} teams to see detailed comparisons</div>
      </div>
    `;
  }

  createEmptyStatistics() {
    return `
      <div class="empty-state">
        <div class="empty-state-description">Select teams to view statistics</div>
      </div>
    `;
  }

  createEmptyHeadToHead() {
    return `
      <div class="empty-state">
        <div class="empty-state-description">Select exactly 2 teams to view head-to-head record</div>
      </div>
    `;
  }

  showMaxTeamsWarning() {
    const notification = document.createElement('div');
    notification.className = 'team-comparison-notification';
    notification.textContent = `Maximum ${this.maxTeams} teams can be compared`;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--pl-red);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 1000;
      animation: fadeInDown 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'fadeOutUp 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  reset() {
    this.selectedTeams.clear();
    const selectedOptions = this.container.querySelectorAll('.team-option.selected');
    selectedOptions.forEach(option => option.classList.remove('selected'));
    this.updateComparison();
  }
}

// Initialize team comparison tools on the page
document.addEventListener('DOMContentLoaded', () => {
  const comparisonTools = document.querySelectorAll('.team-comparison-container');
  comparisonTools.forEach(tool => {
    new TeamComparison(tool.id);
  });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TeamComparison;
}