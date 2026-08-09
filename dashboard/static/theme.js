(() => {
  const key = 'matchday-iq-theme';
  const initial = localStorage.getItem(key) || (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark');
  const apply = (theme) => {
    document.documentElement.dataset.theme = theme;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'light' ? '#edf1f7' : '#090b14');
    localStorage.setItem(key, theme);
  };
  apply(initial);
  document.addEventListener('DOMContentLoaded', () => document.querySelector('.theme-toggle')?.addEventListener('click', () => apply(document.documentElement.dataset.theme === 'light' ? 'dark' : 'light')));
})();
