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
