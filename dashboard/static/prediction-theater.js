/**
 * Prediction Theater
 * Enhanced prediction display with animations and interactive elements
 */

class PredictionTheater {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.currentPrediction = null;
    this.animationQueue = [];
    this.isAnimating = false;

    this.init();
  }

  init() {
    this.setupInteractiveElements();
    this.setupScoreGrid();
    this.setupConfidenceMeter();
    this.setupKeyFactors();
  }

  setupInteractiveElements() {
    // Setup probability bar interactions
    const probBar = this.container.querySelector('.probability-bar');
    if (probBar) {
      probBar.addEventListener('click', (e) => this.handleProbabilityBarClick(e));
    }

    // Setup stat card interactions
    const statCards = this.container.querySelectorAll('.stat-card');
    statCards.forEach(card => {
      card.addEventListener('mouseenter', () => this.highlightStat(card));
      card.addEventListener('mouseleave', () => this.unhighlightStat(card));
    });
  }

  setupScoreGrid() {
    const scoreGrid = this.container.querySelector('.score-grid');
    if (!scoreGrid) return;

    const cells = scoreGrid.querySelectorAll('.score-grid-cell');
    cells.forEach(cell => {
      cell.addEventListener('click', () => this.selectScoreline(cell));
      cell.addEventListener('mouseenter', () => this.showScoreTooltip(cell));
      cell.addEventListener('mouseleave', () => this.hideScoreTooltip());
    });
  }

  setupConfidenceMeter() {
    const confidenceMeter = this.container.querySelector('.confidence-meter');
    if (!confidenceMeter) return;

    const confidenceBar = confidenceMeter.querySelector('.confidence-fill');
    if (confidenceBar) {
      confidenceBar.style.width = '0%';
    }
  }

  setupKeyFactors() {
    const factorItems = this.container.querySelectorAll('.factor-item');
    factorItems.forEach(item => {
      item.addEventListener('click', () => this.expandFactor(item));
    });
  }

  async displayPrediction(prediction) {
    this.currentPrediction = prediction;
    this.isAnimating = true;

    // Clear previous animation queue
    this.animationQueue = [];

    // Build animation sequence
    this.animationQueue.push(() => this.animateHeaderReveal());
    this.animationQueue.push(() => this.animateProbabilityBar(prediction));
    this.animationQueue.push(() => this.animateStatsReveal(prediction));
    this.animationQueue.push(() => this.animateScoreGrid(prediction));
    this.animationQueue.push(() => this.animateConfidenceMeter(prediction));
    this.animationQueue.push(() => this.animateInsights(prediction));

    // Execute animation sequence
    for (const animation of this.animationQueue) {
      await animation();
      await this.delay(300);
    }

    this.isAnimating = false;
  }

  async animateHeaderReveal() {
    const header = this.container.querySelector('.prediction-header');
    if (header) {
      header.classList.add('animate-fade-in-down');
      await this.delay(600);
      header.classList.remove('animate-fade-in-down');
    }
  }

  async animateProbabilityBar(prediction) {
    const probBar = this.container.querySelector('.probability-bar');
    if (!probBar) return;

    const segments = probBar.querySelectorAll('.probability-segment');
    segments.forEach(segment => {
      segment.style.width = '0%';
    });

    await this.delay(100);

    if (segments[0]) segments[0].style.width = `${prediction.p_home * 100}%`;
    if (segments[1]) segments[1].style.width = `${prediction.p_draw * 100}%`;
    if (segments[2]) segments[2].style.width = `${prediction.p_away * 100}%`;

    await this.delay(800);
  }

  async animateStatsReveal(prediction) {
    const statCards = this.container.querySelectorAll('.stat-card');
    const stats = [
      { selector: '.stat-value--xg-home', value: prediction.lambda_home },
      { selector: '.stat-value--xg-away', value: prediction.lambda_away },
      { selector: '.stat-value--btts', value: prediction.p_btts },
      { selector: '.stat-value--over25', value: prediction.p_over_2_5 }
    ];

    for (let i = 0; i < statCards.length; i++) {
      const card = statCards[i];
      const statConfig = stats[i];
      
      if (card && statConfig) {
        card.classList.add('animate-scale-in');
        const valueElement = card.querySelector(statConfig.selector);
        if (valueElement) {
          await this.animateValue(valueElement, statConfig.value);
        }
        await this.delay(150);
      }
    }
  }

  async animateScoreGrid(prediction) {
    const scoreGrid = this.container.querySelector('.score-grid');
    if (!scoreGrid) return;

    const cells = scoreGrid.querySelectorAll('.score-grid-cell');
    cells.forEach(cell => {
      cell.style.opacity = '0';
      cell.style.transform = 'scale(0.8)';
    });

    await this.delay(200);

    // Animate cells in a wave pattern
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      const row = Math.floor(i / 7);
      const col = i % 7;
      const delay = (row + col) * 50;

      setTimeout(() => {
        cell.style.opacity = '1';
        cell.style.transform = 'scale(1)';
        cell.classList.add('animate-scale-in');
      }, delay);
    }

    await this.delay(1000);
  }

  async animateConfidenceMeter(prediction) {
    const confidenceMeter = this.container.querySelector('.confidence-meter');
    if (!confidenceMeter) return;

    const confidenceFill = confidenceMeter.querySelector('.confidence-fill');
    if (confidenceFill) {
      const confidence = this.calculateConfidence(prediction);
      confidenceFill.style.width = '0%';
      
      await this.delay(200);
      confidenceFill.style.width = `${confidence}%`;
      
      await this.delay(800);
    }
  }

  async animateInsights(prediction) {
    const insightsList = this.container.querySelector('.insight-list');
    if (!insightsList) return;

    const insights = insightsList.querySelectorAll('.insight-item');
    insights.forEach((insight, index) => {
      insight.style.opacity = '0';
      insight.style.transform = 'translateX(-20px)';
      
      setTimeout(() => {
        insight.style.opacity = '1';
        insight.style.transform = 'translateX(0)';
        insight.classList.add('animate-fade-in-left');
      }, index * 200);
    });

    await this.delay(insights.length * 200 + 400);
  }

  calculateConfidence(prediction) {
    // Calculate confidence based on probability distribution
    const maxProb = Math.max(prediction.p_home, prediction.p_draw, prediction.p_away);
    const minProb = Math.min(prediction.p_home, prediction.p_draw, prediction.p_away);
    const spread = maxProb - minProb;
    
    // Higher spread = higher confidence
    return Math.min(100, Math.max(0, spread * 100));
  }

  async animateValue(element, targetValue) {
    const startValue = 0;
    const duration = 500;
    const startTime = performance.now();

    const update = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentValue = startValue + (targetValue - startValue) * easeOutQuart;
      
      element.textContent = currentValue.toFixed(2);
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = targetValue.toFixed(2);
      }
    };

    requestAnimationFrame(update);
  }

  handleProbabilityBarClick(e) {
    const segment = e.target.closest('.probability-segment');
    if (!segment) return;

    const type = segment.classList.contains('probability-segment--home') ? 'home' :
                 segment.classList.contains('probability-segment--draw') ? 'draw' : 'away';

    this.showProbabilityDetails(type);
  }

  showProbabilityDetails(type) {
    // Create and show a detailed tooltip or modal
    const details = this.currentPrediction ? {
      home: {
        title: 'Home Win Probability',
        value: this.currentPrediction.p_home,
        factors: ['Home advantage', 'Attack strength', 'Opponent defense']
      },
      draw: {
        title: 'Draw Probability',
        value: this.currentPrediction.p_draw,
        factors: ['Evenly matched', 'Defensive tactics', 'Midfield battle']
      },
      away: {
        title: 'Away Win Probability',
        value: this.currentPrediction.p_away,
        factors: ['Away form', 'Counter-attack strength', 'Home vulnerability']
      }
    }[type] : null;

    if (details) {
      this.showDetailsModal(details);
    }
  }

  showDetailsModal(details) {
    // Implementation for showing detailed probability breakdown
    console.log('Showing details for:', details);
  }

  highlightStat(card) {
    card.style.transform = 'scale(1.05)';
    card.style.borderColor = 'var(--pl-purple)';
  }

  unhighlightStat(card) {
    card.style.transform = 'scale(1)';
    card.style.borderColor = 'var(--border)';
  }

  selectScoreline(cell) {
    // Deselect all cells
    const cells = this.container.querySelectorAll('.score-grid-cell');
    cells.forEach(c => c.classList.remove('score-grid-cell--selected'));

    // Select clicked cell
    cell.classList.add('score-grid-cell--selected');

    // Show scoreline details
    const homeScore = cell.dataset.homeScore;
    const awayScore = cell.dataset.awayScore;
    this.showScorelineDetails(homeScore, awayScore);
  }

  showScoreTooltip(cell) {
    const homeScore = cell.dataset.homeScore;
    const awayScore = cell.dataset.awayScore;
    const probability = cell.dataset.probability;

    const tooltip = document.createElement('div');
    tooltip.className = 'score-tooltip';
    tooltip.innerHTML = `
      <div style="font-weight: 600;">${homeScore} - ${awayScore}</div>
      <div style="font-size: 11px; color: var(--text-muted);">${(probability * 100).toFixed(1)}%</div>
    `;
    tooltip.style.cssText = `
      position: absolute;
      background: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 8px 12px;
      font-size: 12px;
      z-index: 100;
      pointer-events: none;
      white-space: nowrap;
    `;

    const rect = cell.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width / 2}px`;
    tooltip.style.top = `${rect.top - 40}px`;
    tooltip.style.transform = 'translateX(-50%)';

    document.body.appendChild(tooltip);
    this.currentTooltip = tooltip;
  }

  hideScoreTooltip() {
    if (this.currentTooltip) {
      this.currentTooltip.remove();
      this.currentTooltip = null;
    }
  }

  showScorelineDetails(homeScore, awayScore) {
    // Implementation for showing detailed scoreline analysis
    console.log(`Scoreline ${homeScore}-${awayScore} selected`);
  }

  expandFactor(factorItem) {
    const isExpanded = factorItem.classList.contains('expanded');
    
    // Collapse all factors
    const allFactors = this.container.querySelectorAll('.factor-item');
    allFactors.forEach(f => f.classList.remove('expanded'));

    // Expand clicked factor if it wasn't already expanded
    if (!isExpanded) {
      factorItem.classList.add('expanded');
    }
  }

  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  reset() {
    // Reset all animations and states
    const animatedElements = this.container.querySelectorAll('[class*="animate-"]');
    animatedElements.forEach(el => {
      el.classList.remove('animate-fade-in-down', 'animate-scale-in', 'animate-fade-in-left');
    });

    this.isAnimating = false;
    this.animationQueue = [];
  }
}

// Initialize prediction theaters on the page
document.addEventListener('DOMContentLoaded', () => {
  const theaters = document.querySelectorAll('.prediction-container');
  theaters.forEach(theater => {
    new PredictionTheater(theater.id);
  });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PredictionTheater;
}