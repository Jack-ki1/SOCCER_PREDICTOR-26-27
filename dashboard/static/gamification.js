/**
 * Gamification System
 * User engagement features, achievements, and prediction tracking
 */

class GamificationSystem {
  constructor() {
    this.userProgress = this.loadUserProgress();
    this.achievements = this.defineAchievements();
    this.streaks = this.loadStreaks();
    this.badges = this.loadBadges();
    
    this.init();
  }

  init() {
    this.setupPredictionTracking();
    this.setupAchievementSystem();
    this.setupStreakTracking();
    this.setupLeaderboard();
    this.setupBadges();
  }

  loadUserProgress() {
    const saved = localStorage.getItem('epl-predictor-progress');
    return saved ? JSON.parse(saved) : {
      predictionsMade: 0,
      correctPredictions: 0,
      accuracy: 0,
      simulationsRun: 0,
      teamsAnalyzed: new Set(),
      fixturesExplored: new Set(),
      lastActiveDate: null,
      consecutiveDays: 0
    };
  }

  saveUserProgress() {
    // Convert Sets to Arrays for JSON serialization
    const toSave = {
      ...this.userProgress,
      teamsAnalyzed: Array.from(this.userProgress.teamsAnalyzed),
      fixturesExplored: Array.from(this.userProgress.fixturesExplored)
    };
    localStorage.setItem('epl-predictor-progress', JSON.stringify(toSave));
  }

  defineAchievements() {
    return [
      {
        id: 'first-prediction',
        name: 'First Steps',
        description: 'Make your first prediction',
        icon: '🎯',
        condition: () => this.userProgress.predictionsMade >= 1,
        reward: 'Novice Analyst Badge'
      },
      {
        id: 'prediction-streak-5',
        name: 'Hot Streak',
        description: 'Make predictions on 5 consecutive days',
        icon: '🔥',
        condition: () => this.userProgress.consecutiveDays >= 5,
        reward: 'Streak Master Badge'
      },
      {
        id: 'simulation-runner',
        name: 'Season Simulator',
        description: 'Run 10 season simulations',
        icon: '🎲',
        condition: () => this.userProgress.simulationsRun >= 10,
        reward: 'Simulation Expert Badge'
      },
      {
        id: 'team-explorer',
        name: 'Team Explorer',
        description: 'Analyze all 20 teams',
        icon: '🔍',
        condition: () => this.userProgress.teamsAnalyzed.size >= 20,
        reward: 'League Encyclopedia Badge'
      },
      {
        id: 'fixture-expert',
        name: 'Fixture Expert',
        description: 'Explore 50 different fixtures',
        icon: '📊',
        condition: () => this.userProgress.fixturesExplored.size >= 50,
        reward: 'Fixture Guru Badge'
      },
      {
        id: 'accuracy-70',
        name: 'Sharpshooter',
        description: 'Achieve 70% prediction accuracy',
        icon: '🎯',
        condition: () => this.userProgress.accuracy >= 0.7,
        reward: 'Precision Badge'
      },
      {
        id: 'perfect-week',
        name: 'Perfect Week',
        description: 'Get all matchday predictions correct',
        icon: '⭐',
        condition: () => this.checkPerfectWeek(),
        reward: 'Perfectionist Badge'
      },
      {
        id: 'night-owl',
        name: 'Night Owl',
        description: 'Make a prediction after midnight',
        icon: '🦉',
        condition: () => this.checkNightPrediction(),
        reward: 'Night Analyst Badge'
      }
    ];
  }

  setupPredictionTracking() {
    // Track when users make predictions
    document.addEventListener('predictionMade', (e) => {
      this.recordPrediction(e.detail);
    });
  }

  recordPrediction(predictionData) {
    this.userProgress.predictionsMade++;
    
    if (predictionData.correct) {
      this.userProgress.correctPredictions++;
    }
    
    this.userProgress.accuracy = this.userProgress.correctPredictions / this.userProgress.predictionsMade;
    
    // Track fixture exploration
    if (predictionData.fixtureId) {
      this.userProgress.fixturesExplored.add(predictionData.fixtureId);
    }
    
    // Update daily streak
    this.updateDailyStreak();
    
    this.saveUserProgress();
    this.checkAchievements();
  }

  updateDailyStreak() {
    const today = new Date().toDateString();
    const lastActive = this.userProgress.lastActiveDate;
    
    if (lastActive !== today) {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      
      if (lastActive === yesterday.toDateString()) {
        this.userProgress.consecutiveDays++;
      } else if (lastActive !== today) {
        this.userProgress.consecutiveDays = 1;
      }
      
      this.userProgress.lastActiveDate = today;
    }
  }

  setupAchievementSystem() {
    // Create achievement notification container
    this.createAchievementContainer();
    
    // Check achievements periodically
    setInterval(() => this.checkAchievements(), 30000);
  }

  createAchievementContainer() {
    let container = document.getElementById('achievement-container');
    
    if (!container) {
      container = document.createElement('div');
      container.id = 'achievement-container';
      container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        gap: 10px;
      `;
      document.body.appendChild(container);
    }
  }

  checkAchievements() {
    this.achievements.forEach(achievement => {
      if (!this.hasAchievement(achievement.id) && achievement.condition()) {
        this.unlockAchievement(achievement);
      }
    });
  }

  hasAchievement(achievementId) {
    return this.badges.includes(achievementId);
  }

  unlockAchievement(achievement) {
    this.badges.push(achievement.id);
    this.saveBadges();
    this.showAchievementNotification(achievement);
    this.rewardUser(achievement);
  }

  showAchievementNotification(achievement) {
    const container = document.getElementById('achievement-container');
    
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    notification.innerHTML = `
      <div class="achievement-popup animate-bounce-in">
        <div class="achievement-icon">${achievement.icon}</div>
        <div class="achievement-content">
          <div class="achievement-title">Achievement Unlocked!</div>
          <div class="achievement-name">${achievement.name}</div>
          <div class="achievement-description">${achievement.description}</div>
          <div class="achievement-reward">🎁 ${achievement.reward}</div>
        </div>
        <button class="achievement-close" onclick="this.parentElement.remove()">×</button>
      </div>
    `;
    
    notification.style.cssText = `
      background: linear-gradient(135deg, var(--pl-gold), var(--pl-gold-dark));
      border-radius: 12px;
      padding: 16px;
      color: #1a1a2e;
      box-shadow: 0 4px 20px rgba(255, 215, 0, 0.4);
      max-width: 300px;
    `;
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      notification.style.animation = 'fadeOutRight 0.5s ease';
      setTimeout(() => notification.remove(), 500);
    }, 5000);
  }

  rewardUser(achievement) {
    // Implement reward logic (badges, points, etc.)
    console.log(`User rewarded: ${achievement.reward}`);
  }

  setupStreakTracking() {
    // Track user activity streaks
    this.updateDailyStreak();
  }

  loadStreaks() {
    const saved = localStorage.getItem('epl-predictor-streaks');
    return saved ? JSON.parse(saved) : {
      currentStreak: 0,
      longestStreak: 0,
      lastActiveDate: null
    };
  }

  setupLeaderboard() {
    // Create local leaderboard
    this.leaderboard = this.loadLeaderboard();
    this.updateLeaderboard();
  }

  loadLeaderboard() {
    const saved = localStorage.getItem('epl-predictor-leaderboard');
    return saved ? JSON.parse(saved) : [];
  }

  updateLeaderboard() {
    const userEntry = {
      username: this.getUsername(),
      score: this.calculateScore(),
      predictions: this.userProgress.predictionsMade,
      accuracy: this.userProgress.accuracy,
      lastActive: new Date().toISOString()
    };
    
    // Update or add user entry
    const existingIndex = this.leaderboard.findIndex(e => e.username === userEntry.username);
    if (existingIndex >= 0) {
      this.leaderboard[existingIndex] = userEntry;
    } else {
      this.leaderboard.push(userEntry);
    }
    
    // Sort by score
    this.leaderboard.sort((a, b) => b.score - a.score);
    
    // Keep top 100
    this.leaderboard = this.leaderboard.slice(0, 100);
    
    localStorage.setItem('epl-predictor-leaderboard', JSON.stringify(this.leaderboard));
  }

  calculateScore() {
    // Calculate engagement score
    return (
      this.userProgress.predictionsMade * 10 +
      this.userProgress.simulationsRun * 25 +
      this.userProgress.teamsAnalyzed.size * 5 +
      this.userProgress.fixturesExplored.size * 2 +
      this.badges.length * 100 +
      this.userProgress.consecutiveDays * 15
    );
  }

  getUsername() {
    return localStorage.getItem('epl-predictor-username') || 'Anonymous';
  }

  setUsername(username) {
    localStorage.setItem('epl-predictor-username', username);
  }

  setupBadges() {
    // Create badge display
    this.createBadgeDisplay();
  }

  loadBadges() {
    const saved = localStorage.getItem('epl-predictor-badges');
    return saved ? JSON.parse(saved) : [];
  }

  saveBadges() {
    localStorage.setItem('epl-predictor-badges', JSON.stringify(this.badges));
  }

  createBadgeDisplay() {
    // This would create a badge display UI component
    // Implementation depends on where you want to show badges
  }

  getBadges() {
    return this.achievements.filter(a => this.badges.includes(a.id));
  }

  getProgress() {
    return {
      ...this.userProgress,
      teamsAnalyzed: this.userProgress.teamsAnalyzed.size,
      fixturesExplored: this.userProgress.fixturesExplored.size,
      score: this.calculateScore(),
      badgeCount: this.badges.length,
      totalAchievements: this.achievements.length
    };
  }

  // Helper methods for achievement conditions
  checkPerfectWeek() {
    // Implement logic to check if user got all predictions correct in a week
    return false; // Placeholder
  }

  checkNightPrediction() {
    const hour = new Date().getHours();
    return hour >= 0 && hour < 4;
  }

  // Integration with prediction system
  trackSimulation() {
    this.userProgress.simulationsRun++;
    this.saveUserProgress();
    this.checkAchievements();
  }

  trackTeamAnalysis(teamId) {
    this.userProgress.teamsAnalyzed.add(teamId);
    this.saveUserProgress();
    this.checkAchievements();
  }

  // Reset progress (for testing or user request)
  resetProgress() {
    if (confirm('Are you sure you want to reset all your progress? This cannot be undone.')) {
      localStorage.removeItem('epl-predictor-progress');
      localStorage.removeItem('epl-predictor-badges');
      localStorage.removeItem('epl-predictor-streaks');
      this.userProgress = this.loadUserProgress();
      this.badges = this.loadBadges();
      this.streaks = this.loadStreaks();
    }
  }

  // Export/Import progress
  exportProgress() {
    const data = {
      progress: this.userProgress,
      badges: this.badges,
      streaks: this.streaks,
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `epl-predictor-progress-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    
    URL.revokeObjectURL(url);
  }

  importProgress(jsonData) {
    try {
      const data = JSON.parse(jsonData);
      
      this.userProgress = {
        ...data.progress,
        teamsAnalyzed: new Set(data.progress.teamsAnalyzed || []),
        fixturesExplored: new Set(data.progress.fixturesExplored || [])
      };
      this.badges = data.badges || [];
      this.streaks = data.streaks || this.loadStreaks();
      
      this.saveUserProgress();
      this.saveBadges();
      
      return true;
    } catch (error) {
      console.error('Failed to import progress:', error);
      return false;
    }
  }
}

// Initialize gamification system
const gamification = new GamificationSystem();

// Make it globally available for integration
window.gamification = gamification;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = GamificationSystem;
}