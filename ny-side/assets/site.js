// Jylkat – lille script: kort ved klik, formularer uden sideskift, datoknapper på julefrokost-siderne.
(function () {
  // Kort hentes først fra Google, når man klikker (ingen cookies før).
  document.querySelectorAll('.map[data-map]').forEach(function (box) {
    var b = box.querySelector('button');
    if (!b) return;
    b.addEventListener('click', function () {
      box.innerHTML = '<iframe loading="lazy" title="' + box.dataset.title + '" src="' + box.dataset.map + '"></iframe>';
      box.style.padding = '0';
    });
  });

  // Datoknapper udfylder "Ønsket dato".
  document.querySelectorAll('[data-date]').forEach(function (a) {
    a.addEventListener('click', function () {
      var sel = document.querySelector('select[name="preferred_date"]');
      if (sel) sel.value = a.dataset.date;
    });
  });

  // Datofelt: ikke datoer i fortiden.
  var d = document.querySelector('input[type="date"][name="date"]');
  if (d) d.min = new Date().toISOString().slice(0, 10);

  // Formularer sendes med fetch; uden JavaScript virker de stadig som almindelig formular.
  document.querySelectorAll('form[data-ajax]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var ok = f.querySelector('[data-ok]'), err = f.querySelector('[data-err]'), btn = f.querySelector('button[type="submit"]');
      ok.hidden = true; err.hidden = true;
      if (!/jylkat-bar\.dk$/.test(location.hostname) || location.pathname.indexOf('/ny-side/') === 0) {
        err.textContent = 'Prøveversion: formularen sender ikke endnu.'; err.hidden = false; return;
      }
      btn.disabled = true;
      fetch(f.action, { method: 'POST', body: new FormData(f), headers: { 'Accept': 'application/json' } })
        .then(function (r) { return r.json().catch(function () { return { ok: r.ok }; }); })
        .then(function (j) {
          if (j && j.ok) { f.querySelectorAll('input:not([type=hidden]),textarea,select').forEach(function (x) { if (x.type === 'radio') x.checked = false; else x.value = ''; }); ok.hidden = false; ok.scrollIntoView({ block: 'center', behavior: 'smooth' }); }
          else { err.hidden = false; }
        })
        .catch(function () { err.hidden = false; })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
