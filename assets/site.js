// Click a figure to enlarge it; Esc or click closes; arrow keys move between figures of the page.
(function () {
  var box = document.getElementById('lightbox');
  if (!box) return;
  var img = box.querySelector('img'), cap = box.querySelector('p');
  var links = Array.prototype.slice.call(document.querySelectorAll('a.zoom'));
  var cur = -1;
  function show(i) {
    if (i < 0 || i >= links.length) return;
    cur = i;
    img.src = links[i].getAttribute('href');
    var h = links[i].closest('figure').querySelector('h3 a');
    cap.textContent = h ? h.textContent : '';
    box.hidden = false;
  }
  function hide() { box.hidden = true; img.removeAttribute('src'); cur = -1; }
  links.forEach(function (a, i) {
    a.addEventListener('click', function (e) { e.preventDefault(); show(i); });
  });
  box.addEventListener('click', hide);
  document.addEventListener('keydown', function (e) {
    if (box.hidden) return;
    if (e.key === 'Escape') hide();
    if (e.key === 'ArrowRight') show(cur + 1);
    if (e.key === 'ArrowLeft') show(cur - 1);
  });
})();
