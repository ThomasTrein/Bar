/* ===== Numeriek Touchscreen Toetsenbord — KSA Bar ===== */
(function () {
  'use strict';

  var activeInput = null;
  var kbd = null;
  var backInterval = null;

  // ── CSS ─────────────────────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('numkbd-css')) return;
    var s = document.createElement('style');
    s.id = 'numkbd-css';
    s.textContent =
      '#numkbd{' +
        'position:fixed;bottom:0;left:0;right:0;z-index:10000;' +
        'background:#13131a;border-top:1px solid #2b2b38;' +
        'padding:10px 8px 16px;user-select:none;' +
        'transform:translateY(102%);transition:transform .22s ease;' +
        'box-shadow:0 -8px 32px rgba(0,0,0,.85);' +
      '}' +
      '#numkbd.numkbd-on{transform:translateY(0);}' +
      '.numkbd-row{display:flex;gap:8px;margin-bottom:8px;justify-content:center;}' +
      '.numkbd-key{' +
        'flex:1;max-width:90px;min-height:60px;' +
        'background:#1a1a22;color:#e4e4ec;' +
        'border:1px solid #2b2b38;border-radius:10px;' +
        'font-size:22px;font-family:inherit;cursor:pointer;' +
        'display:flex;align-items:center;justify-content:center;' +
        'touch-action:manipulation;-webkit-tap-highlight-color:transparent;' +
        'transition:background .1s;' +
      '}' +
      '.numkbd-key:active,.numkbd-key.pressed{background:#2a2a36;transform:scale(.92);}' +
      '.numkbd-back{background:rgba(240,100,100,.1);color:#f06464;font-size:24px;}' +
      '.numkbd-ok{background:rgba(74,222,128,.12);color:#4ade80;font-size:20px;min-width:90px;}' +
      '.numkbd-zero{flex:2;max-width:190px;}';
    document.head.appendChild(s);
  }

  // ── Build ────────────────────────────────────────────────────────────────────
  function buildKbd() {
    injectStyles();
    kbd = document.createElement('div');
    kbd.id = 'numkbd';
    kbd.setAttribute('aria-hidden', 'true');
    kbd.addEventListener('mousedown', function (e) { e.preventDefault(); });
    kbd.addEventListener('touchstart', function (e) { e.preventDefault(); }, { passive: false });

    var rows = [
      ['7', '8', '9'],
      ['4', '5', '6'],
      ['1', '2', '3'],
      ['0', '.', 'BACK', 'OK']
    ];

    rows.forEach(function (row) {
      var rowEl = document.createElement('div');
      rowEl.className = 'numkbd-row';
      row.forEach(function (key) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'numkbd-key';

        if (key === 'BACK') {
          btn.className += ' numkbd-back';
          btn.textContent = '⌫';
          btn.addEventListener('pointerdown', function (e) {
            e.preventDefault();
            doBack();
            backInterval = setInterval(doBack, 90);
          });
          var stop = function () { clearInterval(backInterval); backInterval = null; };
          btn.addEventListener('pointerup', stop);
          btn.addEventListener('pointerleave', stop);
        } else if (key === 'OK') {
          btn.className += ' numkbd-ok';
          btn.textContent = '✓ OK';
          on(btn, hide);
        } else if (key === '0') {
          btn.className += ' numkbd-zero';
          btn.textContent = '0';
          on(btn, function () { type('0'); });
        } else if (key === '.') {
          btn.textContent = '.';
          on(btn, function () {
            if (activeInput && activeInput.value.indexOf('.') === -1) type('.');
          });
        } else {
          btn.textContent = key;
          on(btn, function (k) { return function () { type(k); }; }(key));
        }

        rowEl.appendChild(btn);
      });
      kbd.appendChild(rowEl);
    });

    document.body.appendChild(kbd);
  }

  // ── Scroll helpers ────────────────────────────────────────────────────────────
  var _paddedEl = null;
  var _paddedOrig = '';

  function getScrollParent(el) {
    el = el.parentElement;
    while (el && el !== document.body) {
      var oy = window.getComputedStyle(el).overflowY;
      if ((oy === 'auto' || oy === 'scroll') && el.scrollHeight > el.clientHeight) return el;
      el = el.parentElement;
    }
    return document.scrollingElement || document.documentElement;
  }

  function scrollAboveKbd(input) {
    var kbdH = kbd ? kbd.offsetHeight : 300;
    var margin = 24;
    var targetBottom = window.innerHeight - kbdH - margin;

    var scrollEl = getScrollParent(input);

    // Add bottom padding once so there is room to scroll
    if (_paddedEl !== scrollEl) {
      if (_paddedEl) _paddedEl.style.paddingBottom = _paddedOrig;
      _paddedEl = scrollEl;
      _paddedOrig = scrollEl.style.paddingBottom;
      var curPad = parseInt(window.getComputedStyle(scrollEl).paddingBottom) || 0;
      scrollEl.style.paddingBottom = (curPad + kbdH + margin) + 'px';
    }

    var rect = input.getBoundingClientRect();
    if (rect.bottom > targetBottom) {
      scrollEl.scrollTop += rect.bottom - targetBottom;
    }
  }

  function restorePadding() {
    if (_paddedEl) {
      _paddedEl.style.paddingBottom = _paddedOrig;
      _paddedEl = null;
      _paddedOrig = '';
    }
  }

  // ── Actions ──────────────────────────────────────────────────────────────────
  function type(char) {
    if (!activeInput) return;
    var v = activeInput.value;
    // type="number" does not support selectionStart — always append
    if (activeInput.selectionStart === null) {
      // Clear leading "0" when typing the first real digit
      activeInput.value = (v === '0' && char !== '.') ? char : v + char;
    } else {
      var start = activeInput.selectionStart;
      var end = activeInput.selectionEnd;
      activeInput.value = v.slice(0, start) + char + v.slice(end);
      try { activeInput.setSelectionRange(start + char.length, start + char.length); } catch (e) {}
    }
    activeInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function doBack() {
    if (!activeInput) return;
    var v = activeInput.value;
    // type="number" does not support selectionStart — delete from end
    if (activeInput.selectionStart === null) {
      activeInput.value = v.slice(0, -1);
    } else {
      var start = activeInput.selectionStart;
      var end = activeInput.selectionEnd;
      if (start !== end) {
        activeInput.value = v.slice(0, start) + v.slice(end);
        try { activeInput.setSelectionRange(start, start); } catch (e) {}
      } else if (start > 0) {
        activeInput.value = v.slice(0, start - 1) + v.slice(start);
        try { activeInput.setSelectionRange(start - 1, start - 1); } catch (e) {}
      }
    }
    activeInput.dispatchEvent(new Event('input', { bubbles: true }));
  }

  function on(btn, fn) {
    btn.addEventListener('pointerdown', function (e) {
      e.preventDefault();
      btn.classList.add('pressed');
      fn();
    });
    btn.addEventListener('pointerup', function () { btn.classList.remove('pressed'); });
    btn.addEventListener('pointerleave', function () { btn.classList.remove('pressed'); });
  }

  function show(input) {
    if (!kbd) buildKbd();
    activeInput = input;
    // Hide the decimal button for integer-only inputs
    var dotBtn = kbd.querySelector('.numkbd-key:not(.numkbd-back):not(.numkbd-ok):not(.numkbd-zero)');
    if (dotBtn && dotBtn.textContent === '.') {
      var isInt = (input.dataset.numericKbd === 'int' || input.step === '1' ||
                   (!input.step && input.getAttribute('type') === 'number' &&
                    !input.getAttribute('step')));
      dotBtn.style.display = isInt ? 'none' : '';
    }
    kbd.classList.add('numkbd-on');
    // After keyboard animation, scroll input into view above keyboard
    setTimeout(function () { scrollAboveKbd(input); }, 260);
  }

  function hide() {
    if (kbd) kbd.classList.remove('numkbd-on');
    restorePadding();
    activeInput = null;
  }

  // ── Init ─────────────────────────────────────────────────────────────────────

  function initInputs() {
    // Pre-mark all numeric-kbd inputs to prevent native keyboard
    document.querySelectorAll('[data-numeric-kbd]').forEach(function (el) {
      el.setAttribute('inputmode', 'none');
    });
  }

  document.addEventListener('focusin', function (e) {
    var el = e.target;
    if (!el || el.tagName !== 'INPUT') return;
    if (el.hasAttribute('data-numeric-kbd')) {
      el.setAttribute('inputmode', 'none');
      show(el);
    }
  });

  document.addEventListener('focusout', function (e) {
    var el = e.target;
    if (el && el.hasAttribute('data-numeric-kbd')) {
      setTimeout(function () {
        var focused = document.activeElement;
        if (!kbd || !kbd.contains(focused)) hide();
      }, 150);
    }
  });

  // Tap outside keyboard → hide
  document.addEventListener('pointerdown', function (e) {
    if (!kbd || !kbd.classList.contains('numkbd-on')) return;
    if (kbd.contains(e.target)) return;
    if (activeInput && activeInput.contains(e.target)) return;
    hide();
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initInputs);
  } else {
    initInputs();
  }

  // Expose for external use
  window.numKbd = { show: show, hide: hide };
}());
