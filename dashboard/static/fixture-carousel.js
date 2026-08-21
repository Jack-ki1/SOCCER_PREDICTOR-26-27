/**
 * Fixture Carousel
 * Interactive fixture browsing with smooth scrolling and filtering
 */

class FixtureCarousel {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) return;

    this.options = {
      itemsPerView: options.itemsPerView || 3,
      gap: options.gap || 16,
      autoScroll: options.autoScroll || false,
      autoScrollInterval: options.autoScrollInterval || 5000,
      ...options
    };

    this.track = this.container.querySelector('.fixture-carousel-track');
    this.items = this.container.querySelectorAll('.fixture-card');
    this.currentIndex = 0;
    this.autoScrollTimer = null;

    this.init();
  }

  init() {
    this.setupNavigation();
    this.setupKeyboardNavigation();
    this.setupTouchGestures();
    this.setupFavoriteButtons();
    
    if (this.options.autoScroll) {
      this.startAutoScroll();
    }

    // Add scroll snap behavior
    this.track.style.scrollSnapType = 'x mandatory';
    this.track.style.scrollBehavior = 'smooth';
  }

  setupNavigation() {
    const prevBtn = this.container.querySelector('.carousel-btn--prev');
    const nextBtn = this.container.querySelector('.carousel-btn--next');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => this.scrollPrev());
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => this.scrollNext());
    }

    this.updateNavigationButtons();
  }

  setupKeyboardNavigation() {
    this.container.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowLeft') {
        this.scrollPrev();
      } else if (e.key === 'ArrowRight') {
        this.scrollNext();
      }
    });
  }

  setupTouchGestures() {
    let startX = 0;
    let currentX = 0;
    let isDragging = false;

    this.track.addEventListener('touchstart', (e) => {
      startX = e.touches[0].clientX;
      isDragging = true;
    });

    this.track.addEventListener('touchmove', (e) => {
      if (!isDragging) return;
      currentX = e.touches[0].clientX;
    });

    this.track.addEventListener('touchend', () => {
      if (!isDragging) return;
      isDragging = false;

      const diff = startX - currentX;
      const threshold = 50;

      if (diff > threshold) {
        this.scrollNext();
      } else if (diff < -threshold) {
        this.scrollPrev();
      }
    });
  }

  setupFavoriteButtons() {
    const favoriteButtons = this.container.querySelectorAll('.favorite-btn');
    favoriteButtons.forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.toggleFavorite(btn);
      });
    });
  }

  toggleFavorite(button) {
    button.classList.toggle('active');
    
    const fixtureCard = button.closest('.fixture-card');
    const fixtureId = fixtureCard.dataset.fixtureId;
    
    // Save to localStorage
    const favorites = this.getFavorites();
    if (button.classList.contains('active')) {
      favorites.add(fixtureId);
      this.showFavoriteNotification(fixtureCard, 'added to favorites');
    } else {
      favorites.delete(fixtureId);
      this.showFavoriteNotification(fixtureCard, 'removed from favorites');
    }
    localStorage.setItem('favorite-fixtures', JSON.stringify([...favorites]));
  }

  getFavorites() {
    const stored = localStorage.getItem('favorite-fixtures');
    return stored ? new Set(JSON.parse(stored)) : new Set();
  }

  showFavoriteNotification(fixtureCard, message) {
    const notification = document.createElement('div');
    notification.className = 'favorite-notification';
    notification.textContent = message;
    notification.style.cssText = `
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 8px 16px;
      border-radius: 4px;
      font-size: 12px;
      z-index: 10;
      animation: fadeInOut 2s ease forwards;
    `;
    
    fixtureCard.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
  }

  scrollNext() {
    if (this.currentIndex < this.items.length - 1) {
      this.currentIndex++;
      this.scrollToItem(this.currentIndex);
    } else {
      // Loop back to start
      this.currentIndex = 0;
      this.scrollToItem(0);
    }
    this.updateNavigationButtons();
  }

  scrollPrev() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
      this.scrollToItem(this.currentIndex);
    } else {
      // Loop to end
      this.currentIndex = this.items.length - 1;
      this.scrollToItem(this.currentIndex);
    }
    this.updateNavigationButtons();
  }

  scrollToItem(index) {
    const item = this.items[index];
    if (item) {
      item.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'start' });
    }
  }

  updateNavigationButtons() {
    const prevBtn = this.container.querySelector('.carousel-btn--prev');
    const nextBtn = this.container.querySelector('.carousel-btn--next');

    if (prevBtn) {
      prevBtn.disabled = this.items.length <= 1;
    }
    if (nextBtn) {
      nextBtn.disabled = this.items.length <= 1;
    }
  }

  startAutoScroll() {
    this.autoScrollTimer = setInterval(() => {
      this.scrollNext();
    }, this.options.autoScrollInterval);
  }

  stopAutoScroll() {
    if (this.autoScrollTimer) {
      clearInterval(this.autoScrollTimer);
      this.autoScrollTimer = null;
    }
  }

  filterFixtures(filterFn) {
    this.items.forEach(item => {
      if (filterFn(item)) {
        item.style.display = '';
      } else {
        item.style.display = 'none';
      }
    });
  }

  resetFilters() {
    this.items.forEach(item => {
      item.style.display = '';
    });
  }

  selectFixture(fixtureId) {
    this.items.forEach(item => {
      item.classList.remove('selected');
      if (item.dataset.fixtureId === fixtureId) {
        item.classList.add('selected');
      }
    });
  }

  destroy() {
    this.stopAutoScroll();
    // Remove event listeners and clean up
  }
}

// Initialize fixture carousels on the page
document.addEventListener('DOMContentLoaded', () => {
  const carousels = document.querySelectorAll('.fixture-carousel');
  carousels.forEach(carousel => {
    new FixtureCarousel(carousel.id, {
      itemsPerView: 3,
      gap: 16,
      autoScroll: false
    });
  });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FixtureCarousel;
}