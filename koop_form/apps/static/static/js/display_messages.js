function armAlerts(root=document) {
// Fade-in: start with .fade only, then add .show on next frame
root.querySelectorAll('#messages .alert.fade:not([data-armed])').forEach(el => {
  el.setAttribute('data-armed','1');
  requestAnimationFrame(() => el.classList.add('show'));
  // Auto-hide → fade-out then remove
  setTimeout(() => {
    el.classList.remove('show');
    el.addEventListener('transitionend', () => el.remove(), { once: true });
  }, 10000);
});
}

// Make fade duration 0.5s (scoped to messages only)
const style = document.createElement('style');
style.textContent = `#messages .fade { transition-duration:.5s !important; }`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => armAlerts(document));
// Re-arm after HTMX OOB swap
document.body.addEventListener('htmx:oobAfterSwap', (e) => {
if (e.target.id === 'messages') armAlerts(e.target);
});
