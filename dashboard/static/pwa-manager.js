/**
 * PWA Manager
 * Progressive Web App functionality for offline support and mobile experience
 */

class PWAManager {
  constructor() {
    this.swRegistration = null;
    this.isOffline = false;
    this.deferredPrompt = null;

    this.init();
  }

  init() {
    this.registerServiceWorker();
    this.setupInstallPrompt();
    this.setupOnlineStatus();
    this.setupCacheStrategy();
  }

  async registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      try {
        this.swRegistration = await navigator.serviceWorker.register('/sw.js');
        console.log('Service Worker registered:', this.swRegistration.scope);
        
        // Check for updates
        this.swRegistration.addEventListener('updatefound', () => {
          const newWorker = this.swRegistration.installing;
          newWorker.addEventListener('statechange', () => {
            if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
              this.showUpdateNotification();
            }
          });
        });
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  }

  setupInstallPrompt() {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      this.deferredPrompt = e;
      this.showInstallButton();
    });

    window.addEventListener('appinstalled', () => {
      this.deferredPrompt = null;
      this.hideInstallButton();
      this.showInstallSuccess();
    });
  }

  setupOnlineStatus() {
    window.addEventListener('online', () => {
      this.isOffline = false;
      this.hideOfflineNotification();
      this.syncOfflineData();
    });

    window.addEventListener('offline', () => {
      this.isOffline = true;
      this.showOfflineNotification();
    });

    // Initial check
    this.isOffline = !navigator.onLine;
    if (this.isOffline) {
      this.showOfflineNotification();
    }
  }

  setupCacheStrategy() {
    // Cache current page for offline access
    if ('caches' in window) {
      this.cacheCurrentPage();
    }
  }

  async cacheCurrentPage() {
    try {
      const cache = await caches.open('epl-predictor-v1');
      await cache.add(window.location.href);
    } catch (error) {
      console.error('Failed to cache current page:', error);
    }
  }

  showInstallButton() {
    let installBtn = document.getElementById('pwa-install-btn');
    
    if (!installBtn) {
      installBtn = document.createElement('button');
      installBtn.id = 'pwa-install-btn';
      installBtn.className = 'btn btn-gold';
      installBtn.innerHTML = '📲 Install App';
      installBtn.style.cssText = `
        position: fixed;
        bottom: 80px;
        right: 20px;
        z-index: 1000;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      `;
      
      installBtn.addEventListener('click', () => this.promptInstall());
      document.body.appendChild(installBtn);
    }
    
    installBtn.style.display = 'block';
  }

  hideInstallButton() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
      installBtn.style.display = 'none';
    }
  }

  async promptInstall() {
    if (!this.deferredPrompt) return;

    this.deferredPrompt.prompt();
    const { outcome } = await this.deferredPrompt.userChoice;
    
    if (outcome === 'accepted') {
      console.log('User accepted install prompt');
    }
    
    this.deferredPrompt = null;
    this.hideInstallButton();
  }

  showInstallSuccess() {
    this.showNotification('🎉 App Installed!', 'You can now access EPL Predictor from your home screen.');
  }

  showOfflineNotification() {
    let notification = document.getElementById('offline-notification');
    
    if (!notification) {
      notification = document.createElement('div');
      notification.id = 'offline-notification';
      notification.className = 'offline-notification';
      notification.innerHTML = `
        <div class="offline-icon">📡</div>
        <div class="offline-message">You're offline. Some features may be limited.</div>
      `;
      notification.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        background: var(--pl-red);
        color: white;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        z-index: 2000;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
      `;
      
      document.body.appendChild(notification);
    }
    
    notification.style.display = 'flex';
  }

  hideOfflineNotification() {
    const notification = document.getElementById('offline-notification');
    if (notification) {
      notification.style.display = 'none';
    }
  }

  showUpdateNotification() {
    const updateBtn = document.createElement('button');
    updateBtn.className = 'update-notification-btn';
    updateBtn.innerHTML = '🔄 Update Available';
    updateBtn.style.cssText = `
      position: fixed;
      bottom: 20px;
      right: 20px;
      padding: 12px 20px;
      background: var(--pl-purple);
      color: white;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      animation: bounceIn 0.5s ease;
    `;
    
    updateBtn.addEventListener('click', () => {
      if (this.swRegistration && this.swRegistration.waiting) {
        this.swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
        window.location.reload();
      }
      updateBtn.remove();
    });
    
    document.body.appendChild(updateBtn);
  }

  showNotification(title, message) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: '/static/epl_logo.png',
        badge: '/static/epl_logo.png'
      });
    } else {
      // Fallback to in-app notification
      this.showInAppNotification(title, message);
    }
  }

  showInAppNotification(title, message) {
    const notification = document.createElement('div');
    notification.className = 'pwa-notification';
    notification.innerHTML = `
      <div class="notification-title">${title}</div>
      <div class="notification-message">${message}</div>
    `;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--surface-alt);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      max-width: 300px;
      z-index: 1000;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      animation: slideInRight 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 5000);
  }

  async syncOfflineData() {
    // Sync any offline predictions or data when back online
    try {
      const offlineData = localStorage.getItem('offline-predictions');
      if (offlineData) {
        const predictions = JSON.parse(offlineData);
        
        for (const prediction of predictions) {
          await this.syncPrediction(prediction);
        }
        
        localStorage.removeItem('offline-predictions');
        this.showNotification('Sync Complete', 'Your offline data has been synced.');
      }
    } catch (error) {
      console.error('Failed to sync offline data:', error);
    }
  }

  async syncPrediction(prediction) {
    // Sync prediction with server
    try {
      await fetch('/api/v1/sync-prediction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prediction)
      });
    } catch (error) {
      console.error('Failed to sync prediction:', error);
    }
  }

  saveOfflinePrediction(prediction) {
    const offlineData = localStorage.getItem('offline-predictions') || '[]';
    const predictions = JSON.parse(offlineData);
    predictions.push({
      ...prediction,
      timestamp: Date.now(),
      synced: false
    });
    localStorage.setItem('offline-predictions', JSON.stringify(predictions));
  }

  async requestNotificationPermission() {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }

  scheduleMatchdayReminder(matchInfo) {
    if ('Notification' in window && Notification.permission === 'granted') {
      const matchTime = new Date(matchInfo.kickoff);
      const reminderTime = new Date(matchTime.getTime() - 60 * 60 * 1000); // 1 hour before
      
      const delay = reminderTime.getTime() - Date.now();
      
      if (delay > 0) {
        setTimeout(() => {
          this.showNotification(
            'Matchday Reminder',
            `${matchInfo.home} vs ${matchInfo.away} kicks off in 1 hour!`
          );
        }, delay);
      }
    }
  }

  addToHomeScreen() {
    // Trigger the install prompt if available
    if (this.deferredPrompt) {
      this.promptInstall();
    } else {
      this.showNotification(
        'Install Instructions',
        'Use your browser\'s "Add to Home Screen" option to install the app.'
      );
    }
  }

  isInstalled() {
    return window.matchMedia('(display-mode: standalone)').matches ||
           window.navigator.standalone === true;
  }

  getInstallState() {
    if (this.isInstalled()) {
      return 'installed';
    } else if (this.deferredPrompt) {
      return 'installable';
    } else {
      return 'not-installable';
    }
  }

  // Cache management
  async clearCache() {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      for (const cacheName of cacheNames) {
        await caches.delete(cacheName);
      }
      this.showNotification('Cache Cleared', 'All cached data has been removed.');
    }
  }

  async getCacheSize() {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      let totalSize = 0;
      
      for (const cacheName of cacheNames) {
        const cache = await caches.open(cacheName);
        const keys = await cache.keys();
        
        for (const request of keys) {
          const response = await cache.match(request);
          if (response) {
            const blob = await response.blob();
            totalSize += blob.size;
          }
        }
      }
      
      return totalSize;
    }
    return 0;
  }

  // Background sync for service worker
  async registerBackgroundSync() {
    if ('serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype) {
      try {
        await this.swRegistration.sync.register('sync-predictions');
      } catch (error) {
        console.error('Background sync registration failed:', error);
      }
    }
  }
}

// Initialize PWA manager
const pwaManager = new PWAManager();

// Request notification permission on user interaction
document.addEventListener('click', async () => {
  await pwaManager.requestNotificationPermission();
}, { once: true });

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PWAManager;
}