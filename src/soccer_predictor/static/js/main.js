/* SOCCER PREDICTOR PRO - Main JavaScript */

(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        initSidebar();
        initTooltips();
        initAutoRefresh();
        initToastSystem();
    });

    function initSidebar() {
        const toggleBtn = document.getElementById('sidebarCollapse');
        const sidebar = document.getElementById('sidebar');
        const content = document.getElementById('content');

        if (!toggleBtn || !sidebar) return;

        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            if (content) content.classList.toggle('expanded');
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });

        if (localStorage.getItem('sidebarCollapsed') === 'true') {
            sidebar.classList.add('collapsed');
            if (content) content.classList.add('expanded');
        }
    }

    function initTooltips() {
        const tooltipTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="tooltip"]')
        );
        tooltipTriggerList.forEach(function(el) {
            new bootstrap.Tooltip(el);
        });
    }

    function initAutoRefresh() {
        const refreshElements = document.querySelectorAll('[data-auto-refresh]');
        if (!refreshElements.length) return;

        setInterval(function() {
            refreshElements.forEach(function(el) {
                el.classList.add('live-indicator');
                setTimeout(function() {
                    el.classList.remove('live-indicator');
                }, 2500);
            });
        }, 60000);
    }

    function initToastSystem() {
        window.showToast = function(message, type, duration) {
            type = type || 'info';
            duration = duration || 4000;

            var container = document.getElementById('toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'toast-container';
                container.className = 'toast-container';
                document.body.appendChild(container);
            }

            var bgClass = type === 'success' ? 'bg-success' : (type === 'error' ? 'bg-danger' : 'bg-info');
            var toastEl = document.createElement('div');
            toastEl.className = 'toast align-items-center text-white ' + bgClass;
            toastEl.setAttribute('role', 'alert');
            toastEl.innerHTML = '<div class="d-flex"><div class="toast-body">' + message + '</div>' +
                '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div>';

            container.appendChild(toastEl);
            var toast = new bootstrap.Toast(toastEl, { delay: duration });
            toast.show();

            toastEl.addEventListener('hidden.bs.toast', function() {
                toastEl.remove();
            });
        };
    }

    window.formatProb = function(prob) {
        if (typeof prob !== 'number') return '0.0%';
        return (prob * 100).toFixed(1) + '%';
    };

    window.formatOdds = function(odds) {
        if (typeof odds !== 'number') return '-';
        return odds.toFixed(2);
    };

    window.debounce = function(func, wait) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                func.apply(context, args);
            }, wait);
        };
    };

    window.throttle = function(func, limit) {
        var inThrottle;
        return function() {
            var args = arguments;
            var context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(function() { inThrottle = false; }, limit);
            }
        };
    };

    window.fetchJSON = async function(url, options) {
        options = options || {};
        options.headers = Object.assign({
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }, options.headers || {});

        try {
            var response = await fetch(url, options);
            if (!response.ok) {
                var errorData = await response.json().catch(function() { return {}; });
                throw new Error(errorData.error || 'HTTP ' + response.status + ': ' + response.statusText);
            }
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            if (window.showToast) window.showToast(error.message, 'error');
            throw error;
        }
    };

    window.showLoading = function(element, message) {
        message = message || 'Loading...';
        var overlay = document.createElement('div');
        overlay.className = 'loading-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        overlay.style.background = 'rgba(26, 29, 41, 0.85)';
        overlay.style.zIndex = '100';
        overlay.style.borderRadius = 'inherit';
        overlay.innerHTML = '<div class="text-center"><div class="spinner-border text-success mb-2" role="status"></div>' +
            '<div class="text-muted small">' + message + '</div></div>';

        var parent = element.parentElement || element;
        parent.style.position = 'relative';
        parent.appendChild(overlay);

        return function hideLoading() { overlay.remove(); };
    };

    window.animateNumber = function(element, target, duration, suffix) {
        suffix = suffix || '';
        duration = duration || 1000;
        var start = parseFloat(element.textContent) || 0;
        var range = target - start;
        var startTime = performance.now();

        function update(currentTime) {
            var elapsed = currentTime - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var easeProgress = 1 - Math.pow(1 - progress, 3);
            var current = start + range * easeProgress;
            element.textContent = (Number.isInteger(target) ? Math.round(current) : current.toFixed(1)) + suffix;
            if (progress < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    };

    window.smoothScrollTo = function(target, offset) {
        offset = offset || 80;
        var element = typeof target === 'string' ? document.querySelector(target) : target;
        if (!element) return;
        var top = element.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top: top, behavior: 'smooth' });
    };

    var observerOptions = { root: null, rootMargin: '0px', threshold: 0.1 };
    var fadeObserver = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in-up');
                fadeObserver.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('[data-animate]').forEach(function(el) {
        fadeObserver.observe(el);
    });

})();
