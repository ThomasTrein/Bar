/* ===== KSA Bar Kiosk JS ===== */

// ---- Screensaver ----
let ssTimer = null;
const SS_KEY = 'screensaver_timeout';

function getTimeout() {
  return (parseInt(document.body.dataset.ssTimeout) || 120) * 1000;
}

function resetTimer() {
  clearTimeout(ssTimer);
  const ss = document.getElementById('screensaver');
  if (ss) ss.classList.add('hidden');
  ssTimer = setTimeout(showScreensaver, getTimeout());
}

function showScreensaver() {
  const ss = document.getElementById('screensaver');
  if (ss) ss.classList.remove('hidden');
}

function updateSsClock() {
  const el = document.getElementById('ss-clock');
  if (el) {
    const n = new Date();
    el.textContent = n.toLocaleTimeString('nl-BE', { hour: '2-digit', minute: '2-digit' });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  resetTimer();
  setInterval(updateSsClock, 1000);
  updateSsClock();
});

['touchstart', 'touchmove', 'click', 'keydown', 'mousemove'].forEach(ev => {
  document.addEventListener(ev, resetTimer, { passive: true });
});
