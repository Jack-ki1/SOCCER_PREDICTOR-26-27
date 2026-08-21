/**
 * Animation Orchestrator
 * Central animation management for EPL Predictor
 */

class AnimationOrchestrator {
  constructor() {
    this.observers = new Map();
    this.timers = new Set();
    this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  /**
   * Initialize all animations on the page
   */
  init() {
    if (this.isReducedMotion) return;
    
    this.initScrollAnimations();
    this.initLoadAnimations();
    this.initHoverAnimations();
  }

  /**
   * Initialize scroll-triggered animations
   */
  initScrollAnimations() {
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.triggerAnimation(entry.target);
          observer.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    animatedElements.forEach(el => observer.observe(el));
    this.observers.set('scroll', observer);
  }

  /**
   * Initialize page load animations
   */
  initLoadAnimations() {
    // Staggered fade-in for hero content
    const heroElements = document.querySelectorAll('.home-hero__copy > *');
    heroElements.forEach((el, index) => {
      el.style.opacity = '0';
      el.style.animation = `fadeInUp 0.6s ease forwards ${index * 0.1}s`;
    });

    // Card entrance animations
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
      card.classList.add('card-entrance');
      card.style.animationDelay = `${index * 0.05}s`;
    });
  }

  /**
   * Initialize hover animations
   */
  initHoverAnimations() {
    // Enhanced button hover effects
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(btn => {
      btn.addEventListener('mouseenter', () => {
        this.createRippleEffect(btn);
      });
    });

    // Card hover effects
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        card.classList.add('hover-lift');
      });
      card.addEventListener('mouseleave', () => {
        card.classList.remove('hover-lift');
      });
    });
  }

  /**
   * Trigger a specific animation on an element
   */
  triggerAnimation(element, animationClass = 'animate-fade-in-up') {
    element.classList.add(animationClass);
    element.addEventListener('animationend', () => {
      element.classList.remove(animationClass);
    }, { once: true });
  }

  /**
   * Create ripple effect on buttons
   */
  createRippleEffect(button) {
    const ripple = document.createElement('span');
    ripple.style.cssText = `
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.3);
      transform: scale(0);
      animation: ripple 0.6s linear;
      pointer-events: none;
    `;
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${rect.width / 2 - size / 2}px`;
    ripple.style.top = `${rect.height / 2 - size / 2}px`;
    
    button.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
  }

  /**
   * Animate a number counter
   */
  animateCounter(element, target, duration = 1000) {
    if (this.isReducedMotion) {
      element.textContent = target;
      return;
    }

    const start = 0;
    const startTime = performance.now();
    
    const update = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const current = Math.floor(start + (target - start) * easeOutQuart);
      
      element.textContent = current;
      
      if (progress < 1) {
        requestAnimationFrame(update);
      } else {
        element.textContent = target;
      }
    };
    
    requestAnimationFrame(update);
  }

  /**
   * Create confetti celebration effect
   */
  createConfetti() {
    if (this.isReducedMotion) return;

    const colors = ['#6b21a8', '#ffd700', '#00ff85', '#00d4ff', '#ff3333'];
    const confettiCount = 50;
    
    for (let i = 0; i < confettiCount; i++) {
      const confetti = document.createElement('div');
      confetti.style.cssText = `
        position: fixed;
        width: ${Math.random() * 10 + 5}px;
        height: ${Math.random() * 10 + 5}px;
        background: ${colors[Math.floor(Math.random() * colors.length)]};
        left: ${Math.random() * 100}vw;
        top: -20px;
        border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
        animation: confettiFall ${Math.random() * 3 + 2}s linear forwards;
        z-index: 9999;
        pointer-events: none;
      `;
      
      document.body.appendChild(confetti);
      
      setTimeout(() => confetti.remove(), 5000);
    }
  }

  /**
   * Goal celebration animation
   */
  celebrateGoal() {
    if (this.isReducedMotion) return;

    this.createConfetti();
    
    // Flash effect
    const flash = document.createElement('div');
    flash.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.3);
      animation: flash 0.3s ease;
      z-index: 9998;
      pointer-events: none;
    `;
    
    document.body.appendChild(flash);
    setTimeout(() => flash.remove(), 300);
  }

  /**
   * Shaking animation for errors
   */
  shakeElement(element) {
    if (this.isReducedMotion) return;
    
    element.classList.add('animate-shake');
    element.addEventListener('animationend', () => {
      element.classList.remove('animate-shake');
    }, { once: true });
  }

  /**
   * Success animation
   */
  successAnimation(element) {
    if (this.isReducedMotion) return;
    
    element.classList.add('success-animation');
    element.addEventListener('animationend', () => {
      element.classList.remove('success-animation');
    }, { once: true });
  }

  /**
   * Clean up all animations and observers
   */
  cleanup() {
    this.observers.forEach(observer => observer.disconnect());
    this.observers.clear();
    
    this.timers.forEach(timer => clearTimeout(timer));
    this.timers.clear();
  }
}

// Global animation instance
const animations = new AnimationOrchestrator();

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => animations.init());
} else {
  animations.init();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AnimationOrchestrator;
}