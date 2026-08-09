document.addEventListener('DOMContentLoaded', () => { document.querySelectorAll('a.btn').forEach((link) => link.addEventListener('click', () => link.textContent = 'Preparing download…')); });
