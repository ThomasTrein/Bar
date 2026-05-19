/* ===== KSA Bar Kiosk JS ===== */

// ── Custom Confirm Modal ──────────────────────────────────────────────────────
(function () {
  'use strict';

  var _overlay = null;

  function injectModal() {
    if (document.getElementById('custom-confirm-overlay')) return;
    var style = document.createElement('style');
    style.textContent =
      '#custom-confirm-overlay{' +
        'position:fixed;inset:0;z-index:9500;' +
        'background:rgba(0,0,0,.72);' +
        'display:flex;align-items:center;justify-content:center;' +
      '}' +
      '#custom-confirm-box{' +
        'background:var(--surface,#1a1a22);' +
        'border:1px solid var(--border,#2b2b38);' +
        'border-radius:12px;padding:28px 32px;min-width:320px;max-width:480px;' +
        'box-shadow:0 8px 40px rgba(0,0,0,.8);' +
      '}' +
      '#custom-confirm-msg{' +
        'font-size:18px;color:var(--text,#e4e4ec);margin-bottom:28px;line-height:1.5;text-align:center;' +
      '}' +
      '#custom-confirm-btns{display:flex;gap:16px;justify-content:center;}' +
      '#custom-confirm-ok{' +
        'background:var(--danger,#e05555);color:#fff;border:none;border-radius:10px;' +
        'padding:14px 32px;font-size:17px;font-family:inherit;cursor:pointer;' +
        'min-width:130px;transition:background .15s;' +
      '}' +
      '#custom-confirm-ok:hover{background:#c94444;}' +
      '#custom-confirm-cancel{' +
        'background:var(--surface-alt,#242430);color:var(--text,#e4e4ec);' +
        'border:1px solid var(--border,#2b2b38);border-radius:10px;' +
        'padding:14px 32px;font-size:17px;font-family:inherit;cursor:pointer;' +
        'min-width:130px;transition:background .15s;' +
      '}' +
      '#custom-confirm-cancel:hover{background:#2e2e3c;}';
    document.head.appendChild(style);

    var overlay = document.createElement('div');
    overlay.id = 'custom-confirm-overlay';
    overlay.style.display = 'none';
    overlay.innerHTML =
      '<div id="custom-confirm-box">' +
        '<div id="custom-confirm-msg"></div>' +
        '<div id="custom-confirm-btns">' +
          '<button id="custom-confirm-cancel" type="button">Annuleren</button>' +
          '<button id="custom-confirm-ok" type="button">Bevestigen</button>' +
        '</div>' +
      '</div>';
    document.body.appendChild(overlay);
    _overlay = overlay;
  }

  window.customConfirm = function (message, onOk, onCancel) {
    injectModal();
    document.getElementById('custom-confirm-msg').textContent = message;
    _overlay.style.display = 'flex';

    var okBtn     = document.getElementById('custom-confirm-ok');
    var cancelBtn = document.getElementById('custom-confirm-cancel');

    function close() { _overlay.style.display = 'none'; }

    var newOk = okBtn.cloneNode(true);
    var newCancel = cancelBtn.cloneNode(true);
    okBtn.parentNode.replaceChild(newOk, okBtn);
    cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);

    newOk.addEventListener('click', function () { close(); if (onOk) onOk(); });
    newCancel.addEventListener('click', function () { close(); if (onCancel) onCancel(); });
  };

  // Intercept forms with data-confirm attribute
  document.addEventListener('submit', function (e) {
    var form = e.target;
    var msg = form.dataset.confirm;
    if (!msg) return;
    e.preventDefault();
    window.customConfirm(msg, function () { form.dataset.confirm = ''; form.submit(); });
  }, true);

  // Intercept standalone buttons with data-confirm
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-confirm]');
    if (!btn || btn.tagName === 'FORM') return;
    var form = btn.closest('form');
    if (form && form.dataset.confirm) return;
    var msg = btn.dataset.confirm;
    if (!msg) return;
    e.preventDefault();
    e.stopImmediatePropagation();
    window.customConfirm(msg, function () {
      btn.dataset.confirm = '';
      btn.click();
    });
  }, true);
}());

// ── Screensaver ───────────────────────────────────────────────────────────────
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
