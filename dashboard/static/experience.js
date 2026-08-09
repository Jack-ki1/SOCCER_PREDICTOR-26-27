// Lightweight interaction layer shared by the editorial home experience.
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.signal-card, .season-stat, .card').forEach((el) => {
    el.addEventListener('pointermove', (event) => {
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
      const rect = el.getBoundingClientRect();
      el.style.setProperty('--mx', `${event.clientX - rect.left}px`);
      el.style.setProperty('--my', `${event.clientY - rect.top}px`);
    });
  });
  const counters = document.querySelectorAll('[data-count]');
  const observer = new IntersectionObserver((entries) => entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const el = entry.target, end = Number(el.dataset.count || 0), start = performance.now();
    const animate = (now) => { const p = Math.min((now - start) / 700, 1); el.textContent = Math.round(end * p); if (p < 1) requestAnimationFrame(animate); };
    requestAnimationFrame(animate); observer.unobserve(el);
  }), { threshold: .5 });
  counters.forEach((counter) => observer.observe(counter));
});
