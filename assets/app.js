// Filtro por tema. La página funciona sin JavaScript; esto solo añade el filtrado.
(function () {
  var buttons = document.querySelectorAll('.filters button');
  var stories = document.querySelectorAll('.story');
  var empty = document.getElementById('empty');
  if (!buttons.length) return;

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      var tag = btn.getAttribute('data-filter');
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      var shown = 0;
      stories.forEach(function (s) {
        var match = tag === 'todo' || s.getAttribute('data-tag') === tag;
        s.hidden = !match;
        if (match) shown++;
      });
      if (empty) empty.hidden = shown !== 0;
    });
  });
})();

// Pestañas desplegables de la cabecera
(function () {
  var tabs = document.querySelectorAll('.tab > button');
  function closeAll(except) {
    tabs.forEach(function (b) {
      if (b === except) return;
      b.setAttribute('aria-expanded', 'false');
      document.getElementById(b.getAttribute('aria-controls')).hidden = true;
    });
  }
  tabs.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.stopPropagation();
      var open = btn.getAttribute('aria-expanded') === 'true';
      closeAll(btn);
      btn.setAttribute('aria-expanded', String(!open));
      document.getElementById(btn.getAttribute('aria-controls')).hidden = open;
    });
  });
  document.addEventListener('click', function (e) { if (!e.target.closest('.panel')) closeAll(); else if (e.target.closest('.panel a')) closeAll(); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeAll(); });
})();
