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

  // Formularerne sendes til one.com's formulartjeneste (den samme som den gamle side brugte),
  // så beskederne lander samme sted som før.
  var API = '/_wp_/wp-json/wsb20/v1/forms/';
  document.querySelectorAll('form[data-ajax]').forEach(function (f) {
    f.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var ok = f.querySelector('[data-ok]'), err = f.querySelector('[data-err]'), btn = f.querySelector('button[type="submit"]');
      ok.hidden = true; err.hidden = true;
      if (!/jylkat-bar\.dk$/.test(location.hostname) || location.pathname.indexOf('/ny-side/') === 0) {
        err.textContent = 'Testversion: formularen sender ikke.'; err.hidden = false; return;
      }
      if (f.querySelector('[name="_hp_company"]').value) { ok.hidden = false; return; } // robot
      if (!f.reportValidity()) return;
      btn.disabled = true;
      var url = API + f.dataset.key + '/submit';
      fetch(url, { cache: 'no-store' })
        .then(function (r) { return r.json(); })
        .then(function (cfg) {
          var allowed = {}; (cfg.accepted_fields || []).forEach(function (a) { allowed[a.name] = true; });
          var data = {};
          new FormData(f).forEach(function (v, k) { if (allowed[k]) data[k] = v; });
          Object.keys(cfg.required_hidden_fields || {}).forEach(function (k) { data[k] = cfg.required_hidden_fields[k]; });
          data._wsb20_company = '';
          return fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
        })
        .then(function (r) { return r.text(); })
        .then(function (t) {
          var j = {}; try { j = JSON.parse(t); } catch (e) {}
          if (j.success || j.code === 'submission_received') {
            f.querySelectorAll('input:not([type=hidden]),textarea,select').forEach(function (x) { if (x.type === 'radio') x.checked = false; else x.value = ''; });
            ok.hidden = false; ok.scrollIntoView({ block: 'center', behavior: 'smooth' });
          } else { err.hidden = false; }
        })
        .catch(function () { err.hidden = false; })
        .finally(function () { btn.disabled = false; });
    });
  });
})();
