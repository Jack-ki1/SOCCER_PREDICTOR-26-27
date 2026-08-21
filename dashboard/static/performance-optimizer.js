/**
 * Performance Optimizer
 * Technical enhancements for performance, caching, and optimization
 */

class PerformanceOptimizer {
  constructor() {
    this.cache = new Map();
    this.observers = new Map();
    this.pendingRequests = new Map();
    
    this.init();
  }

  init() {
    this.setupLazyLoading();
    this.setupCodeSplitting();
    this.setupRequestDeduplication();
    this.setupMemoryManagement();
    this.setupPerformanceMonitoring();
  }

  setupLazyLoading() {
    // Lazy load images and components
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
            }
            observer.unobserve(img);
          }
        });
      });

      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }

    // Lazy load charts
    this.setupChartLazyLoading();
  }

  setupChartLazyLoading() {
    const chartContainers = document.querySelectorAll('.chart-container');
    
    const chartObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const container = entry.target;
          const chartId = container.dataset.chartId;
          
          if (chartId && !container.dataset.loaded) {
            this.loadChart(chartId, container);
            container.dataset.loaded = 'true';
          }
        }
      });
    }, { rootMargin: '50px' });

    chartContainers.forEach(container => {
      chartObserver.observe(container);
    });
  }

  loadChart(chartId, container) {
    // Dynamic chart loading logic
    console.log(`Loading chart: ${chartId}`);
  }

  setupCodeSplitting() {
    // Dynamic import of JavaScript modules
    this.dynamicImports = {
      'team-comparison': () => import('./team-comparison.js'),
      'simulation-visualizer': () => import('./simulation-visualizer.js'),
      'model-explainer': () => import('./model-explainer.js')
    };
  }

  async loadModule(moduleName) {
    if (this.dynamicImports[moduleName]) {
      try {
        const module = await this.dynamicImports[moduleName]();
        return module;
      } catch (error) {
        console.error(`Failed to load module ${moduleName}:`, error);
        return null;
      }
    }
    return null;
  }

  setupRequestDeduplication() {
    // Prevent duplicate API requests
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      const url = args[0];
      const options = args[1] || {};
      const cacheKey = this.getRequestCacheKey(url, options);
      
      // Check if there's a pending request
      if (this.pendingRequests.has(cacheKey)) {
        return this.pendingRequests.get(cacheKey);
      }
      
      // Create new request
      const request = originalFetch(...args);
      this.pendingRequests.set(cacheKey, request);
      
      try {
        const response = await request;
        
        // Cache GET requests
        if (options.method === 'GET' || !options.method) {
          this.cache.set(cacheKey, {
            response: response.clone(),
            timestamp: Date.now()
          });
        }
        
        return response;
      } finally {
        this.pendingRequests.delete(cacheKey);
      }
    };
  }

  getRequestCacheKey(url, options) {
    return `${url}-${JSON.stringify(options)}`;
  }

  setupMemoryManagement() {
    // Periodic cache cleanup
    setInterval(() => {
      this.cleanupCache();
    }, 60000); // Every minute

    // Monitor memory usage
    if (performance.memory) {
      setInterval(() => {
        const used = performance.memory.usedJSHeapSize / 1048576;
        const total = performance.memory.totalJSHeapSize / 1048576;
        
        if (used / total > 0.9) {
          this.cleanupCache();
          console.warn('High memory usage, cache cleaned');
        }
      }, 30000);
    }
  }

  cleanupCache() {
    const now = Date.now();
    const maxAge = 5 * 60 * 1000; // 5 minutes
    
    for (const [key, value] of this.cache.entries()) {
      if (now - value.timestamp > maxAge) {
        this.cache.delete(key);
      }
    }
  }

  setupPerformanceMonitoring() {
    // Monitor page load performance
    window.addEventListener('load', () => {
      this.reportPerformance();
    });

    // Monitor Core Web Vitals
    this.setupCoreWebVitals();
  }

  reportPerformance() {
    if ('performance' in window) {
      const timing = performance.timing;
      const pageLoadTime = timing.loadEventEnd - timing.navigationStart;
      const domReadyTime = timing.domContentLoadedEventEnd - timing.navigationStart;
      
      console.log(`Page load time: ${pageLoadTime}ms`);
      console.log(`DOM ready time: ${domReadyTime}ms`);
      
      // Send to analytics if available
      this.sendPerformanceMetrics({
        pageLoadTime,
        domReadyTime,
        timestamp: Date.now()
      });
    }
  }

  setupCoreWebVitals() {
    // Monitor Largest Contentful Paint (LCP)
    if ('PerformanceObserver' in window) {
      try {
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          console.log('LCP:', lastEntry.startTime);
        });
        
        lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
      } catch (e) {
        console.warn('LCP observer not supported');
      }

      // Monitor First Input Delay (FID)
      try {
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const fid = entries[0];
          console.log('FID:', fid.processingStart - fid.startTime);
        });
        
        fidObserver.observe({ type: 'first-input', buffered: true });
      } catch (e) {
        console.warn('FID observer not supported');
      }

      // Monitor Cumulative Layout Shift (CLS)
      try {
        const clsObserver = new PerformanceObserver((list) => {
          let clsValue = 0;
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          }
          console.log('CLS:', clsValue);
        });
        
        clsObserver.observe({ type: 'layout-shift', buffered: true });
      } catch (e) {
        console.warn('CLS observer not supported');
      }
    }
  }

  sendPerformanceMetrics(metrics) {
    // Send to analytics service
    console.log('Performance metrics:', metrics);
  }

  // Optimized DOM manipulation
  batchDOMUpdates(updates) {
    // Batch DOM updates to minimize reflows
    requestAnimationFrame(() => {
      updates.forEach(update => {
        update();
      });
    });
  }

  // Virtual scrolling for large lists
  setupVirtualScrolling(container, itemHeight, renderItem) {
    let scrollTop = 0;
    let viewportHeight = container.clientHeight;
    let totalItems = 0;
    
    const updateVisibleItems = () => {
      const startIndex = Math.floor(scrollTop / itemHeight);
      const endIndex = Math.min(
        startIndex + Math.ceil(viewportHeight / itemHeight) + 1,
        totalItems
      );
      
      const visibleItems = [];
      for (let i = startIndex; i < endIndex; i++) {
        visibleItems.push(renderItem(i));
      }
      
      container.innerHTML = visibleItems.join('');
    };
    
    container.addEventListener('scroll', () => {
      scrollTop = container.scrollTop;
      requestAnimationFrame(updateVisibleItems);
    });
    
    return {
      setItems: (count) => {
        totalItems = count;
        updateVisibleItems();
      },
      refresh: updateVisibleItems
    };
  }

  // Debounce function for performance
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // Throttle function for performance
  throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // Optimized event listeners
  setupDelegatedEvents(container, eventType, selector, handler) {
    container.addEventListener(eventType, (e) => {
      const target = e.target.closest(selector);
      if (target && container.contains(target)) {
        handler.call(target, e);
      }
    });
  }

  // Service Worker cache management
  async cacheAssets(assets) {
    if ('caches' in window) {
      try {
        const cache = await caches.open('epl-predictor-v1');
        await cache.addAll(assets);
        console.log('Assets cached successfully');
      } catch (error) {
        console.error('Failed to cache assets:', error);
      }
    }
  }

  async clearOldCaches() {
    if ('caches' in window) {
      const cacheNames = await caches.keys();
      const currentCache = 'epl-predictor-v1';
      
      for (const cacheName of cacheNames) {
        if (cacheName !== currentCache) {
          await caches.delete(cacheName);
          console.log(`Deleted old cache: ${cacheName}`);
        }
      }
    }
  }

  // Prefetch critical resources
  prefetchResources(urls) {
    urls.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    });
  }

  // Preload critical resources
  preloadResources(urls) {
    urls.forEach(url => {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = url;
      link.as = url.endsWith('.js') ? 'script' : 'style';
      document.head.appendChild(link);
    });
  }

  getPerformanceMetrics() {
    return {
      cacheSize: this.cache.size,
      pendingRequests: this.pendingRequests.size,
      memoryUsage: performance.memory ? {
        used: performance.memory.usedJSHeapSize,
        total: performance.memory.totalJSHeapSize,
        limit: performance.memory.jsHeapSizeLimit
      } : null
    };
  }
}

// Initialize performance optimizer
const performanceOptimizer = new PerformanceOptimizer();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PerformanceOptimizer;
}