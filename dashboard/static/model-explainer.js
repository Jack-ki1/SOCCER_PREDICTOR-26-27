/**
 * Model Explainer
 * Interactive model education and explanation system
 */

class ModelExplainer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.currentSection = 'overview';
    this.interactiveWeights = {
      attack: 0.38,
      defense: 0.27,
      form: 0.19,
      homeAdvantage: 0.16
    };

    this.init();
  }

  init() {
    this.setupNavigation();
    this.setupInteractiveVisualization();
    this.setupWeightSliders();
    this.setupModelComparison();
    this.setupAccuracyDisplay();
  }

  setupNavigation() {
    const navItems = this.container.querySelectorAll('.model-nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const section = item.dataset.section;
        this.navigateToSection(section);
      });
    });
  }

  setupInteractiveVisualization() {
    this.visualization = this.container.querySelector('.model-visualization');
    if (!this.visualization) return;

    this.createPitchVisualization();
  }

  setupWeightSliders() {
    const sliders = this.container.querySelectorAll('.weight-slider');
    sliders.forEach(slider => {
      slider.addEventListener('input', (e) => {
        const weightType = e.target.dataset.weightType;
        const value = parseFloat(e.target.value) / 100;
        this.updateWeight(weightType, value);
      });
    });
  }

  setupModelComparison() {
    const comparisonTabs = this.container.querySelectorAll('.comparison-tab');
    comparisonTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        const model = tab.dataset.model;
        this.showModelComparison(model);
      });
    });
  }

  setupAccuracyDisplay() {
    this.accuracyChart = this.container.querySelector('#accuracy-chart');
    if (this.accuracyChart && typeof Chart !== 'undefined') {
      this.createAccuracyChart();
    }
  }

  navigateToSection(section) {
    this.currentSection = section;

    // Update navigation
    const navItems = this.container.querySelectorAll('.model-nav-item');
    navItems.forEach(item => {
      item.classList.toggle('active', item.dataset.section === section);
    });

    // Update content sections
    const sections = this.container.querySelectorAll('.model-section');
    sections.forEach(sec => {
      sec.classList.toggle('active', sec.dataset.section === section);
    });
  }

  createPitchVisualization() {
    const pitchContainer = this.visualization.querySelector('.pitch-container');
    if (!pitchContainer) return;

    pitchContainer.innerHTML = `
      <div class="pitch-model">
        <div class="pitch-model-line pitch-model-line--half"></div>
        <div class="pitch-model-circle"></div>
        
        <div class="pitch-token pitch-token--a" data-factor="attack">
          <span class="pitch-token-label">Attack</span>
          <span class="pitch-token-value">${Math.round(this.interactiveWeights.attack * 100)}%</span>
        </div>
        
        <div class="pitch-token pitch-token--b" data-factor="defense">
          <span class="pitch-token-label">Defense</span>
          <span class="pitch-token-value">${Math.round(this.interactiveWeights.defense * 100)}%</span>
        </div>
        
        <div class="pitch-token pitch-token--c" data-factor="form">
          <span class="pitch-token-label">Form</span>
          <span class="pitch-token-value">${Math.round(this.interactiveWeights.form * 100)}%</span>
        </div>
        
        <div class="pitch-token pitch-token--d" data-factor="homeAdvantage">
          <span class="pitch-token-label">Home</span>
          <span class="pitch-token-value">${Math.round(this.interactiveWeights.homeAdvantage * 100)}%</span>
        </div>
        
        <div class="pitch-model-centre">
          <span class="pitch-model-label">DC</span>
          <span class="pitch-model-sublabel">MODEL</span>
        </div>
      </div>
    `;

    // Add interactivity to tokens
    const tokens = pitchContainer.querySelectorAll('.pitch-token');
    tokens.forEach(token => {
      token.addEventListener('click', () => {
        const factor = token.dataset.factor;
        this.highlightFactor(factor);
      });
    });
  }

  updateWeight(factorType, value) {
    this.interactiveWeights[factorType] = value;

    // Normalize weights to sum to 1
    const total = Object.values(this.interactiveWeights).reduce((sum, val) => sum + val, 0);
    Object.keys(this.interactiveWeights).forEach(key => {
      this.interactiveWeights[key] /= total;
    });

    // Update visualization
    this.updatePitchVisualization();
    this.updateWeightSliders();
    this.updatePredictionImpact();
  }

  updatePitchVisualization() {
    const tokens = this.visualization.querySelectorAll('.pitch-token');
    tokens.forEach(token => {
      const factor = token.dataset.factor;
      const value = this.interactiveWeights[factor];
      const valueElement = token.querySelector('.pitch-token-value');
      if (valueElement) {
        valueElement.textContent = `${Math.round(value * 100)}%`;
      }
      
      // Update size based on weight
      const scale = 0.8 + (value * 0.4);
      token.style.transform = `scale(${scale})`;
    });
  }

  updateWeightSliders() {
    const sliders = this.container.querySelectorAll('.weight-slider');
    sliders.forEach(slider => {
      const weightType = slider.dataset.weightType;
      const value = this.interactiveWeights[weightType];
      slider.value = Math.round(value * 100);
    });
  }

  updatePredictionImpact() {
    const impactDisplay = this.container.querySelector('.prediction-impact');
    if (!impactDisplay) return;

    // Calculate how weight changes would affect a sample prediction
    const samplePrediction = this.calculateSamplePrediction();
    
    impactDisplay.innerHTML = `
      <div class="impact-preview">
        <div class="impact-title">Sample Prediction Impact</div>
        <div class="impact-bars">
          <div class="impact-bar">
            <span class="impact-label">Home Win</span>
            <div class="impact-bar-fill" style="width: ${samplePrediction.home * 100}%;"></div>
            <span class="impact-value">${(samplePrediction.home * 100).toFixed(1)}%</span>
          </div>
          <div class="impact-bar">
            <span class="impact-label">Draw</span>
            <div class="impact-bar-fill" style="width: ${samplePrediction.draw * 100}%;"></div>
            <span class="impact-value">${(samplePrediction.draw * 100).toFixed(1)}%</span>
          </div>
          <div class="impact-bar">
            <span class="impact-label">Away Win</span>
            <div class="impact-bar-fill" style="width: ${samplePrediction.away * 100}%;"></div>
            <span class="impact-value">${(samplePrediction.away * 100).toFixed(1)}%</span>
          </div>
        </div>
      </div>
    `;
  }

  calculateSamplePrediction() {
    // Simplified sample prediction based on current weights
    const baseHome = 0.45;
    const baseDraw = 0.25;
    const baseAway = 0.30;

    const homeBoost = (this.interactiveWeights.attack + this.interactiveWeights.homeAdvantage) * 0.1;
    const awayBoost = this.interactiveWeights.defense * 0.05;

    let home = baseHome + homeBoost;
    let away = baseAway + awayBoost;
    let draw = baseDraw;

    // Normalize
    const total = home + draw + away;
    home /= total;
    draw /= total;
    away /= total;

    return { home, draw, away };
  }

  highlightFactor(factor) {
    const tokens = this.visualization.querySelectorAll('.pitch-token');
    tokens.forEach(token => {
      if (token.dataset.factor === factor) {
        token.classList.add('highlighted');
      } else {
        token.classList.remove('highlighted');
      }
    });

    // Show factor explanation
    this.showFactorExplanation(factor);
  }

  showFactorExplanation(factor) {
    const explanations = {
      attack: 'Attack strength measures a team\'s ability to create and convert scoring chances based on historical performance, player quality, and tactical approach.',
      defense: 'Defense strength evaluates a team\'s ability to prevent opponents from scoring, considering defensive organization, goalkeeper quality, and pressing effectiveness.',
      form: 'Form captures recent performance trends, giving more weight to a team\'s last 5-10 matches to reflect current momentum and confidence levels.',
      homeAdvantage: 'Home advantage accounts for the well-documented boost teams receive when playing at their home stadium, including crowd support and familiarity.'
    };

    const explanationBox = this.container.querySelector('.factor-explanation');
    if (explanationBox) {
      explanationBox.innerHTML = `
        <div class="explanation-title">${factor.charAt(0).toUpperCase() + factor.slice(1)} Factor</div>
        <div class="explanation-text">${explanations[factor]}</div>
        <div class="explanation-weight">Current weight: ${Math.round(this.interactiveWeights[factor] * 100)}%</div>
      `;
      explanationBox.classList.add('animate-fade-in');
    }
  }

  showModelComparison(model) {
    const comparisonContent = this.container.querySelector('.comparison-content');
    if (!comparisonContent) return;

    const modelData = {
      'dixon-coles': {
        name: 'Dixon-Coles',
        description: 'A bivariate Poisson model with a low-score correlation adjustment that accounts for the tendency of football matches to end in low-scoring draws.',
        strengths: ['Well-established in football analytics', 'Handles low-score correlations', 'Interpretable parameters'],
        weaknesses: ['Doesn\'t incorporate player-level data', 'Limited tactical factors'],
        accuracy: '72%'
      },
      'poisson': {
        name: 'Basic Poisson',
        description: 'A simple Poisson distribution model that assumes goals are independent events occurring at a constant rate.',
        strengths: ['Simple and fast', 'Easy to understand', 'Good baseline'],
        weaknesses: ['Ignores score correlation', 'Less accurate for low scores'],
        accuracy: '65%'
      },
      'random-forest': {
        name: 'Random Forest',
        description: 'A machine learning ensemble method that uses multiple decision trees to predict match outcomes based on various features.',
        strengths: ['Handles complex interactions', 'Incorporates many features', 'Non-linear relationships'],
        weaknesses: ['Less interpretable', 'Requires more data', 'Can overfit'],
        accuracy: '74%'
      }
    };

    const model = modelData[model];
    comparisonContent.innerHTML = `
      <div class="model-details animate-fade-in">
        <div class="model-header">
          <h3>${model.name}</h3>
          <div class="model-accuracy">${model.accuracy} accuracy</div>
        </div>
        <p class="model-description">${model.description}</p>
        
        <div class="model-factors">
          <div class="factor-section">
            <h4>Strengths</h4>
            <ul>
              ${model.strengths.map(s => `<li>${s}</li>`).join('')}
            </ul>
          </div>
          <div class="factor-section">
            <h4>Weaknesses</h4>
            <ul>
              ${model.weaknesses.map(w => `<li>${w}</li>`).join('')}
            </ul>
          </div>
        </div>
      </div>
    `;
  }

  createAccuracyChart() {
    const ctx = this.accuracyChart.getContext('2d');
    
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: ['Week 1', 'Week 5', 'Week 10', 'Week 15', 'Week 20', 'Week 25', 'Week 30', 'Week 35'],
        datasets: [
          {
            label: 'Dixon-Coles',
            data: [68, 71, 73, 72, 74, 73, 75, 72],
            borderColor: '#6b21a8',
            backgroundColor: 'rgba(107, 33, 168, 0.1)',
            tension: 0.4
          },
          {
            label: 'Random Forest',
            data: [65, 68, 70, 71, 73, 74, 76, 74],
            borderColor: '#00ff85',
            backgroundColor: 'rgba(0, 255, 133, 0.1)',
            tension: 0.4
          },
          {
            label: 'Basic Poisson',
            data: [60, 63, 65, 64, 66, 65, 67, 65],
            borderColor: '#ffd700',
            backgroundColor: 'rgba(255, 215, 0, 0.1)',
            tension: 0.4
          }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: false,
            min: 50,
            max: 85,
            ticks: {
              callback: value => value + '%'
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

  reset() {
    this.interactiveWeights = {
      attack: 0.38,
      defense: 0.27,
      form: 0.19,
      homeAdvantage: 0.16
    };
    this.updatePitchVisualization();
    this.updateWeightSliders();
    this.navigateToSection('overview');
  }
}

// Initialize model explainers on the page
document.addEventListener('DOMContentLoaded', () => {
  const explainers = document.querySelectorAll('.model-explainer-container');
  explainers.forEach(explainer => {
    new ModelExplainer(explainer.id);
  });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModelExplainer;
}