/**
 * Simulation Visualizer
 * Visual season simulation process with live table updates
 */

class SimulationVisualizer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.isSimulating = false;
    this.currentSimulation = null;
    this.simulationSpeed = 100; // ms per fixture
    this.updateInterval = null;

    this.init();
  }

  init() {
    this.setupControls();
    this.setupProgressVisualization();
    this.setupLiveTable();
    this.setupChampionshipRace();
  }

  setupControls() {
    const runBtn = this.container.querySelector('#run-simulation-btn');
    const stopBtn = this.container.querySelector('#stop-simulation-btn');
    const speedSlider = this.container.querySelector('#simulation-speed');
    const countInput = this.container.querySelector('#simulation-count');

    if (runBtn) {
      runBtn.addEventListener('click', () => this.startSimulation());
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', () => this.stopSimulation());
    }

    if (speedSlider) {
      speedSlider.addEventListener('input', (e) => {
        this.simulationSpeed = parseInt(e.target.value);
      });
    }

    if (countInput) {
      countInput.addEventListener('change', (e) => {
        this.simulationCount = parseInt(e.target.value) || 300;
      });
    }
  }

  setupProgressVisualization() {
    this.progressBar = this.container.querySelector('.simulation-progress-fill');
    this.progressPercentage = this.container.querySelector('.simulation-progress-percentage');
    this.progressDetails = this.container.querySelector('.simulation-progress-details');
  }

  setupLiveTable() {
    this.liveTable = this.container.querySelector('.live-table-content');
    if (!this.liveTable) return;

    // Initialize empty table
    this.liveTable.innerHTML = this.createEmptyTableMessage();
  }

  setupChampionshipRace() {
    this.championshipBars = this.container.querySelector('.championship-bars');
    if (!this.championshipBars) return;

    // Initialize empty championship race
    this.championshipBars.innerHTML = this.createEmptyChampionshipMessage();
  }

  async startSimulation() {
    if (this.isSimulating) return;

    this.isSimulating = true;
    this.updateUIState('running');

    const count = this.simulationCount || 300;
    const fixtures = await this.getAllFixtures();

    // Start visual simulation
    await this.runVisualSimulation(fixtures, count);

    this.isSimulating = false;
    this.updateUIState('completed');
  }

  stopSimulation() {
    if (!this.isSimulating) return;

    this.isSimulating = false;
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }

    this.updateUIState('stopped');
  }

  async runVisualSimulation(fixtures, count) {
    const totalFixtures = fixtures.length;
    let completedFixtures = 0;

    // Initialize simulation state
    const simulationState = this.initializeSimulationState();

    // Process fixtures with visual updates
    for (const fixture of fixtures) {
      if (!this.isSimulating) break;

      // Simulate this fixture
      const result = this.simulateFixture(fixture, simulationState);
      
      // Update simulation state
      this.updateSimulationState(result, simulationState);

      // Update visual progress
      completedFixtures++;
      const progress = (completedFixtures / totalFixtures) * 100;
      this.updateProgress(progress, completedFixtures, totalFixtures, result);

      // Update live table periodically
      if (completedFixtures % 10 === 0) {
        this.updateLiveTable(simulationState);
      }

      // Update championship race periodically
      if (completedFixtures % 20 === 0) {
        this.updateChampionshipRace(simulationState);
      }

      // Delay for visual effect
      await this.delay(this.simulationSpeed);
    }

    // Final updates
    this.updateLiveTable(simulationState);
    this.updateChampionshipRace(simulationState);
    this.showFinalResults(simulationState);
  }

  initializeSimulationState() {
    // Initialize team states
    const teams = {};
    // This would be populated from actual team data
    return { teams, fixtureHistory: [] };
  }

  simulateFixture(fixture, state) {
    // Simulate fixture result using prediction model
    // This would call the actual prediction API
    return {
      home: fixture.home,
      away: fixture.away,
      homeGoals: Math.floor(Math.random() * 4),
      awayGoals: Math.floor(Math.random() * 4),
      probability: Math.random()
    };
  }

  updateSimulationState(result, state) {
    // Update team points, goals, etc.
    const homeTeam = state.teams[result.home];
    const awayTeam = state.teams[result.away];

    if (result.homeGoals > result.awayGoals) {
      homeTeam.points += 3;
      homeTeam.wins++;
      awayTeam.losses++;
    } else if (result.awayGoals > result.homeGoals) {
      awayTeam.points += 3;
      awayTeam.wins++;
      homeTeam.losses++;
    } else {
      homeTeam.points += 1;
      awayTeam.points += 1;
      homeTeam.draws++;
      awayTeam.draws++;
    }

    homeTeam.goalsFor += result.homeGoals;
    homeTeam.goalsAgainst += result.awayGoals;
    awayTeam.goalsFor += result.awayGoals;
    awayTeam.goalsAgainst += result.homeGoals;

    state.fixtureHistory.push(result);
  }

  updateProgress(percentage, completed, total, lastResult) {
    if (this.progressBar) {
      this.progressBar.style.width = `${percentage}%`;
    }

    if (this.progressPercentage) {
      this.progressPercentage.textContent = `${Math.round(percentage)}%`;
    }

    if (this.progressDetails) {
      this.progressDetails.innerHTML = `
        <div class="simulation-progress-detail">
          <span>Fixtures:</span>
          <strong>${completed}/${total}</strong>
        </div>
        <div class="simulation-progress-detail">
          <span>Last:</span>
          <strong>${lastResult.home} ${lastResult.homeGoals}-${lastResult.awayGoals} ${lastResult.away}</strong>
        </div>
      `;
    }
  }

  updateLiveTable(state) {
    if (!this.liveTable) return;

    // Sort teams by points
    const sortedTeams = Object.values(state.teams)
      .sort((a, b) => b.points - a.points);

    this.liveTable.innerHTML = sortedTeams.map((team, index) => `
      <div class="live-table-row animate-fade-in">
        <div class="live-table-position">${index + 1}</div>
        <div class="live-table-team">
          <span class="crest" style="width: 24px; height: 24px; background: ${team.color};">${team.short}</span>
          <span>${team.name}</span>
        </div>
        <div class="live-table-points">${team.points}</div>
      </div>
    `).join('');
  }

  updateChampionshipRace(state) {
    if (!this.championshipBars) return;

    // Calculate title probabilities based on current standings
    const sortedTeams = Object.values(state.teams)
      .sort((a, b) => b.points - a.points)
      .slice(0, 6);

    const maxPoints = Math.max(...sortedTeams.map(t => t.points));

    this.championshipBars.innerHTML = sortedTeams.map(team => {
      const probability = (team.points / maxPoints) * 100;
      return `
        <div class="championship-bar-container animate-fade-in">
          <div class="championship-team">
            <span class="crest" style="width: 20px; height: 20px; background: ${team.color};">${team.short}</span>
            <span>${team.short}</span>
          </div>
          <div class="championship-bar-wrapper">
            <div class="championship-bar championship-bar--title" style="width: ${probability}%;">
              ${probability.toFixed(1)}%
            </div>
          </div>
          <div class="championship-probability">${team.points} pts</div>
        </div>
      `;
    }).join('');
  }

  showFinalResults(state) {
    // Show final table and probabilities
    this.updateLiveTable(state);
    this.updateChampionshipRace(state);
    this.updateRelegationBattle(state);
    this.updateEuropeanQualification(state);
  }

  updateRelegationBattle(state) {
    const relegationSection = this.container.querySelector('.relegation-teams');
    if (!relegationSection) return;

    const sortedTeams = Object.values(state.teams)
      .sort((a, b) => a.points - b.points)
      .slice(0, 5);

    relegationSection.innerHTML = sortedTeams.map(team => {
      const relegationProb = this.calculateRelegationProbability(team, state);
      return `
        <div class="relegation-team-row animate-fade-in">
          <div class="relegation-team-info">
            <span class="crest" style="width: 24px; height: 24px; background: ${team.color};">${team.short}</span>
            <span class="relegation-team-name">${team.name}</span>
          </div>
          <div class="relegation-probability-bar">
            <div class="relegation-probability-fill" style="width: ${relegationProb}%;"></div>
          </div>
          <div class="relegation-probability-value">${relegationProb.toFixed(1)}%</div>
        </div>
      `;
    }).join('');
  }

  updateEuropeanQualification(state) {
    const europeanSection = this.container.querySelector('.european-spots');
    if (!europeanSection) return;

    const sortedTeams = Object.values(state.teams)
      .sort((a, b) => b.points - a.points)
      .slice(0, 7);

    // Champions League (top 4)
    const championsLeague = sortedTeams.slice(0, 4);
    // Europa League (5th)
    const europaLeague = [sortedTeams[4]];
    // Conference League (6th)
    const conferenceLeague = [sortedTeams[5]];

    europeanSection.innerHTML = `
      <div class="european-spot-card">
        <div class="european-spot-competition">Champions League</div>
        <div class="european-spot-teams">
          ${championsLeague.map(team => `
            <div class="european-spot-team">
              <span class="crest" style="width: 16px; height: 16px; background: ${team.color};">${team.short}</span>
              ${team.name}
            </div>
          `).join('')}
        </div>
      </div>
      <div class="european-spot-card">
        <div class="european-spot-competition">Europa League</div>
        <div class="european-spot-teams">
          ${europaLeague.map(team => `
            <div class="european-spot-team">
              <span class="crest" style="width: 16px; height: 16px; background: ${team.color};">${team.short}</span>
              ${team.name}
            </div>
          `).join('')}
        </div>
      </div>
      <div class="european-spot-card">
        <div class="european-spot-competition">Conference League</div>
        <div class="european-spot-teams">
          ${conferenceLeague.map(team => `
            <div class="european-spot-team">
              <span class="crest" style="width: 16px; height: 16px; background: ${team.color};">${team.short}</span>
              ${team.name}
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  calculateRelegationProbability(team, state) {
    // Simple calculation based on points and position
    const sortedTeams = Object.values(state.teams).sort((a, b) => a.points - b.points);
    const position = sortedTeams.findIndex(t => t.id === team.id) + 1;
    
    if (position <= 3) return 80 + Math.random() * 20;
    if (position <= 5) return 40 + Math.random() * 40;
    if (position <= 7) return 10 + Math.random() * 30;
    return Math.random() * 10;
  }

  updateUIState(state) {
    const runBtn = this.container.querySelector('#run-simulation-btn');
    const stopBtn = this.container.querySelector('#stop-simulation-btn');

    if (runBtn) {
      runBtn.disabled = state === 'running';
    }

    if (stopBtn) {
      stopBtn.disabled = state !== 'running';
    }
  }

  createEmptyTableMessage() {
    return '<div style="text-align: center; padding: 20px; color: var(--text-muted);">Run simulation to see live table updates</div>';
  }

  createEmptyChampionshipMessage() {
    return '<div style="text-align: center; padding: 20px; color: var(--text-muted);">Run simulation to see championship race</div>';
  }

  async getAllFixtures() {
    // This would fetch actual fixtures from the API
    return [];
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  reset() {
    this.stopSimulation();
    if (this.liveTable) {
      this.liveTable.innerHTML = this.createEmptyTableMessage();
    }
    if (this.championshipBars) {
      this.championshipBars.innerHTML = this.createEmptyChampionshipMessage();
    }
    if (this.progressBar) {
      this.progressBar.style.width = '0%';
    }
    if (this.progressPercentage) {
      this.progressPercentage.textContent = '0%';
    }
  }
}

// Initialize simulation visualizers on the page
document.addEventListener('DOMContentLoaded', () => {
  const visualizers = document.querySelectorAll('.simulation-container');
  visualizers.forEach(visualizer => {
    new SimulationVisualizer(visualizer.id);
  });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SimulationVisualizer;
}