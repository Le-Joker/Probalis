(function () {
  'use strict';
  var doc = document;
  var win = window;
  var root = doc.documentElement;
  var lang = root.lang || 'fr';
  var T = {};
  var CFG = {};
  try { T = JSON.parse(doc.getElementById('pb-i18n').textContent); } catch (e) {}
  try { CFG = JSON.parse(doc.getElementById('pb-config').textContent); } catch (e) {}
  var $$ = function (sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); };
  var fmt = function (s, o) { return String(s || '').replace(/\{(\w+)\}/g, function (_, k) { return o[k]; }); };
  var cap = function (s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; };
  var noop = function () {};
  var store = function (area) {
    return {
      get: function (k) { try { return win[area].getItem(k); } catch (e) { return null; } },
      set: function (k, v) { try { win[area].setItem(k, v); } catch (e) {} },
      del: function (k) { try { win[area].removeItem(k); } catch (e) {} }
    };
  };
  var local = store('localStorage');
  var session = store('sessionStorage');
  var reduced = win.matchMedia ? win.matchMedia('(prefers-reduced-motion: reduce)') : { matches: false };
  var loc = lang === 'fr' ? 'fr-FR' : 'en-GB';
  var F = {
    time: new Intl.DateTimeFormat(loc, { hour: '2-digit', minute: '2-digit' }),
    short: new Intl.DateTimeFormat(loc, { weekday: 'short', day: 'numeric' }),
    med: new Intl.DateTimeFormat(loc, { weekday: 'short', day: 'numeric', month: 'short' }),
    long: new Intl.DateTimeFormat(loc, { weekday: 'long', day: 'numeric', month: 'long' }),
    wd: new Intl.DateTimeFormat(loc, { weekday: 'short' }),
    dt: new Intl.DateTimeFormat(loc, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }),
    date: new Intl.DateTimeFormat(loc, { day: 'numeric', month: 'long', year: 'numeric' })
  };

  // ---------- Petits messages ----------
  var toast = function (msg) {
    var el = doc.createElement('div');
    el.className = 'toast';
    el.setAttribute('role', 'status');
    el.textContent = msg;
    doc.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 2600);
  };
  var live = doc.createElement('div');
  live.className = 'sr-only';
  live.setAttribute('aria-live', 'polite');
  doc.body.appendChild(live);

  // ---------- Thème clair / sombre (mémorisé sur l'appareil) ----------
  var media = win.matchMedia ? win.matchMedia('(prefers-color-scheme: dark)') : null;
  var isDark = function () { return root.dataset.theme ? root.dataset.theme === 'dark' : !!(media && media.matches); };
  var syncThemeColor = function () {
    var c = isDark() ? '#071426' : '#F3F5F8';
    $$('meta[name="theme-color"]').forEach(function (m) { m.setAttribute('content', c); });
  };
  if (root.dataset.theme) syncThemeColor();
  doc.addEventListener('click', function (e) {
    if (!e.target.closest('.theme')) return;
    root.dataset.theme = isDark() ? 'light' : 'dark';
    local.set('theme', root.dataset.theme);
    syncThemeColor();
  });

  // ---------- Barre de progression (comme YouTube) ----------
  // Elle suit le téléchargement réel de la page quand le serveur annonce sa taille, sinon elle avance
  // doucement à chaque morceau reçu. Elle ne recule jamais.
  var progress = (function () {
    var el, bar, val = 0, timer, hideT;
    var ensure = function () {
      if (el) return;
      el = doc.createElement('div');
      el.className = 'pb-progress';
      el.setAttribute('aria-hidden', 'true');
      bar = doc.createElement('i');
      el.appendChild(bar);
      doc.body.appendChild(el);
    };
    var set = function (v) {
      val = Math.max(val, Math.min(v, 0.994));
      bar.style.width = (val * 100).toFixed(1) + '%';
    };
    return {
      start: function () {
        ensure();
        clearTimeout(hideT);
        clearInterval(timer);
        val = 0;
        el.className = 'pb-progress on';
        bar.style.transition = 'none';
        bar.style.width = '0';
        void bar.offsetWidth;
        bar.style.transition = '';
        set(0.08);
        timer = setInterval(function () { set(val + (0.82 - val) * 0.045); }, 260);
      },
      data: function (ratio) { if (!el) return; if (ratio == null) set(val + (0.9 - val) * 0.12); else set(0.1 + 0.85 * Math.min(ratio, 1)); },
      done: function (failed) {
        if (!el) return;
        clearInterval(timer);
        val = 1;
        bar.style.width = '100%';
        if (failed) el.className = 'pb-progress on fail';
        hideT = setTimeout(function () { el.className = 'pb-progress'; }, failed ? 600 : 260);
      }
    };
  })();

  // ---------- Connexion lente ou coupée ----------
  var conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  var slowNet = function () { return !!conn && (!!conn.saveData || /(^|-)2g$/.test(conn.effectiveType || '')); };
  var goodNet = function () {
    if (root.classList.contains('lite') || (navigator.onLine === false)) return false;
    return !conn || (!conn.saveData && (!conn.effectiveType || conn.effectiveType === '4g'));
  };
  var netbar = (function () {
    var el, txt, hideT;
    var icons = {
      slow: '<svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M5 19v-3M10 19v-6M15 19V9" /><path d="M20 19V5" opacity=".35"/></svg>',
      offline: '<svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><path d="M3 3l18 18M8.5 16.5a5 5 0 0 1 7 0M5 12.5a10 10 0 0 1 4-2.4M19 12.5a10 10 0 0 0-2.3-1.7M2 8.8a14.5 14.5 0 0 1 4.2-2.6M22 8.8a14.6 14.6 0 0 0-10-3.8M12 20h.01"/></svg>',
      ok: '<svg class="ic" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m5 12 5 5 9-10"/></svg>'
    };
    var show = function (kind, msg, ms) {
      if (!el) {
        el = doc.createElement('div');
        el.className = 'netbar';
        el.setAttribute('role', 'status');
        el.innerHTML = '<span class="nb-ic"></span><span class="nb-txt"></span><button type="button"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg></button>';
        el.querySelector('button').setAttribute('aria-label', T.net_close || 'OK');
        el.querySelector('button').addEventListener('click', hide);
        txt = el.querySelector('.nb-txt');
        doc.body.appendChild(el);
      }
      clearTimeout(hideT);
      el.querySelector('.nb-ic').innerHTML = icons[kind];
      txt.textContent = msg;
      el.classList.toggle('ok', kind === 'ok');
      void el.offsetWidth;
      el.classList.add('on');
      if (ms) hideT = setTimeout(hide, ms);
    };
    var hide = function () { if (el) el.classList.remove('on'); };
    return {
      slow: function () {
        if (session.get('pb-slow-shown')) return;
        session.set('pb-slow-shown', '1');
        show('slow', T.net_slow, 6000);
      },
      offline: function () { show('offline', T.net_offline); },
      online: function () { show('ok', T.net_online, 2500); },
      hide: hide
    };
  })();
  win.addEventListener('offline', function () { netbar.offline(); });
  win.addEventListener('online', function () { netbar.online(); });
  if (navigator.onLine === false) netbar.offline();
  else if (slowNet()) setTimeout(netbar.slow, 800);
  if (conn && conn.addEventListener) {
    conn.addEventListener('change', function () { root.classList.toggle('lite', slowNet()); if (slowNet()) netbar.slow(); });
  }

  // ---------- Prix dans la monnaie du pays ----------
  var P = CFG.prices || { currencies: {}, countries: {}, plans: {}, default_currency: {} };
  var TZ = {
    'Africa/Dakar': 'SN', 'Africa/Abidjan': 'CI', 'Africa/Porto-Novo': 'BJ', 'Africa/Ouagadougou': 'BF', 'Africa/Bamako': 'ML',
    'Africa/Niamey': 'NE', 'Africa/Lome': 'TG', 'Africa/Bissau': 'GW', 'Africa/Douala': 'CM', 'Africa/Libreville': 'GA',
    'Africa/Brazzaville': 'CG', 'Africa/Ndjamena': 'TD', 'Africa/Bangui': 'CF', 'Africa/Malabo': 'GQ', 'Africa/Lagos': 'NG',
    'Africa/Accra': 'GH', 'Africa/Nairobi': 'KE', 'Africa/Kampala': 'UG', 'Africa/Dar_es_Salaam': 'TZ', 'Africa/Kigali': 'RW',
    'Africa/Lusaka': 'ZM', 'Africa/Johannesburg': 'ZA', 'Africa/Casablanca': 'MA', 'Africa/Algiers': 'DZ', 'Africa/Tunis': 'TN',
    'Africa/Kinshasa': 'CD', 'Africa/Lubumbashi': 'CD', 'Indian/Antananarivo': 'MG', 'America/Port-au-Prince': 'HT',
    'Europe/London': 'GB', 'Europe/Paris': 'FR', 'Europe/Brussels': 'BE', 'Europe/Luxembourg': 'LU', 'Europe/Berlin': 'DE',
    'Europe/Madrid': 'ES', 'Europe/Rome': 'IT', 'Europe/Lisbon': 'PT', 'Europe/Amsterdam': 'NL', 'Europe/Dublin': 'IE',
    'Europe/Vienna': 'AT', 'Europe/Helsinki': 'FI', 'Europe/Athens': 'GR', 'Europe/Monaco': 'MC', 'Europe/Zurich': 'CH',
    'America/Toronto': 'CA', 'America/Montreal': 'CA', 'America/Vancouver': 'CA', 'America/New_York': 'US',
    'America/Chicago': 'US', 'America/Denver': 'US', 'America/Los_Angeles': 'US'
  };
  var guessCountry = function () {
    var saved = local.get('pb-country');
    if (saved !== null && (saved === '' || P.countries[saved])) return saved;
    var tz = '';
    try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
    if (TZ[tz]) return TZ[tz];
    var m = /-([A-Z]{2})$/.exec(navigator.language || '');
    return m && P.countries[m[1]] ? m[1] : '';
  };
  var currencyOf = function (country) { return (country && P.countries[country]) || P.default_currency[lang] || 'EUR'; };
  var money = function (v, code, digits) {
    try {
      return new Intl.NumberFormat(lang === 'fr' ? 'fr-FR' : 'en-US', { style: 'currency', currency: code, minimumFractionDigits: digits, maximumFractionDigits: digits }).format(v);
    } catch (e) { return v + ' ' + code; }
  };

  // ---------- Compte : état gardé sur l'appareil, Supabase chargé seulement si besoin ----------
  var Acct = (function () {
    var KEY = 'pb-acct';
    var listeners = [];
    var state = null;
    try { state = JSON.parse(local.get(KEY) || 'null'); } catch (e) {}
    var demo = !!CFG.demo || !CFG.sb;
    if (state && !!state.demo !== demo) state = null;  // on est passé du mode démo au vrai mode (ou l'inverse)

    var defaults = function () {
      return { premium_until: null, email_news: false, email_reminders: true, favorite_leagues: [], lang: lang, country: null,
        is_adult: false, welcome_sent_at: null, tz: null, free_day: null, free_match: null };
    };
    var isPremium = function (s) {
      s = s === undefined ? state : s;
      var u = s && s.profile && s.profile.premium_until;
      return !!u && new Date(u).getTime() > Date.now();
    };
    var apply = function () {
      root.classList.toggle('signed', !!(state && state.user));
      root.classList.toggle('premium', isPremium());
    };
    var save = function (s) {
      state = s;
      if (s) local.set(KEY, JSON.stringify(s)); else local.del(KEY);
      apply();
      listeners = listeners.filter(function (l) { return l.alive(); });
      listeners.forEach(function (l) { l.fn(state); });
      return s;
    };
    var clone = function (o) { return JSON.parse(JSON.stringify(o)); };
    var addDays = function (until, days) {
      var base = Math.max(Date.now(), until ? new Date(until).getTime() : 0);
      return new Date(base + days * 864e5).toISOString();
    };
    apply();

    // Mode démo : tout se passe sur le téléphone
    var Demo = {
      session: function () { return Promise.resolve(state); },
      signIn: function () {
        return Promise.resolve(save({ demo: true, t: Date.now(),
          user: { id: 'demo', email: 'demo@probalis.app', name: T.demo_name, avatar: null },
          profile: Object.assign(defaults(), { is_adult: true, welcome_sent_at: new Date().toISOString() }) }));
      },
      update: function (patch) { var s = clone(state); Object.assign(s.profile, patch); return Promise.resolve(save(s)); },
      // Analyse gratuite du jour : un seul match par jour, impossible à changer avant le lendemain
      useFree: function (slug, day) {
        var s = clone(state);
        if (!s.profile.free_day || s.profile.free_day < day) { s.profile.free_day = day; s.profile.free_match = slug; }
        return Promise.resolve(save(s));
      },
      signOut: function () { return Promise.resolve(save(null)); },
      remove: function () { return Promise.resolve(save(null)); },
      welcome: function () { return Promise.resolve(); },
      checkout: function (plan) {
        var s = clone(state);
        s.profile.premium_until = addDays(s.profile.premium_until, (P.plans[plan] || { days: 7 }).days);
        save(s);
        return Promise.resolve({ demo: true, until: s.profile.premium_until });
      },
      confirm: function () { return Promise.resolve(); }
    };

    // Vrai mode : Supabase (connexion Google, profil, fonctions de paiement et d'e-mail)
    var lib = null;
    var sb = function () {
      if (lib) return lib;
      lib = new Promise(function (resolve, reject) {
        var make = function () {
          return win.supabase.createClient(CFG.sb.url, CFG.sb.key, {
            auth: { flowType: 'pkce', detectSessionInUrl: true, persistSession: true, autoRefreshToken: true } });
        };
        if (win.supabase && win.supabase.createClient) { resolve(make()); return; }
        var s = doc.createElement('script');
        s.src = CFG.sb.lib;
        if (CFG.sb.sri) s.integrity = CFG.sb.sri;
        s.crossOrigin = 'anonymous';
        s.async = true;
        s.onload = function () { try { resolve(make()); } catch (e) { reject(e); } };
        s.onerror = function () { lib = null; reject(new Error('supabase-js')); };
        doc.head.appendChild(s);
      });
      return lib;
    };
    var check = function (r) { if (r && r.error) throw r.error; return r; };
    var Real = {
      session: function () {
        return sb().then(function (c) {
          return c.auth.getSession().then(function (r) {
            var ses = r.data && r.data.session;
            if (!ses) return save(null);
            var u = ses.user;
            var md = u.user_metadata || {};
            return c.from('profiles').select('*').eq('id', u.id).maybeSingle().then(check).then(function (pr) {
              return save({ t: Date.now(), user: { id: u.id, email: u.email,
                name: md.full_name || md.name || (u.email || '').split('@')[0], avatar: md.avatar_url || md.picture || null },
                profile: Object.assign(defaults(), pr.data || {}) });
            });
          });
        });
      },
      signIn: function () {
        return sb().then(function (c) {
          return c.auth.signInWithOAuth({ provider: 'google',
            options: { redirectTo: location.origin + '/' + lang + '/compte.html' } }).then(check);
        });
      },
      update: function (patch) {
        return sb().then(function (c) {
          return c.from('profiles').update(patch).eq('id', state.user.id).select().single();
        }).then(check).then(function (r) {
          var s = clone(state);
          s.profile = Object.assign(defaults(), r.data);
          return save(s);
        });
      },
      useFree: function (slug, day) {
        return sb().then(function (c) {
          return c.rpc('use_free_analysis', { p_match: slug, p_day: day });
        }).then(check).then(function (r) {
          var row = (r.data && r.data[0]) || {};
          var s = clone(state);
          s.profile.free_day = row.free_day || null;
          s.profile.free_match = row.free_match || null;
          return save(s);
        });
      },
      signOut: function () {
        return sb().then(function (c) { return c.auth.signOut(); }).then(function () { return save(null); }, function () { return save(null); });
      },
      remove: function () {
        return sb().then(function (c) {
          return c.rpc('delete_my_account').then(check).then(function () { return c.auth.signOut(); });
        }).then(function () { return save(null); });
      },
      welcome: function () {
        return sb().then(function (c) { return c.functions.invoke('welcome', { body: { lang: lang } }); });
      },
      checkout: function (plan, country) {
        return sb().then(function (c) {
          return c.functions.invoke('checkout', { body: { plan: plan, country: country, lang: lang } });
        }).then(check).then(function (r) { return r.data; });
      },
      confirm: function (params) {
        return sb().then(function (c) { return c.functions.invoke('confirm-payment', { body: params }); });
      }
    };
    var B = demo ? Demo : Real;
    var hasToken = function () {
      try {
        for (var i = 0; i < localStorage.length; i++) if (/^sb-.+-auth-token$/.test(localStorage.key(i))) return true;
      } catch (e) {}
      return false;
    };
    return {
      demo: demo,
      get: function () { return state; },
      premium: isPremium,
      on: function (fn, alive) { listeners.push({ fn: fn, alive: alive }); },
      api: B,
      hasToken: hasToken,
      // En arrière-plan : on rafraîchit le profil (Premium acheté sur un autre appareil, etc.)
      boot: function () {
        if (demo) return;
        if (!hasToken()) { if (state) save(null); return; }
        if (state && Date.now() - (state.t || 0) < 30 * 60e3) return;
        var go = function () { B.session().catch(noop); };
        if (win.requestIdleCallback) win.requestIdleCallback(go, { timeout: 4000 }); else setTimeout(go, 1500);
      }
    };
  })();

  // =====================================================================================================
  // Initialisation d'une page (au premier chargement, puis après chaque changement de page)
  // =====================================================================================================
  var shortDay = function (d) { return cap(F.short.format(d)).replace(/^(\p{L}+)(?!\.)\s/u, lang === 'fr' ? '$1. ' : '$1 '); };
  var pad = function (n) { return (n < 10 ? '0' : '') + n; };
  var dayKey = function (d) { return d.getFullYear() + '-' + pad(d.getMonth() + 1) + '-' + pad(d.getDate()); };
  var fromKey = function (k) { var p = k.split('-'); return new Date(+p[0], +p[1] - 1, +p[2], 12); };

  var initDates = function (scope) {
    // Heures et dates dans le fuseau horaire du téléphone
    $$('time[data-ko]', scope).forEach(function (el) { el.textContent = F.time.format(new Date(el.dataset.ko)); });
    $$('[data-dshort]', scope).forEach(function (el) { el.textContent = shortDay(new Date(el.dataset.dshort)); });
    $$('[data-dmed]', scope).forEach(function (el) { el.textContent = cap(F.med.format(new Date(el.dataset.dmed))); });
    $$('[data-dt]', scope).forEach(function (el) { el.textContent = F.dt.format(new Date(el.dataset.dt)); });
    // Matchs déjà joués (plus de 2 h après le coup d'envoi) : retirés des listes
    var now = Date.now();
    $$('[data-expire]', scope).forEach(function (el) {
      if (new Date(el.dataset.expire).getTime() + 2 * 3600e3 < now) el.hidden = true;
    });
  };

  // Logos : petit repère qui pulse pendant le chargement, fondu à l'arrivée, initiales si l'image manque
  var initImages = function (scope) {
    $$('.crest img, .lgl img', scope).forEach(function (img) {
      var box = img.parentNode;
      var ok = function () { img.classList.add('ld'); box.classList.remove('wait'); };
      var drop = function () { box.classList.remove('wait'); box.classList.add('noimg'); img.remove(); };
      if (img.complete) { if (img.naturalWidth) ok(); else drop(); return; }
      box.classList.add('wait');
      img.addEventListener('load', ok);
      img.addEventListener('error', drop);
    });
  };

  var initPrices = function (scope) {
    var els = $$('[data-from-price]', scope);
    if (!els.length) return;
    var code = currencyOf(guessCountry());
    var c = P.currencies[code];
    if (!c) return;
    var txt = fmt(T.from_price, { p: money(c.week, code, c.decimals) });
    els.forEach(function (el) { el.textContent = txt; });
  };

  // ---------- Accueil : filtres par jour et par championnat ----------
  var initHome = function (scope) {
    var list = scope.querySelector('#list');
    if (!list) return;
    var cards = $$('.mcard', list);
    var groups = $$('section.lg', list);
    var ad = list.querySelector('.ad');
    var feats = $$('.featured', scope);
    var chips = $$('#chips .chip', scope);
    var daysEl = scope.querySelector('#days');
    var weekBtn = daysEl.querySelector('.week');
    var empty = scope.querySelector('#empty');
    var label = scope.querySelector('#day-label');
    var dot = scope.querySelector('#open-sheet .dot');
    var sheet = scope.querySelector('#sheet');
    var rows = $$('.lrow', sheet);
    var boxes = $$('input[type="checkbox"]', sheet);
    var applyBtn = scope.querySelector('#sheet-apply');
    var search = scope.querySelector('#sheet-search');
    var known = rows.map(function (r) { return r.dataset.league; });
    var today = dayKey(new Date());

    cards.forEach(function (c) { c._d = dayKey(new Date(c.dataset.ko)); });
    feats.forEach(function (f) { f._d = dayKey(new Date(f.dataset.ko)); });
    var days = cards.map(function (c) { return c._d; })
      .filter(function (d, i, a) { return d >= today && a.indexOf(d) === i; }).sort();

    var sel = [];
    try { sel = JSON.parse(local.get('leagues') || '[]').filter(function (c) { return known.indexOf(c) >= 0; }); } catch (e) {}
    var saved = session.get('day');
    var state = { day: saved === 'all' || days.indexOf(saved) >= 0 ? saved : (days[0] || 'all'), sel: sel };

    var pills = days.map(function (d) {
      var b = doc.createElement('button');
      var dt = fromKey(d);
      b.type = 'button';
      b.className = 'day';
      b.dataset.day = d;
      b.setAttribute('aria-label', cap(F.long.format(dt)));
      var s = doc.createElement('small');
      s.textContent = d === today ? T.today : cap(F.wd.format(dt));
      var n = doc.createElement('b');
      n.textContent = dt.getDate();
      b.appendChild(s);
      b.appendChild(n);
      daysEl.insertBefore(b, weekBtn);
      return b;
    });
    pills.push(weekBtn);

    var inSel = function (code, s) { s = s || state.sel; return !s.length || s.indexOf(code) >= 0; };
    var onDay = function (d) { return d >= today && (state.day === 'all' || d === state.day); };
    var plural = function (n) { return n === 1 ? T.one_match : fmt(T.n_matches, { n: n }); };
    var save = function () { local.set('leagues', JSON.stringify(state.sel)); session.set('day', state.day); };

    var render = function () {
      pills.forEach(function (p) {
        var on = p.dataset.day === state.day;
        p.classList.toggle('on', on);
        p.setAttribute('aria-pressed', on);
      });
      var counts = {};
      cards.forEach(function (c) { if (onDay(c._d)) counts[c.dataset.league] = (counts[c.dataset.league] || 0) + 1; });
      chips.forEach(function (ch) {
        var code = ch.dataset.league;
        var on = code ? state.sel.indexOf(code) >= 0 : !state.sel.length;
        if (code) {
          var n = counts[code] || 0;
          ch.hidden = !n && !on;
          ch.querySelector('.count').textContent = n;
        }
        ch.classList.toggle('on', on);
        ch.setAttribute('aria-pressed', on);
      });
      var shown = 0;
      cards.forEach(function (c) {
        var v = onDay(c._d) && inSel(c.dataset.league);
        c.hidden = !v;
        if (v) shown++;
      });
      groups.forEach(function (g) {
        g.hidden = !g.querySelector('.mcard:not([hidden])');
        var sa = g.querySelector('.see-all');
        if (sa) sa.hidden = state.day === 'all' && state.sel.length === 1 && state.sel[0] === g.dataset.league;
      });
      // La pub reste discrète : après le 2e championnat affiché, jamais en tête de liste
      if (ad) {
        var vis = groups.filter(function (g) { return !g.hidden; });
        ad.hidden = vis.length < 3;
        if (!ad.hidden && vis[1].nextElementSibling !== ad) vis[1].parentNode.insertBefore(ad, vis[1].nextElementSibling);
      }
      list.classList.toggle('week', state.day === 'all');
      // À la une : la plus belle affiche parmi les matchs affichés, grands championnats d'abord
      var pool = feats.filter(function (f) { f.hidden = true; return onDay(f._d) && inSel(f.dataset.league); });
      var prime = pool.filter(function (f) { return f.dataset.prime === '1'; });
      var best = null;
      (prime.length ? prime : pool).forEach(function (f) {
        if (!best || +f.dataset.stature > +best.dataset.stature) best = f;
      });
      if (best) best.hidden = false;
      empty.hidden = shown > 0;
      label.textContent = state.day === 'all' ? T.all_week : cap(F.long.format(fromKey(state.day)));
      dot.hidden = !state.sel.length;
      rows.forEach(function (r) {
        var n = counts[r.dataset.league] || 0;
        r.querySelector('.lr-count').textContent = n ? plural(n) : T.no_match_day;
        r.classList.toggle('zero', !n);
      });
    };

    daysEl.addEventListener('click', function (e) {
      var b = e.target.closest('.day');
      if (!b) return;
      state.day = b.dataset.day;
      save();
      render();
    });
    scope.querySelector('#chips').addEventListener('click', function (e) {
      var ch = e.target.closest('.chip');
      if (!ch) return;
      var code = ch.dataset.league;
      state.sel = !code || (state.sel.length === 1 && state.sel[0] === code) ? [] : [code];
      save();
      render();
    });
    list.addEventListener('click', function (e) {
      var b = e.target.closest('.see-all');
      if (!b) return;
      state.sel = [b.dataset.league];
      state.day = 'all';
      save();
      render();
      daysEl.scrollIntoView({ block: 'start', behavior: reduced.matches ? 'auto' : 'smooth' });
    });
    scope.querySelector('#reset-filter').addEventListener('click', function () {
      state.sel = [];
      save();
      render();
    });

    // Feuille « Championnats » : cases à cocher, recherche, nombre de matchs
    var checked = function () { return boxes.filter(function (b) { return b.checked; }).map(function (b) { return b.value; }); };
    var updateApply = function () {
      var s = checked();
      var n = cards.filter(function (c) { return onDay(c._d) && inSel(c.dataset.league, s); }).length;
      applyBtn.textContent = n === 1 ? T.show_one : n ? fmt(T.show_n, { n: n }) : T.show_none;
    };
    var fold = function (s) { return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim(); };
    var filterRows = function () {
      var q = fold(search.value);
      var any = false;
      rows.forEach(function (r) { r.hidden = !!q && r.dataset.search.indexOf(q) < 0; if (!r.hidden) any = true; });
      $$('.sec', sheet).forEach(function (s) { s.hidden = !s.querySelector('.lrow:not([hidden])'); });
      sheet.querySelector('.sheet-none').hidden = any;
    };
    scope.querySelector('#open-sheet').addEventListener('click', function () {
      boxes.forEach(function (b) { b.checked = state.sel.indexOf(b.value) >= 0; });
      search.value = '';
      filterRows();
      updateApply();
      if (sheet.showModal) sheet.showModal(); else sheet.setAttribute('open', '');
    });
    sheet.addEventListener('change', updateApply);
    search.addEventListener('input', filterRows);
    scope.querySelector('#sheet-reset').addEventListener('click', function () {
      boxes.forEach(function (b) { b.checked = false; });
      updateApply();
    });
    applyBtn.addEventListener('click', function () {
      state.sel = checked();
      save();
      render();
      if (sheet.close) sheet.close(); else sheet.removeAttribute('open');
    });
    sheet.addEventListener('click', function (e) { if (e.target === sheet && sheet.close) sheet.close(); });

    render();
    var on = daysEl.querySelector('.day.on');
    if (on && on.offsetLeft > daysEl.clientWidth - 60) daysEl.scrollLeft = on.offsetLeft - 20;
  };

  // ---------- Page match : onglets ----------
  var initTabs = function (scope) {
    var tabNav = scope.querySelector('.ptabs');
    if (!tabNav) return;
    var links = $$('a', tabNav);
    var panels = links.map(function (a) { return scope.querySelector('#' + a.hash.slice(1)); });
    var anchor = scope.querySelector('#tabs-anchor');
    tabNav.setAttribute('role', 'tablist');
    links.forEach(function (a, i) {
      a.setAttribute('role', 'tab');
      a.setAttribute('aria-controls', panels[i].id);
      panels[i].setAttribute('role', 'tabpanel');
      panels[i].setAttribute('aria-labelledby', a.id);
      panels[i].removeAttribute('aria-label');
    });
    var show = function (i, user) {
      links.forEach(function (a, j) {
        var on = i === j;
        a.classList.toggle('on', on);
        a.setAttribute('aria-selected', on);
        a.tabIndex = on ? 0 : -1;
        panels[j].hidden = !on;
      });
      tabNav.scrollTo({ left: Math.max(0, links[i].offsetLeft - 20), behavior: user && !reduced.matches ? 'smooth' : 'auto' });
      if (user) {
        history.replaceState(history.state, '', i ? links[i].hash : location.pathname + location.search);
        var top = anchor.getBoundingClientRect().top + win.scrollY;
        if (win.scrollY > top) win.scrollTo(0, top);
      }
    };
    tabNav.addEventListener('click', function (e) {
      var a = e.target.closest('a');
      if (!a) return;
      e.preventDefault();
      show(links.indexOf(a), true);
    });
    tabNav.addEventListener('keydown', function (e) {
      var i = links.indexOf(doc.activeElement);
      if (i < 0 || (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft')) return;
      var j = (i + (e.key === 'ArrowRight' ? 1 : links.length - 1)) % links.length;
      show(j, true);
      links[j].focus();
      e.preventDefault();
    });
    $$('[data-tab]', scope).forEach(function (a) {
      if (a.closest('.tabbar')) return;
      a.addEventListener('click', function (e) {
        var i = panels.map(function (p) { return p.id; }).indexOf(a.dataset.tab);
        if (i < 0) return;
        e.preventDefault();
        show(i, true);
      });
    });
    var start = links.map(function (a) { return a.hash; }).indexOf(location.hash);
    show(start > 0 ? start : 0, false);
  };

  // ---------- Compare ta cote ----------
  var initCompare = function (scope) {
    var cmp = scope.querySelector('#compare');
    if (!cmp) return;
    var data = {};
    try { data = JSON.parse(scope.querySelector('#cmp-data').textContent); } catch (e) { return; }
    var select = scope.querySelector('#cmp-sel');
    var input = scope.querySelector('#cmp-odds');
    var chance = scope.querySelector('#cmp-chance');
    var out = scope.querySelector('#cmp-verdict');
    var txt = out.querySelector('.v-txt');
    var nf = new Intl.NumberFormat(loc, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    var pct = function (p) { var v = Math.round(p * 100); return lang === 'fr' ? v + ' %' : v + '%'; };
    var run = function () {
      var it = data.items[select.value];
      if (!it) return;
      chance.textContent = fmt(T.chance, { p: pct(it.p), fair: nf.format(it.fair) });
      var raw = input.value.trim().replace(',', '.');
      if (!raw) { out.hidden = true; return; }
      var odds = parseFloat(raw);
      var kind, msg;
      if (!isFinite(odds) || odds <= 1 || !/^\d+(\.\d*)?$/.test(raw)) {
        kind = 'warn';
        msg = '<b>' + T.v_invalid + '</b>' + T.colon + T.v_invalid_txt;
      } else {
        var r = odds / it.fair;
        kind = r >= 1.02 ? 'good' : r >= 0.98 ? 'fair' : 'bad';
        msg = '<b>' + T['v_' + kind] + '</b>' + T.colon +
          fmt(T['v_' + kind + '_txt'], { odds: nf.format(odds), fair: nf.format(it.fair), m: pct(1 - r) }) +
          ' ' + T.v_note + (data.source === 'model' ? ' ' + T.v_model : '');
      }
      out.className = 'verdict ' + kind;
      txt.innerHTML = msg;
      out.hidden = false;
    };
    select.addEventListener('change', run);
    input.addEventListener('input', run);
    run();
  };

  // ---------- Partager un match ----------
  doc.addEventListener('click', function (e) {
    if (!e.target.closest('.share')) return;
    var url = location.href.split('#')[0];
    if (navigator.share) {
      navigator.share({ title: doc.title, url: url }).catch(noop);
    } else if (navigator.clipboard) {
      navigator.clipboard.writeText(url).then(function () { toast(T.link_copied); }, noop);
    }
  });

  var flash = function (scope, msg, kind) {
    var el = scope.querySelector('#flash');
    if (!el) { toast(msg); return; }
    el.className = 'flash' + (kind ? ' ' + kind : '');
    el.textContent = msg;
    el.hidden = false;
  };
  var params = function () {
    var o = {};
    location.search.slice(1).split('&').forEach(function (kv) {
      if (!kv) return;
      var p = kv.split('=');
      o[decodeURIComponent(p[0])] = decodeURIComponent((p[1] || '').replace(/\+/g, ' '));
    });
    return o;
  };
  var cleanUrl = function () { history.replaceState(history.state, '', location.pathname + location.hash); };
  var untilTxt = function (s) { return F.date.format(new Date(s.profile.premium_until)); };

  // ---------- Mon compte ----------
  var initAccount = function (scope) {
    var box = scope.querySelector('#acct');
    if (!box) return;
    var api = Acct.api;
    var adult = box.querySelector('#adult');
    var gbtn = box.querySelector('#google');
    var render = function (s) {
      box.dataset.state = s && s.user ? 'in' : 'out';
      if (!s || !s.user) { gbtn.disabled = false; return; }
      var u = s.user;
      var p = s.profile || {};
      box.querySelector('#acct-name').textContent = u.name || u.email;
      box.querySelector('#acct-email').textContent = u.email || '';
      var av = box.querySelector('#acct-avatar');
      av.textContent = '';
      if (u.avatar) {
        var img = doc.createElement('img');
        img.alt = '';
        img.referrerPolicy = 'no-referrer';
        img.src = u.avatar;
        img.onerror = function () { av.textContent = (u.name || '?').charAt(0).toUpperCase(); };
        av.appendChild(img);
      } else av.textContent = (u.name || u.email || '?').charAt(0).toUpperCase();
      var prem = Acct.premium(s);
      var badge = box.querySelector('#plan-badge');
      badge.className = 'plan-badge' + (prem ? ' prem' : '');
      badge.textContent = prem ? T.plan_premium : T.plan_free;
      var pt = box.querySelector('#plan-text');
      pt.textContent = prem ? fmt(T.premium_until, { d: untilTxt(s) }) : pt.dataset.free;
      var cta = box.querySelector('#plan-cta');
      cta.querySelector('span').textContent = prem ? cta.dataset.extend : cta.dataset.go;
      var dp = box.querySelector('#demo-premium');
      if (dp) dp.checked = prem;
      $$('[data-pref]', box).forEach(function (el) {
        var k = el.dataset.pref;
        if (el.type === 'checkbox') el.checked = !!p[k];
        else if (p[k]) el.value = p[k];
      });
      var fav = p.favorite_leagues || [];
      $$('.fav-chip', box).forEach(function (b) { b.setAttribute('aria-pressed', fav.indexOf(b.dataset.league) >= 0); });
    };
    var s0 = Acct.get();
    var returning = /[?&]code=/.test(location.search);
    var check = !Acct.demo && (Acct.hasToken() || returning);
    if (check && !s0) box.dataset.state = '';  // squelette le temps de vérifier la connexion
    else render(s0);
    Acct.on(render, function () { return box.isConnected; });

    var afterLogin = function (s) {
      if (!s || !s.user) return;
      var steps = Promise.resolve(s);
      var patch = {};
      if (local.get('pb-adult') === '1' && !s.profile.is_adult) patch.is_adult = true;
      local.del('pb-adult');
      // Fuseau horaire du téléphone : pour écrire l'heure des matchs dans les e-mails
      var tz = ''; try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) {}
      if (tz && s.profile.tz !== tz) patch.tz = tz;
      if (!s.profile.country) patch.country = guessCountry();
      if (Object.keys(patch).length) steps = steps.then(function () { return api.update(patch); }).catch(noop);
      if (!s.profile.welcome_sent_at) {
        api.welcome().catch(noop);
        toast(fmt(T.welcome, { n: (s.user.name || '').split(' ')[0] || '' }));
      }
      var next = local.get('pb-next');
      if (next) { local.del('pb-next'); steps.then(function () { router.go(next); }); }
      return steps;
    };

    // Retour d'un paiement
    var q = params();
    var payReturn = function () {
      // Stripe revient avec ?paiement=ok&session_id=… ; Flutterwave avec ?status=…&tx_ref=…&transaction_id=…
      if (q.paiement === 'annule' || q.status === 'cancelled' || q.status === 'failed') { flash(scope, T.pay_cancel, 'warn'); cleanUrl(); return; }
      if (q.paiement !== 'ok' && !q.transaction_id) return;
      flash(scope, T.pay_pending);
      var tries = 0;
      var confirmP = q.session_id ? api.confirm({ provider: 'stripe', session_id: q.session_id })
        : q.transaction_id ? api.confirm({ provider: 'flutterwave', transaction_id: q.transaction_id, tx_ref: q.tx_ref || '' })
          : Promise.resolve();
      cleanUrl();
      var poll = function () {
        api.session().then(function (s) {
          if (Acct.premium(s)) { flash(scope, fmt(T.pay_ok, { d: untilTxt(s) })); return; }
          if (++tries < 8) setTimeout(poll, 3500); else flash(scope, T.pay_slow, 'warn');
        }, function () { flash(scope, T.pay_slow, 'warn'); });
      };
      confirmP.then(poll, poll);
    };

    // Lien « Me désinscrire » d'une alerte : marche même sans être connecté (lien signé)
    if (q.desabo && q.u && q.t) {
      var kind = q.desabo === 'reminders' ? 'reminders' : 'news';
      var unsub = Acct.demo ? Promise.resolve(true) : fetch(CFG.sb.url + '/functions/v1/unsubscribe', {
        method: 'POST', headers: { 'Content-Type': 'application/json', apikey: CFG.sb.key },
        body: JSON.stringify({ u: q.u, k: kind, t: q.t }) }).then(function (r) { return r.ok; });
      cleanUrl();
      unsub.then(function (ok) {
        flash(scope, ok ? T['unsub_' + kind] : T.unsub_bad, ok ? undefined : 'warn');
        var st = Acct.get();
        if (ok && !Acct.demo && st && st.user && st.user.id === q.u) api.session().then(render, noop);
      }, function () { flash(scope, T.error, 'bad'); });
    }

    if (check) {
      api.session().then(function (s) {
        render(s);
        if (s && returning) { cleanUrl(); afterLogin(s); }
        payReturn();
      }, function () { render(Acct.get()); flash(scope, T.error, 'bad'); });
    } else payReturn();

    gbtn.addEventListener('click', function () {
      if (!adult.checked) {
        var lab = adult.closest('.adult');
        lab.classList.remove('shake');
        void lab.offsetWidth;
        lab.classList.add('shake');
        toast(T.adult_required);
        adult.focus();
        return;
      }
      local.set('pb-adult', '1');
      gbtn.disabled = true;
      api.signIn().then(function (s) {
        if (Acct.demo) { toast(T.demo_welcome); afterLogin(Object.assign({}, s, { profile: Object.assign({}, s.profile, { welcome_sent_at: 'x' }) })); }
      }, function () { gbtn.disabled = false; toast(T.error); });
    });

    var saveTimer;
    var savePatch = function (patch, undo) {
      api.update(patch).then(function () { toast(T.saved); }, function () { if (undo) undo(); toast(T.error); });
    };
    $$('[data-pref]', box).forEach(function (el) {
      el.addEventListener('change', function () {
        var k = el.dataset.pref;
        var patch = {};
        if (el.type === 'checkbox') {
          patch[k] = el.checked;
          savePatch(patch, function () { el.checked = !el.checked; });
        } else if (k === 'lang') {
          api.update({ lang: el.value }).then(function () { location.href = '/' + el.value + '/compte.html'; }, function () { toast(T.error); });
        }
      });
    });
    box.querySelector('#favs').addEventListener('click', function (e) {
      var b = e.target.closest('.fav-chip');
      if (!b) return;
      b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') !== 'true');
      clearTimeout(saveTimer);
      saveTimer = setTimeout(function () {
        var list = $$('.fav-chip[aria-pressed="true"]', box).map(function (x) { return x.dataset.league; });
        savePatch({ favorite_leagues: list });
      }, 700);
    });
    var dp = box.querySelector('#demo-premium');
    if (dp) dp.addEventListener('change', function () {
      api.update({ premium_until: dp.checked ? new Date(Date.now() + 7 * 864e5).toISOString() : null });
    });
    box.querySelector('#signout').addEventListener('click', function () {
      api.signOut().then(function () { toast(T.signed_out); win.scrollTo(0, 0); });
    });
    box.querySelector('#delete').addEventListener('click', function () {
      if (!win.confirm(T.delete_confirm)) return;
      api.remove().then(function () { toast(T.deleted); win.scrollTo(0, 0); }, function () { toast(T.error); });
    });
  };

  // ---------- Offres Premium ----------
  var initPremium = function (scope) {
    var plansEl = scope.querySelector('#plans');
    if (!plansEl) return;
    var select = scope.querySelector('#pay-country');
    var payBtn = scope.querySelector('#pay-btn');
    var methods = scope.querySelector('#pay-methods');
    var secure = scope.querySelector('#pay-secure');
    var plan = 'month';
    var names = null;
    try { names = new Intl.DisplayNames([lang], { type: 'region' }); } catch (e) {}
    var countries = Object.keys(P.countries).map(function (c) { return { c: c, n: names ? names.of(c) : c }; });
    countries.sort(function (a, b) { return a.n.localeCompare(b.n, lang); });
    countries.forEach(function (o) {
      var opt = doc.createElement('option');
      opt.value = o.c;
      opt.textContent = o.n;
      select.appendChild(opt);
    });
    var s = Acct.get();
    select.value = (s && s.profile && s.profile.country && P.countries[s.profile.country]) ? s.profile.country : guessCountry();
    var render = function () {
      var code = currencyOf(select.value);
      var c = P.currencies[code];
      if (!c) return;
      $$('[data-price]', scope).forEach(function (el) { el.textContent = money(c[el.dataset.price], code, c.decimals); });
      $$('[data-perday]', scope).forEach(function (el) {
        var k = el.dataset.perday;
        var days = (P.plans[k] || { days: 1 }).days;
        el.textContent = fmt(T.per_day, { p: money(c[k] / days, code, c.decimals ? 2 : 0) });
      });
      $$('.plan', plansEl).forEach(function (b) {
        var on = b.dataset.plan === plan;
        b.classList.toggle('on', on);
        b.setAttribute('aria-checked', on);
      });
      methods.textContent = methods.dataset[c.provider] || methods.textContent;
      secure.textContent = secure.dataset[c.provider] || secure.textContent;
      payBtn.querySelector('span').textContent = fmt(T.pay_btn, { p: money(c[plan], code, c.decimals) });
    };
    plansEl.addEventListener('click', function (e) {
      var b = e.target.closest('.plan');
      if (!b) return;
      plan = b.dataset.plan;
      render();
    });
    select.addEventListener('change', function () {
      local.set('pb-country', select.value);
      var st = Acct.get();
      if (st && st.user) Acct.api.update({ country: select.value || null }).catch(noop);
      render();
    });
    var showStatus = function (st) {
      if (Acct.premium(st)) flash(scope, fmt(T.already_premium, { d: untilTxt(st) }));
    };
    showStatus(s);
    var q = params();
    if (q.paiement === 'annule') { flash(scope, T.pay_cancel, 'warn'); cleanUrl(); }
    payBtn.addEventListener('click', function () {
      var st = Acct.get();
      if (!st || !st.user) {
        toast(T.need_signin);
        local.set('pb-next', location.pathname);
        router.go('compte.html');
        return;
      }
      payBtn.disabled = true;
      if (!Acct.demo) toast(T.pay_redirect);
      Acct.api.checkout(plan, select.value).then(function (r) {
        if (r && r.demo) {
          payBtn.disabled = false;
          flash(scope, fmt(T.demo_paid, { d: untilTxt(Acct.get()) }));
          win.scrollTo({ top: 0, behavior: reduced.matches ? 'auto' : 'smooth' });
        } else if (r && r.url) location.href = r.url;
        else throw new Error('checkout');
      }).catch(function () { payBtn.disabled = false; toast(T.error); });
    });
    render();
  };

  // ---------- Gratuit : 1 analyse complète par jour, avec un compte, sur le match choisi ----------
  // Le choix est gardé dans le profil (free_day, free_match) : il suit le compte sur tous ses appareils.
  var Free = {
    today: function () { return dayKey(new Date()); },
    // null : pas connecté ; sinon { m: match choisi aujourd'hui, ou null s'il reste à choisir }
    get: function () {
      var s = Acct.get();
      if (!s || !s.user) return null;
      var p = s.profile || {};
      return { m: p.free_day === Free.today() && p.free_match ? p.free_match : null };
    },
    // Nom du match choisi (pour le lien « tu l'as utilisée sur … »), gardé sur le téléphone
    name: function (slug, name) {
      if (name) local.set('pb-free-name', JSON.stringify({ m: slug, n: name }));
      try { var o = JSON.parse(local.get('pb-free-name') || 'null'); return o && o.m === slug ? o.n : null; } catch (e) { return null; }
    }
  };
  var slugOf = function (href) { var r = /match\/([^\/?#]+)\.html/.exec(href || ''); return r ? r[1] : null; };
  var initFree = function (scope) {
    var card = scope.querySelector('#free-card');
    var app = card && card.closest('.app');
    var slug = card && card.dataset.slug;
    var busy = false;
    var use = function () {
      if (busy) return;
      busy = true;
      Acct.api.useFree(slug, Free.today()).then(function () {
        busy = false;
        var f = Free.get();
        if (f && f.m === slug) { Free.name(slug, card.dataset.name); toast(T.free_unlocked); }
        render();
      }, function () { busy = false; toast(T.error); });
    };
    var render = function () {
      var f = Free.get();
      var m = f && f.m;
      $$('a.mcard, a.pick, a.featured', scope).forEach(function (a) {
        a.classList.toggle('free-ok', !!m && slugOf(a.getAttribute('href')) === m);
      });
      if (!card) return;
      var mine = !!m && m === slug;
      if (app) app.classList.toggle('free-ok', mine);
      card.dataset.state = !f ? 'signin' : mine ? 'this' : m ? 'used' : 'new';
      if (m && !mine) {
        var a = card.querySelector('[data-free-link]');
        a.textContent = Free.name(m) || T.free_other;
        a.setAttribute('href', m + '.html');
      }
      // Retour après la connexion lancée depuis ce match : on le débloque directement
      if (f && !m && local.get('pb-free-want') === slug) { local.del('pb-free-want'); use(); }
    };
    render();
    Acct.on(render, function () { return card ? card.isConnected : scope !== doc && scope.isConnected; });
    if (!card) return;
    card.querySelector('#free-use').addEventListener('click', use);
    card.querySelector('#free-signin').addEventListener('click', function () {
      local.set('pb-free-want', slug);
      local.set('pb-next', location.pathname);
      router.go(card.dataset.account);
    });
  };

  var init = function (scope) {
    initDates(scope);
    initImages(scope);
    initPrices(scope);
    initHome(scope);
    initTabs(scope);
    initCompare(scope);
    initAccount(scope);
    initPremium(scope);
    initFree(scope);
  };

  // =====================================================================================================
  // Navigation façon appli : on télécharge la page suivante en arrière-plan, on montre tout de suite un
  // squelette et la barre de progression, puis on remplace le contenu sans recharger tout le site.
  // =====================================================================================================
  var router = (function () {
    var supported = !!(win.history && history.pushState && win.fetch && win.DOMParser && doc.body.replaceWith);
    var cache = {};
    var inflight = {};
    var ctrl = null;
    var seq = 0;
    var currentKey = location.pathname + location.search;
    var FRESH = 5 * 60e3;

    var keyOf = function (href) {
      var u;
      try { u = new URL(href, location.href); } catch (e) { return null; }
      if (u.origin !== location.origin) return null;
      if (!/(\.html|\/)$/.test(u.pathname)) return null;
      if (u.pathname.split('/')[1] !== lang) return null;  // autre langue : chargement complet
      return { key: u.pathname + u.search, url: u };
    };
    var linkOf = function (e) {
      var a = e.target.closest && e.target.closest('a[href]');
      if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download') || a.dataset.lang || a.hasAttribute('data-reload')) return null;
      var k = keyOf(a.href);
      if (!k) return null;
      if (k.key === currentKey && k.url.hash) return null;  // ancre dans la même page
      return k;
    };
    var trim = function () {
      var keys = Object.keys(cache);
      if (keys.length <= 14) return;
      keys.sort(function (a, b) { return cache[a].t - cache[b].t; }).slice(0, keys.length - 14).forEach(function (k) { delete cache[k]; });
    };
    var load = function (key, signal, onData, low) {
      if (inflight[key]) return inflight[key];
      var opts = { credentials: 'same-origin', headers: { 'X-Probalis-Nav': '1' } };
      if (signal) opts.signal = signal;
      if (low) opts.priority = 'low';
      var p = fetch(key, opts).then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        if ((res.headers.get('content-type') || '').indexOf('text/html') < 0) throw new Error('type');
        var total = res.headers.get('content-encoding') ? 0 : +(res.headers.get('content-length') || 0);
        if (!res.body || !res.body.getReader || !win.TextDecoder) return res.text();
        var reader = res.body.getReader();
        var dec = new TextDecoder();
        var html = '';
        var got = 0;
        var pump = function () {
          return reader.read().then(function (r) {
            if (r.done) return html + dec.decode();
            got += r.value.length;
            html += dec.decode(r.value, { stream: true });
            if (onData) onData(total ? got / total : null);
            return pump();
          });
        };
        return pump();
      }).then(function (html) {
        cache[key] = { html: html, t: Date.now() };
        trim();
        delete inflight[key];
        return html;
      }, function (err) { delete inflight[key]; throw err; });
      inflight[key] = p;
      return p;
    };

    // Squelettes : la forme de la page suivante, affichée tout de suite
    var rep = function (s, n) { var o = ''; for (var i = 0; i < n; i++) o += s; return o; };
    var SK_TOP = '<div class="sk-top"><span class="sk sk-logo"></span><span class="sk-row"><span class="sk sk-round"></span><span class="sk sk-round"></span></span></div>';
    var skeleton = function (path) {
      if (/\/match\//.test(path)) {
        return '<div class="hero sk-hero"><div class="hero-top"><span class="sk sk-round"></span><span class="sk sk-line"></span><span class="sk sk-round"></span></div>' +
          '<div class="hero-teams"><div class="side"><span class="sk sk-disc"></span><span class="sk sk-line"></span></div><div class="hero-when"><span class="sk sk-time"></span></div>' +
          '<div class="side"><span class="sk sk-disc"></span><span class="sk sk-line"></span></div></div><span class="sk sk-bar"></span></div>' +
          '<div class="sk-row sk-days">' + rep('<span class="sk sk-tab"></span>', 4) + '</div>' + rep('<span class="sk sk-block"></span>', 3);
      }
      if (/\/(index\.html)?$/.test(path)) {
        return SK_TOP + '<span class="sk sk-kicker"></span><span class="sk sk-h1"></span>' +
          '<div class="sk-row sk-days">' + rep('<span class="sk sk-day"></span>', 7) + '</div>' +
          '<div class="sk-row sk-days">' + rep('<span class="sk sk-chip"></span>', 4) + '</div>' +
          '<span class="sk sk-feat"></span><span class="sk sk-lg"></span>' + rep('<span class="sk sk-mcard"></span>', 4);
      }
      return SK_TOP + '<span class="sk sk-kicker"></span><span class="sk sk-h1"></span><span class="sk sk-line" style="width: 92%"></span>' +
        '<span class="sk sk-line" style="width: 68%"></span>' + rep('<span class="sk sk-block"></span>', 3);
    };
    var setTab = function (path) {
      var name = path.split('/').pop() || 'index.html';
      var tab = { 'index.html': 'matches', 'paris.html': 'bets', 'ticket.html': 'ticket', 'historique.html': 'historique', 'compte.html': 'compte' }[name];
      if (!tab && /\/match\//.test(path)) tab = 'matches';
      if (!tab) return;
      $$('.tabbar a').forEach(function (a) {
        if (a.dataset.tab === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
      });
    };
    var saveScroll = function () {
      try { history.replaceState(Object.assign({}, history.state, { pb: 1, scroll: win.scrollY }), ''); } catch (e) {}
    };

    var swap = function (html, k, opts) {
      var d = new DOMParser().parseFromString(html, 'text/html');
      var app = d.querySelector('.app');
      var bar = d.querySelector('.tabbar');
      var css = d.querySelector('link[rel="stylesheet"]');
      var cur = doc.querySelector('link[rel="stylesheet"]');
      // Nouvelle version du site (styles ou scripts changés) : chargement complet
      if (!app || !bar || !css || !cur || css.getAttribute('href') !== cur.getAttribute('href') || d.documentElement.lang !== lang) return false;
      doc.title = d.title;
      var desc = d.querySelector('meta[name="description"]');
      var myDesc = doc.querySelector('meta[name="description"]');
      if (desc && myDesc) myDesc.setAttribute('content', desc.getAttribute('content'));
      var alt = d.querySelector('link[rel="alternate"]');
      var myAlt = doc.querySelector('link[rel="alternate"]');
      if (alt && myAlt) myAlt.setAttribute('href', alt.getAttribute('href'));
      doc.body.className = d.body.className;
      app = doc.adoptNode(app);
      doc.querySelector('.app').replaceWith(app);
      doc.querySelector('.tabbar').replaceWith(doc.adoptNode(bar));
      if (opts.push) history.pushState({ pb: 1, scroll: 0 }, '', k.url.href);
      currentKey = k.key;
      init(app);
      if (opts.pop && opts.scroll != null) win.scrollTo(0, opts.scroll);
      else if (k.url.hash && doc.getElementById(k.url.hash.slice(1)) && !doc.querySelector('.ptabs')) doc.getElementById(k.url.hash.slice(1)).scrollIntoView();
      else win.scrollTo(0, 0);
      if (!reduced.matches && !opts.pop) {
        app.classList.add('enter');
        setTimeout(function () { app.classList.remove('enter'); }, 400);
      }
      if (opts.push) { var main = doc.getElementById('main'); if (main) main.focus({ preventScroll: true }); }
      live.textContent = fmt(T.loaded, { t: d.title });
      return true;
    };

    var go = function (href, opts) {
      opts = opts || { push: true };
      var k = keyOf(href);
      if (!supported || !k) { location.href = href; return; }
      var my = ++seq;
      if (ctrl) ctrl.abort();
      ctrl = win.AbortController ? new AbortController() : null;
      if (!opts.pop) saveScroll();
      setTab(k.url.pathname);
      var hit = cache[k.key];
      var maxAge = opts.pop ? 30 * 60e3 : FRESH;
      if (hit && Date.now() - hit.t < maxAge) {
        if (!swap(hit.html, k, opts)) location.href = k.url.href;
        return;
      }
      progress.start();
      var old = doc.querySelector('.app');
      var sk = null;
      var skT = setTimeout(function () {
        if (my !== seq) return;
        sk = doc.createElement('div');
        sk.className = 'app skel';
        sk.setAttribute('aria-busy', 'true');
        sk.innerHTML = skeleton(k.url.pathname);
        old.replaceWith(sk);
        win.scrollTo(0, 0);
      }, 120);
      var slowT = setTimeout(function () { if (my === seq) netbar.slow(); }, 3000);
      load(k.key, ctrl && ctrl.signal, progress.data).then(function (html) {
        clearTimeout(skT);
        clearTimeout(slowT);
        if (my !== seq) return;
        if (!swap(html, k, opts)) { location.href = k.url.href; return; }
        progress.done();
      }).catch(function (err) {
        clearTimeout(skT);
        clearTimeout(slowT);
        if (my !== seq || (err && err.name === 'AbortError')) return;
        progress.done(true);
        if (sk) sk.replaceWith(old);
        setTab(location.pathname);
        if (opts.pop) { location.reload(); return; }
        if (navigator.onLine === false) netbar.offline(); else toast(T.nav_error);
      });
    };

    var prefetch = function (k) {
      if (!k || !goodNet() || inflight[k.key] || (cache[k.key] && Date.now() - cache[k.key].t < FRESH)) return;
      load(k.key, null, null, true).catch(noop);
    };

    var start = function () {
      if (!supported) return;
      try { history.scrollRestoration = 'manual'; } catch (e) {}
      history.replaceState(Object.assign({}, history.state, { pb: 1, scroll: win.scrollY }), '');
      doc.addEventListener('click', function (e) {
        if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        var k = linkOf(e);
        if (!k) {
          // Changement de langue : la barre de progression montre que ça charge
          if (e.target.closest && e.target.closest('a[data-lang]')) { local.set('lang', e.target.closest('a[data-lang]').dataset.lang); progress.start(); }
          return;
        }
        e.preventDefault();
        go(k.url.href, { push: true });
      });
      win.addEventListener('popstate', function (e) {
        var key = location.pathname + location.search;
        if (key === currentKey) return;  // simple changement d'onglet (#)
        go(location.href, { pop: true, scroll: e.state && e.state.scroll });
      });
      // Préchargement au survol ou au toucher (seulement avec une bonne connexion)
      var hoverT;
      doc.addEventListener('mouseover', function (e) {
        var k = linkOf(e);
        if (!k) return;
        clearTimeout(hoverT);
        hoverT = setTimeout(function () { prefetch(k); }, 70);
      });
      doc.addEventListener('touchstart', function (e) { prefetch(linkOf(e)); }, { passive: true });
      // Les pages légères de la barre d'onglets sont préparées quand le téléphone ne fait rien
      var idle = function () {
        $$('.tabbar a:not([aria-current])').forEach(function (a) {
          var k = keyOf(a.href);
          if (k && !/\/(index\.html)?$/.test(k.url.pathname)) prefetch(k);
        });
      };
      if (win.requestIdleCallback) win.requestIdleCallback(idle, { timeout: 6000 }); else setTimeout(idle, 3000);
    };
    return { start: start, go: go };
  })();

  init(doc);
  router.start();
  Acct.boot();

  // ---------- Application installable et utilisable hors connexion ----------
  if ('serviceWorker' in navigator && location.protocol !== 'file:') {
    win.addEventListener('load', function () { navigator.serviceWorker.register('/sw.js').catch(noop); });
  }
})();
