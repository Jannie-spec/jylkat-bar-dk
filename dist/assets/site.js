// Jylkat – lille script: kort ved klik, formularer uden sideskift, datoer på julefrokost-siderne.
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

  // Julefrokost: skjul datoer der er overstået, og lad datoknapperne udfylde "Ønsket dato".
  var today = new Date().toISOString().slice(0, 10);
  document.querySelectorAll('[data-iso]').forEach(function (el) {
    if (el.dataset.iso < today) el.remove();
  });
  document.querySelectorAll('[data-date]').forEach(function (a) {
    a.addEventListener('click', function () {
      var sel = document.querySelector('select[name="preferred_date"]');
      if (sel) sel.value = a.dataset.date;
    });
  });

  // Bordbestilling: ikke datoer i fortiden.
  var d = document.querySelector('input[type="date"][name="date"]');
  if (d) d.min = today;

  // Formularerne sendes af send.php som mail til Zendesk (samme sted og samme opbygning som før).
  document.querySelectorAll('form[data-ajax]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var ok = f.querySelector('[data-ok]'), err = f.querySelector('[data-err]'), btn = f.querySelector('button[type="submit"]');
      ok.hidden = true; err.hidden = true;
      if (!/jylkat-bar\.dk$/.test(location.hostname)) {
        err.textContent = 'Testversion: formularen sender ikke.'; err.hidden = false; return;
      }
      if (f.querySelector('[name="_hp_company"]').value) { ok.hidden = false; return; } // robot
      if (!f.reportValidity()) return;
      btn.disabled = true;
      fetch('/send.php', { method: 'POST', body: new FormData(f), headers: { 'X-Requested-With': 'fetch' }, cache: 'no-store' })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (j && j.ok) {
            f.querySelectorAll('input:not([type=hidden]),textarea,select').forEach(function (x) { if (x.type === 'radio') x.checked = false; else x.value = ''; });
            ok.hidden = false; ok.scrollIntoView({ block: 'center', behavior: 'smooth' });
          } else { err.hidden = false; }
        })
        .catch(function () { err.hidden = false; })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
