/* ===== Touchscreen Kalender Datepicker — KSA Bar ===== */
(function () {
  'use strict';

  var MAANDEN = ['Januari','Februari','Maart','April','Mei','Juni',
                 'Juli','Augustus','September','Oktober','November','December'];
  var DAGEN   = ['Ma','Di','Wo','Do','Vr','Za','Zo'];

  var popup     = null;
  var activeEl  = null;
  var curYear   = 0;
  var curMonth  = 0;  // 0-based

  // ── CSS ─────────────────────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('datepicker-css')) return;
    var s = document.createElement('style');
    s.id = 'datepicker-css';
    s.textContent =
      '#dp-popup{' +
        'position:fixed;z-index:20000;background:#1a1a22;border:1px solid #2b2b38;' +
        'border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,.8);' +
        'padding:12px;min-width:280px;touch-action:manipulation;' +
      '}' +
      '#dp-popup .dp-header{' +
        'display:flex;align-items:center;justify-content:space-between;' +
        'margin-bottom:10px;gap:4px;' +
      '}' +
      '#dp-popup .dp-nav{' +
        'background:#2a2a36;border:none;color:#e4e4ec;border-radius:8px;' +
        'width:40px;height:40px;font-size:18px;cursor:pointer;' +
        'display:flex;align-items:center;justify-content:center;' +
        'touch-action:manipulation;' +
      '}' +
      '#dp-popup .dp-nav:active{background:#3a3a4a;}' +
      '#dp-popup .dp-title{' +
        'flex:1;text-align:center;font-weight:600;color:#e4e4ec;font-size:15px;' +
      '}' +
      '#dp-popup .dp-grid{' +
        'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;' +
      '}' +
      '#dp-popup .dp-dayname{' +
        'text-align:center;font-size:11px;color:#888;padding:4px 0;' +
      '}' +
      '#dp-popup .dp-day{' +
        'text-align:center;padding:8px 0;border-radius:8px;' +
        'cursor:pointer;color:#e4e4ec;font-size:14px;' +
        'touch-action:manipulation;user-select:none;' +
      '}' +
      '#dp-popup .dp-day:active,' +
      '#dp-popup .dp-day.dp-selected{background:var(--accent,#4ade80);color:#000;font-weight:700;}' +
      '#dp-popup .dp-day.dp-today{outline:1px solid var(--accent,#4ade80);}' +
      '#dp-popup .dp-day.dp-other-month{color:#555;}' +
      '#dp-popup .dp-clear{' +
        'display:block;width:100%;margin-top:8px;padding:8px;' +
        'background:#2a2a36;border:none;color:#f06464;' +
        'border-radius:8px;cursor:pointer;font-size:13px;' +
        'touch-action:manipulation;' +
      '}';
    document.head.appendChild(s);
  }

  // ── Build/update popup ────────────────────────────────────────────────────
  function buildPopup() {
    injectStyles();
    popup = document.createElement('div');
    popup.id = 'dp-popup';
    // Prevent focus loss AND prevent outside-click handler from seeing clicks inside popup
    popup.addEventListener('pointerdown', function (e) { e.preventDefault(); e.stopPropagation(); });
    popup.addEventListener('mousedown',   function (e) { e.preventDefault(); });
    popup.addEventListener('touchstart',  function (e) { e.stopPropagation(); }, { passive: true });
    document.body.appendChild(popup);
  }

  function renderCalendar() {
    var selected = parseDate(activeEl ? activeEl.value : '');
    var today = new Date();
    var firstDay = new Date(curYear, curMonth, 1);
    // Week starts on Monday: (0=Sun → 6, 1=Mon → 0, ...)
    var startDow = (firstDay.getDay() + 6) % 7;
    var daysInMonth = new Date(curYear, curMonth + 1, 0).getDate();

    var html = '<div class="dp-header">' +
      '<button class="dp-nav" id="dp-prev">&#8249;</button>' +
      '<span class="dp-title">' + MAANDEN[curMonth] + ' ' + curYear + '</span>' +
      '<button class="dp-nav" id="dp-next">&#8250;</button>' +
    '</div><div class="dp-grid">';

    DAGEN.forEach(function (d) {
      html += '<div class="dp-dayname">' + d + '</div>';
    });

    // Blank cells before first day
    for (var i = 0; i < startDow; i++) {
      html += '<div class="dp-day dp-other-month"></div>';
    }

    for (var day = 1; day <= daysInMonth; day++) {
      var cls = 'dp-day';
      var isToday = (today.getFullYear() === curYear && today.getMonth() === curMonth && today.getDate() === day);
      var isSel   = selected && (selected.getFullYear() === curYear && selected.getMonth() === curMonth && selected.getDate() === day);
      if (isToday) cls += ' dp-today';
      if (isSel)   cls += ' dp-selected';
      html += '<div class="' + cls + '" data-day="' + day + '">' + day + '</div>';
    }

    html += '</div><button class="dp-clear" id="dp-clear">Wissen</button>';
    popup.innerHTML = html;

    popup.querySelector('#dp-prev').addEventListener('pointerdown', function (e) {
      e.preventDefault();
      curMonth--;
      if (curMonth < 0) { curMonth = 11; curYear--; }
      renderCalendar();
    });
    popup.querySelector('#dp-next').addEventListener('pointerdown', function (e) {
      e.preventDefault();
      curMonth++;
      if (curMonth > 11) { curMonth = 0; curYear++; }
      renderCalendar();
    });
    popup.querySelector('#dp-clear').addEventListener('pointerdown', function (e) {
      e.preventDefault();
      if (activeEl) { activeEl.value = ''; activeEl.dispatchEvent(new Event('change', { bubbles: true })); }
      hide();
    });
    popup.querySelectorAll('.dp-day[data-day]').forEach(function (el) {
      el.addEventListener('pointerdown', function (e) {
        e.preventDefault();
        var d = parseInt(el.dataset.day);
        var dateStr = pad(curYear, 4) + '-' + pad(curMonth + 1, 2) + '-' + pad(d, 2);
        if (activeEl) { activeEl.value = dateStr; activeEl.dispatchEvent(new Event('change', { bubbles: true })); }
        hide();
      });
    });
  }

  // ── Positioning ───────────────────────────────────────────────────────────
  function position() {
    if (!popup || !activeEl) return;
    var rect = activeEl.getBoundingClientRect();
    var pw = popup.offsetWidth  || 290;
    var ph = popup.offsetHeight || 300;
    var left = Math.min(rect.left, window.innerWidth - pw - 8);
    var top  = rect.bottom + 4;
    if (top + ph > window.innerHeight - 8) top = rect.top - ph - 4;
    if (left < 4) left = 4;
    popup.style.left = left + 'px';
    popup.style.top  = top  + 'px';
  }

  // ── Show / Hide ───────────────────────────────────────────────────────────
  function show(input) {
    if (!popup) buildPopup();
    activeEl = input;
    var d = parseDate(input.value) || new Date();
    curYear  = d.getFullYear();
    curMonth = d.getMonth();
    renderCalendar();
    popup.style.display = 'block';
    // Position after render so offsetHeight is known
    setTimeout(position, 0);
  }

  function hide() {
    if (popup) popup.style.display = 'none';
    activeEl = null;
  }

  // ── Helpers ───────────────────────────────────────────────────────────────
  function parseDate(str) {
    if (!str) return null;
    var m = str.match(/^(\d{4})-(\d{2})-(\d{2})$/);
    if (!m) return null;
    return new Date(+m[1], +m[2] - 1, +m[3]);
  }

  function pad(n, w) {
    var s = String(n);
    while (s.length < w) s = '0' + s;
    return s;
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  function initDateInputs() {
    // Pre-set inputmode="none" on all date inputs so native picker never shows
    document.querySelectorAll('input[type="date"]').forEach(function (el) {
      el.setAttribute('inputmode', 'none');
      el.setAttribute('autocomplete', 'off');
    });
  }

  document.addEventListener('focusin', function (e) {
    var el = e.target;
    if (!el || el.tagName !== 'INPUT' || el.type !== 'date') return;
    el.setAttribute('inputmode', 'none');  // ensure it's set even for dynamically added inputs
    show(el);
  });

  // Close on outside tap — note: clicks inside popup are stopped at popup level (stopPropagation)
  document.addEventListener('pointerdown', function (e) {
    if (!popup || popup.style.display === 'none') return;
    if (activeEl && e.target === activeEl) return;
    hide();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDateInputs);
  } else {
    initDateInputs();
  }

  window.datePicker = { show: show, hide: hide };
}());
