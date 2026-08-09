document.addEventListener('DOMContentLoaded', () => { const picker = document.querySelector('#fixture-picker'); picker?.addEventListener('click', () => navigator.vibrate?.(8)); });
