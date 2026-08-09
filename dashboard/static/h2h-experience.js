document.addEventListener('DOMContentLoaded', () => { document.querySelectorAll('#team-a,#team-b').forEach((el) => el.addEventListener('change', () => window.compare?.())); });
