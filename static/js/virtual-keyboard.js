/* ===== Virtual On-Screen Keyboard — KSA Bar ===== */
(function () {
  'use strict';

  // ── Layouts ──────────────────────────────────────────────────────────────
  var ALPHA = [
    ['a','z','e','r','t','y','u','i','o','p'],
    ['q','s','d','f','g','h','j','k','l','m'],
    ['SHIFT','w','x','c','v','b','n',',',':','BACK'],
    ['123','ACC','SPACE','OK']
  ];

  var NUM = [
    ['1','2','3','4','5','6','7','8','9','0'],
    ['-','/',':',';','(',')','€','&','@','"'],
    ['#','~','!','?','_','\'','.',',','BACK'],
    ['ABC','ACC','SPACE','OK']
  ];

  var ACC = [
    ['é','è','ê','ë','à','á','â','ä','ã','å'],
    ['ù','ú','û','ü','ò','ó','ô','ö','î','ï'],
    ['ç','ñ','ý','ì','í','ð','ß','BACK'],
    ['ABC','SPACE','OK']
  ];

  // ── State ─────────────────────────────────────────────────────────────────
  var activeInput   = null;
  var shiftOnce     = false;
  var capsLock      = false;
  var mode          = 'alpha';
  var backInterval  = null;
  var kbd           = null;

  // ── CSS injection ─────────────────────────────────────────────────────────
  function injectStyles() {
    if (document.getElementById('vkbd-css')) return;
    var s = document.createElement('style');
    s.id = 'vkbd-css';
    s.textContent =
      '#vkbd{' +
        'position:fixed;bottom:0;left:0;right:0;z-index:8000;' +
        'background:#141418;border-top:2px solid #333;' +
        'padding:8px 6px 14px;user-select:none;' +
        'transform:translateY(102%);transition:transform .22s ease;' +
        'box-shadow:0 -6px 28px rgba(0,0,0,.8);' +
      '}' +
      '#vkbd.vkbd-on{transform:translateY(0);}' +
      '.vkbd-row{display:flex;gap:5px;margin-bottom:5px;justify-content:center;}' +
      '.vkbd-key{' +
        'flex:1;max-width:54px;min-height:52px;' +
        'background:#2a2a2a;color:#e8e8f0;' +
        'border:1px solid #3a3a4a;border-radius:9px;' +
        'font-size:17px;font-family:inherit;cursor:pointer;' +
        'display:flex;align-items:center;justify-content:center;' +
        'touch-action:manipulation;-webkit-tap-highlight-color:transparent;' +
        'transition:background .1s;' +
      '}' +
      '.vkbd-key:active,.vkbd-key.pressed{background:#444;transform:scale(.93);}' +
      '.vkbd-key.mod{flex:0 0 auto;}' +
      '.vkbd-shift{min-width:54px;max-width:54px;background:#23233a;font-size:20px;}' +
      '.vkbd-shift.on{background:#4f8ef7;color:#fff;}' +
      '.vkbd-back{min-width:54px;max-width:54px;background:#2e1a1a;color:#e05555;font-size:18px;}' +
      '.vkbd-mode{min-width:62px;max-width:62px;font-size:13px;background:#1e1e28;color:#9090b0;}' +
      '.vkbd-space{flex:3;max-width:9999px;}' +
      '.vkbd-ok{min-width:64px;max-width:64px;background:#1a3a26;color:#4caf7a;font-size:20px;}';
    document.head.appendChild(s);
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  function buildKbd() {
    injectStyles();
    kbd = document.createElement('div');
    kbd.id = 'vkbd';
    kbd.setAttribute('aria-hidden', 'true');
    // Prevent inputs from blurring when user taps keyboard
    kbd.addEventListener('mousedown',  function(e){ e.preventDefault(); });
    kbd.addEventListener('touchstart', function(e){ e.preventDefault(); }, {passive: false});
    document.body.appendChild(kbd);
  }

  // ── Render ────────────────────────────────────────────────────────────────
  function render() {
    if (!kbd) buildKbd();
    kbd.innerHTML = '';
    var rows = mode === 'alpha' ? ALPHA : mode === 'num' ? NUM : ACC;

    rows.forEach(function(row) {
      var rowEl = document.createElement('div');
      rowEl.className = 'vkbd-row';

      row.forEach(function(key) {
        rowEl.appendChild(makeKey(key));
      });

      kbd.appendChild(rowEl);
    });
  }

  function makeKey(key) {
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'vkbd-key';

    switch (key) {
      case 'SHIFT':
        btn.className += ' mod vkbd-shift' + (shiftOnce || capsLock ? ' on' : '');
        btn.textContent = capsLock ? '⇪' : '⇧';
        on(btn, doShift);
        break;

      case 'BACK':
        btn.className += ' mod vkbd-back';
        btn.textContent = '⌫';
        btn.addEventListener('pointerdown', function(e) {
          e.preventDefault();
          e.stopPropagation();
          doBack();
          backInterval = setInterval(doBack, 90);
        });
        var stopFn = function() { clearInterval(backInterval); backInterval = null; };
        btn.addEventListener('pointerup',    stopFn);
        btn.addEventListener('pointerleave', stopFn);
        break;

      case '123':
        btn.className += ' mod vkbd-mode';
        btn.textContent = '123';
        on(btn, function(){ mode = 'num'; render(); });
        break;

      case 'ABC':
        btn.className += ' mod vkbd-mode';
        btn.textContent = 'ABC';
        on(btn, function(){ mode = 'alpha'; render(); });
        break;

      case 'ACC':
        btn.className += ' mod vkbd-mode';
        btn.textContent = 'àéü';
        on(btn, function(){ mode = 'acc'; render(); });
        break;

      case 'SPACE':
        btn.className += ' vkbd-space';
        btn.textContent = ' ';
        on(btn, function(){ type(' '); });
        break;

      case 'OK':
        btn.className += ' mod vkbd-ok';
        btn.textContent = '✓';
        on(btn, doOk);
        break;

      default:
        var ch = key;
        if (mode === 'alpha' && key.length === 1 && key >= 'a' && key <= 'z') {
          ch = (shiftOnce || capsLock) ? key.toUpperCase() : key;
        }
        btn.textContent = ch;
        (function(k){ on(btn, function(){ type(k); }); })(key);
        break;
    }

    return btn;
  }

  // ── Pointer helper ────────────────────────────────────────────────────────
  function on(btn, fn) {
    btn.addEventListener('pointerdown', function(e) {
      e.preventDefault();
      e.stopPropagation();
      fn();
    });
  }

  // ── Actions ───────────────────────────────────────────────────────────────
  function type(key) {
    if (!activeInput) return;
    var ch = key;
    if (mode === 'alpha' && key.length === 1 && key >= 'a' && key <= 'z') {
      ch = (shiftOnce || capsLock) ? key.toUpperCase() : key;
    }
    var start = activeInput.selectionStart;
    var end   = activeInput.selectionEnd;
    var val   = activeInput.value;
    activeInput.value = val.slice(0, start) + ch + val.slice(end);
    activeInput.setSelectionRange(start + ch.length, start + ch.length);
    activeInput.dispatchEvent(new Event('input',  {bubbles: true}));
    activeInput.dispatchEvent(new Event('change', {bubbles: true}));

    if (shiftOnce && !capsLock) {
      shiftOnce = false;
      render();
    }
  }

  function doBack() {
    if (!activeInput) return;
    var start = activeInput.selectionStart;
    var end   = activeInput.selectionEnd;
    var val   = activeInput.value;
    if (start !== end) {
      activeInput.value = val.slice(0, start) + val.slice(end);
      activeInput.setSelectionRange(start, start);
    } else if (start > 0) {
      activeInput.value = val.slice(0, start - 1) + val.slice(start);
      activeInput.setSelectionRange(start - 1, start - 1);
    }
    activeInput.dispatchEvent(new Event('input', {bubbles: true}));
  }

  function doShift() {
    if (!shiftOnce && !capsLock)      { shiftOnce = true;  }
    else if (shiftOnce && !capsLock)  { shiftOnce = false; capsLock = true;  }
    else                              { shiftOnce = false; capsLock = false; }
    render();
  }

  function doOk() {
    if (activeInput && activeInput.form) {
      var submit = activeInput.form.querySelector('[type="submit"]');
      if (submit) { submit.click(); return; }
      activeInput.form.submit();
    }
    hide();
  }

  // ── Show / hide ───────────────────────────────────────────────────────────
  function show(input) {
    activeInput = input;
    if (!kbd) buildKbd();
    render();
    requestAnimationFrame(function(){
      kbd.classList.add('vkbd-on');
    });
  }

  function hide() {
    if (kbd) kbd.classList.remove('vkbd-on');
    activeInput = null;
  }

  // ── Init ──────────────────────────────────────────────────────────────────
  function init() {
    document.addEventListener('focusin', function(e) {
      var el = e.target;
      if (!el || !el.matches) return;
      if (el.matches('input[type="text"], input[type="password"], input[type="search"]')) {
        if (el.dataset.noVkbd === '1') return;
        show(el);
      }
    });

    // Hide when tapping outside the keyboard and any text input
    document.addEventListener('pointerdown', function(e) {
      if (!kbd || !kbd.classList.contains('vkbd-on')) return;
      var t = e.target;
      if (kbd.contains(t)) return;
      if (t.matches && t.matches('input[type="text"], input[type="password"], input[type="search"]')) return;
      hide();
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
