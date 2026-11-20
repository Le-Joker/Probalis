/* Probalis · site vitrine : installation selon l'appareil, « annoncé vs réel », décodeur de cote, prix, visite. */
(function () {
  'use strict';
  var doc = document;
  var win = window;
  var root = doc.documentElement;
  var C = {};
  try { C = JSON.parse(doc.getElementById('pb-site').textContent); } catch (e) {}
  var lang = C.lang || 'fr';
  var $ = function (s, el) { return (el || doc).querySelector(s); };
  var $$ = function (s, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(s)); };
  var fmt = function (s, o) { return String(s || '').replace(/\{(\w+)\}/g, function (_, k) { return o[k]; }); };
  var still = !!(win.matchMedia && win.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var lite = root.classList.contains('lite');
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var pctTxt = function (p) { var v = Math.round(p * 100); return lang === 'fr' ? v + ' %' : v + '%'; };

  // ---------- En-tête : un trait discret dès qu'on descend ----------
  var hd = $('.hd');
  var onScroll = function () { if (hd) hd.classList.toggle('scrolled', (win.pageYOffset || 0) > 8); };
  win.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // ---------- Heures affichées dans le fuseau du visiteur ----------
  $$('time[data-dt]').forEach(function (el) {
    var d = new Date(el.getAttribute('datetime'));
    if (isNaN(d.getTime())) return;
    try {
      var loc = lang === 'fr' ? 'fr-FR' : 'en-GB';
      el.textContent = d.toLocaleDateString(loc, { weekday: 'short', day: 'numeric', month: 'short' }) + ', ' +
        d.toLocaleTimeString(loc, { hour: '2-digit', minute: '2-digit' });
    } catch (e) {}
  });

  // ---------- Bandeau « aussi en anglais / en français » ----------
  (function () {
    var b = $('#lang-banner');
    if (!b || store.get('pb-lb-off')) return;
    var pref = store.get('lang') || ((navigator.language || 'fr').toLowerCase().indexOf('fr') === 0 ? 'fr' : 'en');
    if (pref === lang) return;
    b.hidden = false;
    $('.lb-x', b).addEventListener('click', function () { b.hidden = true; store.set('pb-lb-off', '1'); });
  })();

  // ---------- Annoncé vs réel : l'annonce se pose, puis le réel la rejoint ----------
  (function () {
    var cal = $('#cal');
    if (!cal || still || lite || !('IntersectionObserver' in win)) return;
    var rows = $$('.cal-row', cal);
    var reals = [];
    rows.forEach(function (r, i) {
      r.style.setProperty('--d', String(i * 170));
      var b = $('.cal-real b', r);
      if (b) {
        reals.push({ el: b, txt: b.textContent, to: +b.getAttribute('data-to'), delay: i * 170 + 250 });
        b.textContent = b.textContent.replace(/\d+/, '0');
      }
    });
    cal.classList.add('arm');
    var ease = function (t) { return t >= 1 ? 1 : 1 - Math.pow(2, -10 * t); };
    var count = function (n) {
      var start = null;
      var step = function (now) {
        if (start === null) start = now;
        var t = (now - start - n.delay) / 1600;
        if (t < 0) { win.requestAnimationFrame(step); return; }
        n.el.textContent = n.txt.replace(/\d+/, String(Math.round(n.to * ease(Math.min(1, t)))));
        if (t < 1) win.requestAnimationFrame(step);
      };
      win.requestAnimationFrame(step);
    };
    var io = new IntersectionObserver(function (entries) {
      if (!entries.some(function (e) { return e.isIntersecting; })) return;
      io.disconnect();
      cal.classList.remove('arm');
      cal.classList.add('play');
      reals.forEach(count);
    }, { threshold: 0.35 });
    io.observe(cal);
    // À l'impression, tout s'affiche
    win.addEventListener('beforeprint', function () {
      cal.classList.remove('arm');
      reals.forEach(function (n) { n.el.textContent = n.txt; });
    });
  })();

  // ---------- Visite : le téléphone suit le chapitre lu (grand écran) ----------
  (function () {
    var chaps = $$('.chap');
    var imgs = $$('.tour-phone img');
    if (!chaps.length || !imgs.length || !('IntersectionObserver' in win)) return;
    var set = function (i) {
      imgs.forEach(function (im) { im.classList.toggle('on', im.getAttribute('data-i') === i); });
      chaps.forEach(function (c) { c.classList.toggle('on', c.getAttribute('data-i') === i); });
    };
    set('0');
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) set(e.target.getAttribute('data-i')); });
    }, { rootMargin: '-45% 0px -45% 0px' });
    chaps.forEach(function (c) { io.observe(c); });
  })();

  // ---------- Décodeur de cote ----------
  (function () {
    var form = $('#odds-form');
    var input = $('#odds-in');
    if (!form || !input) return;
    var big = $('#oo-big');
    var need = $('#oo-pct');
    var margin = $('#oo-margin');
    var err = $('#odds-err');
    var dots = $$('#oo-dots i');
    var btns = $$('.odds-ex button');
    var num = function (s) { return parseFloat(String(s).replace(',', '.')); };
    var update = function () {
      var raw = input.value.trim().replace(',', '.');
      var o = parseFloat(raw);
      var ok = /^\d{1,3}([.]\d{1,3})?$/.test(raw) && o >= 1.01 && o <= 100;
      var bad = !ok && raw !== '';
      input.setAttribute('aria-invalid', bad ? 'true' : 'false');
      err.hidden = !bad;
      btns.forEach(function (b) { b.setAttribute('aria-pressed', ok && Math.abs(num(b.getAttribute('data-o')) - o) < 1e-9 ? 'true' : 'false'); });
      if (!ok) return;
      var p = 1 / o;
      big.textContent = p >= 0.095 ? fmt(C.odds_times10, { n: Math.max(1, Math.min(9, Math.round(p * 10))) })
        : fmt(C.odds_times100, { n: Math.max(1, Math.round(p * 100)) });
      need.textContent = fmt(C.odds_need_pct, { p: Math.max(1, Math.round(p * 100)) });
      margin.textContent = fmt(C.odds_margin, { f: pctTxt(p / (1 + (C.margin || 0.05))) });
      dots.forEach(function (d, i) { d.style.setProperty('--f', Math.max(0, Math.min(1, p * 10 - i)).toFixed(2)); });
    };
    input.addEventListener('input', update);
    form.addEventListener('submit', function (e) { e.preventDefault(); input.blur(); });
    btns.forEach(function (b) {
      b.addEventListener('click', function () { input.value = b.getAttribute('data-o'); update(); });
    });
    update();
  })();

  // ---------- Prix dans la monnaie choisie ----------
  (function () {
    var table = null;
    try { table = JSON.parse($('#pb-prices').textContent); } catch (e) { return; }
    var btns = $$('.cur button');
    if (!btns.length || !table) return;
    var apply = function (code) {
      if (!table[code]) return;
      btns.forEach(function (b) { b.setAttribute('aria-pressed', b.getAttribute('data-cur') === code ? 'true' : 'false'); });
      $$('[data-p]').forEach(function (el) { var v = table[code][el.getAttribute('data-p')]; if (el.tagName === 'EM') el.hidden = !v; if (v) el.textContent = v; });
    };
    btns.forEach(function (b) {
      b.addEventListener('click', function () { var c = b.getAttribute('data-cur'); apply(c); store.set('pb-cur-' + lang, c); });
    });
    var saved = store.get('pb-cur-' + lang);
    if (saved) apply(saved);
  })();

  // ---------- Installation : téléphone, iPhone, ordinateur, navigateur d'une autre appli ----------
  (function () {
    var box = $('#inst');
    var ua = navigator.userAgent || '';
    var isIOS = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    var isAndroid = /Android/i.test(ua);
    var inApp = /FBAN|FBAV|FB_IAB|Instagram|Line\/|Snapchat|TikTok|musical_ly|Bytedance|MicroMessenger|; wv\)/i.test(ua);
    var mobile = isIOS || isAndroid || /Mobi/i.test(ua);
    var bip = win.__pbBip || null;
    var done = false;
    var state = function () {
      if (done) return 'done';
      if (inApp) return 'inapp' + (isIOS ? ' ios' : ' android');
      if (!mobile) return 'desktop';
      if (isIOS) return 'ios';
      if (bip) return 'prompt';
      return isAndroid ? 'android' : 'android ios';
    };
    var render = function () { if (box) box.setAttribute('data-s', state()); };
    render();
    win.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      bip = e;
      root.classList.add('can-install');
      render();
    });
    win.addEventListener('appinstalled', function () {
      bip = null;
      done = true;
      root.classList.remove('can-install');
      render();
    });
    var install = function () {
      if (!bip) return false;
      var p = bip;
      bip = null;
      root.classList.remove('can-install');
      try {
        p.prompt();
        if (p.userChoice && p.userChoice.then) {
          p.userChoice.then(function (r) { if (r && r.outcome === 'accepted') done = true; render(); });
        }
      } catch (e) { render(); }
      return true;
    };
    $$('[data-install]').forEach(function (b) {
      b.addEventListener('click', function () { if (!install()) render(); });
    });
    // « Accéder à l'application » : installe si le navigateur le permet, ouvre l'appli sur ordinateur,
    // sinon descend vers les explications (iPhone, navigateur d'une autre appli…).
    $$('[data-go]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        if (bip) { e.preventDefault(); install(); return; }
        if (!mobile && !inApp && C.app) { e.preventDefault(); location.href = C.app; }
      });
    });
    var copyFallback = function (text) {
      var t = doc.createElement('textarea');
      t.value = text;
      t.setAttribute('readonly', '');
      t.style.position = 'fixed';
      t.style.opacity = '0';
      doc.body.appendChild(t);
      t.select();
      try { doc.execCommand('copy'); } catch (e) {}
      doc.body.removeChild(t);
    };
    $$('[data-copy]').forEach(function (b) {
      b.addEventListener('click', function () {
        var url = b.getAttribute('data-copy');
        var msg = $('.ip-copied', b.parentNode);
        var ok = function () { if (msg) msg.textContent = C.inst_copied || ''; };
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(ok, function () { copyFallback(url); ok(); });
        } else { copyFallback(url); ok(); }
      });
    });
  })();

  // ---------- Hors connexion et installable ----------
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    win.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(function () {}); });
  }
})();
