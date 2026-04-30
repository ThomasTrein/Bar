document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.personen-grid').forEach(function (grid) {
    const kaarten = grid.querySelectorAll('.persoon-kaart');
    if (!kaarten.length) return;

    // Injecteer zoekbalk boven het grid (als die er nog niet is)
    if (!grid.previousElementSibling || !grid.previousElementSibling.classList.contains('letter-nav')) {
      const zoekWrap = document.createElement('div');
      zoekWrap.className = 'search-bar-wrap';
      const zoekInput = document.createElement('input');
      zoekInput.type = 'text';
      zoekInput.className = 'search-input';
      zoekInput.placeholder = '🔍 Zoek naam...';
      zoekInput.autocomplete = 'off';
      zoekInput.oninput = function () { filterGrid(this.value, kaarten); };
      zoekWrap.appendChild(zoekInput);
      grid.parentNode.insertBefore(zoekWrap, grid);

      // Bouw letter-navigatie
      const letters = new Set();
      kaarten.forEach(k => {
        const z = k.dataset.zoek || '';
        if (z[0]) letters.add(z[0].toUpperCase());
      });
      const nav = document.createElement('div');
      nav.className = 'letter-nav';
      [...letters].sort().forEach(l => {
        const btn = document.createElement('button');
        btn.className = 'letter-btn';
        btn.textContent = l;
        btn.onclick = () => {
          const target = [...kaarten].find(k => (k.dataset.zoek || '')[0]?.toUpperCase() === l);
          if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
        nav.appendChild(btn);
      });
      grid.parentNode.insertBefore(nav, grid);
    }
  });

  // Globale filterfunctie (voor achterwaartse compatibiliteit met oninput="filterPersonen(...)")
  window.filterPersonen = function (q) {
    const grid = document.querySelector('.personen-grid');
    if (grid) filterGrid(q, grid.querySelectorAll('.persoon-kaart'));
  };

  function filterGrid(q, kaarten) {
    const lq = q.toLowerCase().trim();
    kaarten.forEach(k => {
      const zoek = k.dataset.zoek || '';
      const visible = !lq || zoek.includes(lq);
      const wrapper = k.closest('form') || k;
      wrapper.style.display = visible ? '' : 'none';
    });
  }
});
