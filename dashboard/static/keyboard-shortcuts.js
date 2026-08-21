/**
 * Keyboard Shortcuts
 * Power user keyboard navigation and shortcuts
 */

class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.helpVisible = false;
    this.helpModal = null;

    this.init();
  }

  init() {
    this.registerDefaultShortcuts();
    this.setupEventListeners();
    this.createHelpModal();
  }

  registerDefaultShortcuts() {
    // Navigation shortcuts
    this.register('Ctrl+K', 'Focus search', () => this.focusSearch());
    this.register('Ctrl+/', 'Show keyboard shortcuts', () => this.toggleHelp());
    this.register('Escape', 'Close modals', () => this.closeModals());
    this.register('Ctrl+H', 'Go to homepage', () => this.navigate('/'));
    this.register('Ctrl+D', 'Go to dashboard', () => this.navigate('/dashboard'));
    this.register('Ctrl+T', 'Go to table', () => this.navigate('/table'));
    this.register('Ctrl+F', 'Go to fixtures', () => this.navigate('/fixtures'));
    this.register('Ctrl+A', 'Go to analytics', () => this.navigate('/analytics'));
    this.register('Ctrl+L', 'Go to FPL Lab', () => this.navigate('/fpl_lab'));

    // Action shortcuts
    this.register('Ctrl+R', 'Run prediction', () => this.runPrediction());
    this.register('Ctrl+S', 'Run simulation', () => this.runSimulation());
    this.register('Ctrl+N', 'New prediction', () => this.newPrediction());
    this.register('Ctrl+E', 'Export data', () => this.exportData());

    // Navigation within pages
    this.register('ArrowLeft', 'Previous fixture', () => this.previousFixture());
    this.register('ArrowRight', 'Next fixture', () => this.nextFixture());
    this.register('ArrowUp', 'Scroll up', () => this.scrollUp());
    this.register('ArrowDown', 'Scroll down', () => this.scrollDown());
    this.register('Home', 'Go to top', () => this.scrollToTop());
    this.register('End', 'Go to bottom', () => this.scrollToBottom());

    // Utility shortcuts
    this.register('Ctrl+T', 'Toggle theme', () => this.toggleTheme());
    this.register('Ctrl+M', 'Toggle mobile menu', () => this.toggleMobileMenu());
  }

  register(shortcut, description, callback) {
    this.shortcuts.set(shortcut, { description, callback });
  }

  setupEventListeners() {
    document.addEventListener('keydown', (e) => {
      // Don't trigger shortcuts when typing in input fields
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) {
        return;
      }

      const shortcut = this.getShortcutString(e);
      if (this.shortcuts.has(shortcut)) {
        e.preventDefault();
        const { callback } = this.shortcuts.get(shortcut);
        callback();
      }
    });
  }

  getShortcutString(event) {
    const parts = [];
    
    if (event.ctrlKey) parts.push('Ctrl');
    if (event.altKey) parts.push('Alt');
    if (event.shiftKey) parts.push('Shift');
    if (event.metaKey) parts.push('Meta');
    
    if (event.key && event.key !== 'Control' && event.key !== 'Alt' && event.key !== 'Shift' && event.key !== 'Meta') {
      parts.push(event.key);
    }
    
    return parts.join('+');
  }

  createHelpModal() {
    this.helpModal = document.createElement('div');
    this.helpModal.className = 'keyboard-shortcuts-modal';
    this.helpModal.innerHTML = `
      <div class="modal-backdrop" onclick="keyboardShortcuts.toggleHelp()"></div>
      <div class="modal-content">
        <div class="modal-header">
          <h3>Keyboard Shortcuts</h3>
          <button class="modal-close" onclick="keyboardShortcuts.toggleHelp()">×</button>
        </div>
        <div class="modal-body">
          <div class="shortcuts-grid">
            ${this.renderShortcutsGrid()}
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" onclick="keyboardShortcuts.toggleHelp()">Close</button>
        </div>
      </div>
    `;
    
    this.helpModal.style.display = 'none';
    document.body.appendChild(this.helpModal);
  }

  renderShortcutsGrid() {
    const categories = {
      'Navigation': [],
      'Actions': [],
      'Page Navigation': [],
      'Utility': []
    };

    this.shortcuts.forEach(({ description }, shortcut) => {
      if (shortcut.includes('Ctrl+') && (shortcut.includes('H') || shortcut.includes('D') || shortcut.includes('T') || shortcut.includes('F') || shortcut.includes('A') || shortcut.includes('L'))) {
        categories['Navigation'].push({ shortcut, description });
      } else if (shortcut.includes('Ctrl+') && (shortcut.includes('R') || shortcut.includes('S') || shortcut.includes('N') || shortcut.includes('E'))) {
        categories['Actions'].push({ shortcut, description });
      } else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(shortcut)) {
        categories['Page Navigation'].push({ shortcut, description });
      } else {
        categories['Utility'].push({ shortcut, description });
      }
    });

    return Object.entries(categories).map(([category, shortcuts]) => `
      <div class="shortcut-category">
        <h4>${category}</h4>
        <div class="shortcut-list">
          ${shortcuts.map(({ shortcut, description }) => `
            <div class="shortcut-item">
              <kbd class="shortcut-key">${this.formatShortcut(shortcut)}</kbd>
              <span class="shortcut-description">${description}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');
  }

  formatShortcut(shortcut) {
    return shortcut.split('+').map(part => {
      if (part === 'Ctrl') return '⌃';
      if (part === 'Alt') return '⌥';
      if (part === 'Shift') return '⇧';
      if (part === 'Meta') return '⌘';
      if (part === 'ArrowLeft') return '←';
      if (part === 'ArrowRight') return '→';
      if (part === 'ArrowUp') return '↑';
      if (part === 'ArrowDown') return '↓';
      return part.length === 1 ? part.toUpperCase() : part;
    }).join('');
  }

  toggleHelp() {
    this.helpVisible = !this.helpVisible;
    this.helpModal.style.display = this.helpVisible ? 'block' : 'none';
    
    if (this.helpVisible) {
      this.helpModal.querySelector('.modal-content').classList.add('animate-scale-in');
    }
  }

  // Shortcut implementations
  focusSearch() {
    const searchInput = document.querySelector('.fixture-search-input, [type="search"]');
    if (searchInput) {
      searchInput.focus();
      searchInput.select();
    }
  }

  closeModals() {
    // Close any open modals
    const modals = document.querySelectorAll('.modal-backdrop.visible');
    modals.forEach(modal => {
      modal.classList.remove('visible');
    });
    
    // Close help if visible
    if (this.helpVisible) {
      this.toggleHelp();
    }
  }

  navigate(path) {
    window.location.href = path;
  }

  runPrediction() {
    const runButton = document.querySelector('#run-prediction-btn, [onclick*="runPrediction"]');
    if (runButton) {
      runButton.click();
    }
  }

  runSimulation() {
    const runButton = document.querySelector('#run-simulation-btn, [onclick*="runSimulation"]');
    if (runButton) {
      runButton.click();
    }
  }

  newPrediction() {
    this.navigate('/dashboard');
    setTimeout(() => {
      const firstFixture = document.querySelector('#fixture-picker button');
      if (firstFixture) {
        firstFixture.click();
      }
    }, 100);
  }

  exportData() {
    this.navigate('/download');
  }

  previousFixture() {
    const carousel = document.querySelector('.fixture-carousel');
    if (carousel) {
      const prevBtn = carousel.querySelector('.carousel-btn--prev');
      if (prevBtn) prevBtn.click();
    }
  }

  nextFixture() {
    const carousel = document.querySelector('.fixture-carousel');
    if (carousel) {
      const nextBtn = carousel.querySelector('.carousel-btn--next');
      if (nextBtn) nextBtn.click();
    }
  }

  scrollUp() {
    window.scrollBy({ top: -200, behavior: 'smooth' });
  }

  scrollDown() {
    window.scrollBy({ top: 200, behavior: 'smooth' });
  }

  scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
  }

  toggleTheme() {
    const themeToggle = document.querySelector('.theme-toggle');
    if (themeToggle) {
      themeToggle.click();
    }
  }

  toggleMobileMenu() {
    const navToggle = document.querySelector('.nav-toggle');
    if (navToggle) {
      navToggle.click();
    }
  }

  // Add custom shortcut
  addCustomShortcut(shortcut, description, callback) {
    this.register(shortcut, description, callback);
    this.updateHelpModal();
  }

  updateHelpModal() {
    const shortcutsGrid = this.helpModal.querySelector('.shortcuts-grid');
    if (shortcutsGrid) {
      shortcutsGrid.innerHTML = this.renderShortcutsGrid();
    }
  }

  // Remove shortcut
  removeShortcut(shortcut) {
    this.shortcuts.delete(shortcut);
    this.updateHelpModal();
  }

  // Get all shortcuts
  getAllShortcuts() {
    return Object.fromEntries(this.shortcuts);
  }

  // Export shortcuts for documentation
  exportShortcuts() {
    const shortcuts = {};
    this.shortcuts.forEach(({ description }, shortcut) => {
      shortcuts[shortcut] = description;
    });
    return shortcuts;
  }
}

// Initialize keyboard shortcuts globally
const keyboardShortcuts = new KeyboardShortcuts();

// Make it available globally for the help modal
window.keyboardShortcuts = keyboardShortcuts;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = KeyboardShortcuts;
}