/* Probalis Office · l'appli de l'administrateur (page /office/, en français seulement).
   Tout passe par la fonction Supabase « admin », qui vérifie à chaque appel que le compte connecté est dans ADMIN_EMAILS.
   En mode démo, de faux membres sont fabriqués ici : rien n'est envoyé ni enregistré. */
(function () {
  'use strict';
  var PB = window.Probalis;
  var doc = document;
  var win = window;
  var box = doc.getElementById('adm');
  if (!PB || !box) return;
  var toast = PB.toast;
  var esc = PB.esc;
  var P = PB.P || { plans: {}, currencies: {}, countries: {} };
  var $ = function (sel, el) { return (el || doc).querySelector(sel); };
  var $$ = function (sel, el) { return Array.prototype.slice.call((el || doc).querySelectorAll(sel)); };
  var DATA = { plans: Object.keys(P.plans || {}), currencies: Object.keys(P.currencies || {}) };
  try { DATA = JSON.parse($('#adm-data').textContent); } catch (e) {}

  // ---------- Libellés ----------
  var DUR = { week: '7 jours', month: '30 jours', quarter: '3 mois', half: '6 mois', year: '1 an' };
  var pass = function (plan) { return 'Pass ' + (DUR[plan] || plan || ''); };
  var giftLabel = function (r) { return r.kind === 'premium' ? 'Premium · ' + (DUR[r.plan] || r.plan) : analyses(r.amount); };
  var analyses = function (n) { return n + (n > 1 ? ' analyses de match' : ' analyse de match'); };
  var SOURCE = { gift: 'Cadeau', referral_signup: 'Parrainage · inscription', referral_active: 'Parrainage · ami actif',
    referral_purchase: 'Parrainage · achat', welcome_bonus: 'Bienvenue (invité)' };
  var RSTATUS = { sent: ['Pas encore ouvert', 'wait'], available: ['À activer', 'open'], used: ['Utilisé', 'ok'],
    expired: ['Expiré', 'off'], cancelled: ['Annulé', 'off'] };
  var PSTATUS = { pending: ['En attente', 'wait'], paid: ['Payé', 'ok'], failed: ['Échoué', 'bad'], cancelled: ['Annulé', 'off'],
    refunded: ['Remboursé', 'off'] };
  var PROVIDER = { manual: 'WhatsApp (direct)', stripe: 'Carte (Stripe)', flutterwave: 'Flutterwave' };
  var EMAIL = { welcome: 'Bienvenue', receipt: 'Reçu de paiement', expiry: 'Fin du Premium', big_match: 'Grand match',
    gift: 'Cadeau', reward: 'Récompense', premium_on: 'Premium activé' };
  var ACTION = { gift: 'Cadeau offert', resend_gift: 'Cadeau renvoyé', cancel_reward: 'Récompense annulée',
    manual_payment: 'Paiement WhatsApp enregistré', end_premium: 'Premium arrêté', settings: 'Barème du parrainage modifié',
    broadcast: 'Annonce envoyée' };
  var FR = 'fr-FR';
  var fDay = new Intl.DateTimeFormat(FR, { day: 'numeric', month: 'short', year: 'numeric' });
  var fDt = new Intl.DateTimeFormat(FR, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  var fWd = new Intl.DateTimeFormat(FR, { weekday: 'short', day: 'numeric', month: 'short' });
  var day = function (v) { return v ? fDay.format(new Date(v)) : '—'; };
  var dt = function (v) { return v ? fDt.format(new Date(v)) : '—'; };
  var num = function (n) { return new Intl.NumberFormat(FR).format(n || 0); };
  var cash = function (v, cur) {
    var c = P.currencies && P.currencies[cur];
    try {
      return new Intl.NumberFormat(FR, { style: 'currency', currency: cur, minimumFractionDigits: c ? c.decimals : 0,
        maximumFractionDigits: c ? c.decimals : 2 }).format(v);
    } catch (e) { return v + ' ' + cur; }
  };
  var price = function (plan, cur) { var c = P.currencies && P.currencies[cur]; return c && c[plan]; };
  var ic = function (n) { var t = $('#ic-' + n); return t ? t.innerHTML : ''; };
  var premiumOn = function (m) { return !!m.premium_until && new Date(m.premium_until) > new Date(); };
  var initials = function (name) {
    return String(name || '?').trim().split(/\s+/).slice(0, 2).map(function (w) { return w.charAt(0); }).join('').toUpperCase();
  };
  var pill = function (pair) { return '<span class="adm-tag ' + pair[1] + '">' + esc(pair[0]) + '</span>'; };
  var ERR = {
    auth: 'Session expirée : reconnecte-toi.', forbidden: "Ce compte n'a pas accès à l'administration.", plan: 'Formule inconnue.',
    amount: 'Montant invalide.', currency: 'Monnaie inconnue.', unknown: 'Membre introuvable.', id: 'Identifiant invalide.',
    not_resendable: 'Ce cadeau ne peut plus être renvoyé.', not_cancellable: 'Cette récompense ne peut plus être annulée.',
    text: 'Titre et texte obligatoires.', server: 'Erreur du serveur : réessaie dans un instant.', demo: 'Indisponible en mode démo.'
  };
  var errText = function (e) { return ERR[e && (e.code || e.message)] || 'Erreur : ' + ((e && (e.code || e.message)) || 'inconnue'); };

  // =====================================================================================================
  // Mode démo : faux membres, tout reste dans cette page
  // =====================================================================================================
  var Demo = (function () {
    var seed = 7;
    var rnd = function () { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
    var pick = function (a) { return a[Math.floor(rnd() * a.length)]; };
    var uid = function () {
      var h = '';
      for (var i = 0; i < 32; i++) h += Math.floor(rnd() * 16).toString(16);
      return h.slice(0, 8) + '-' + h.slice(8, 12) + '-4' + h.slice(13, 16) + '-a' + h.slice(17, 20) + '-' + h.slice(20, 32);
    };
    var ago = function (days) { return new Date(Date.now() - days * 864e5).toISOString(); };
    var NAMES = ['Awa Diallo', 'Jean-Paul Kamga', 'Fatou Ndiaye', 'Moussa Traoré', 'Aïcha Mbarga', 'Kevin Ekotto', 'Mariam Coulibaly',
      'Patrick Nana', 'Grace Tchoumi', 'Ibrahim Sow', 'Chantal Essomba', 'Yannick Fotso', 'Nadia Bello', 'Serge Mvondo',
      'Ruth Ngo Bayiha', 'Samuel Owona', 'Aminata Keïta', 'Brice Talla', 'Estelle Nkoulou', 'Olivier Ateba', 'Linda Manga',
      'Hervé Djoko', 'Sandrine Abena', 'Cédric Onana', 'Prisca Mballa', 'Thierry Zambo'];
    var COUNTRIES = ['CM', 'CM', 'CM', 'CI', 'SN', 'FR', 'CM', 'GA', 'BE', 'CM'];
    var code = function () { var a = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789', s = ''; for (var i = 0; i < 6; i++) s += pick(a.split('')); return s; };
    var db = { members: [], rewards: [], payments: [], emails: [], log: [], subs: {},
      referral: { signup: 2, active: 3, active_days: 3, welcome: 2, monthly_cap: 10, purchase: { week: 4, month: 5, quarter: 6, half: 8, year: 10 } } };
    NAMES.forEach(function (name, i) {
      var since = Math.floor(rnd() * 40) + (i === 0 ? 0 : 1) - (i < 2 ? 1 : 0);
      var slug = name.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z]+/g, '.');
      var m = { id: uid(), email: slug + '@exemple.com', name: name, avatar_url: null, country: pick(COUNTRIES), lang: rnd() < 0.85 ? 'fr' : 'en',
        premium_until: rnd() < 0.25 ? ago(-Math.floor(rnd() * 80 + 2)) : null, bonus_analyses: rnd() < 0.3 ? Math.floor(rnd() * 6) : 0,
        extra_matches: [], created_at: ago(Math.max(0, since) + rnd() * 0.9), last_seen: ago(Math.floor(rnd() * 9)).slice(0, 10),
        active_days: Math.floor(rnd() * 25) + 1, ref_code: code(), referred_by: null, role: 'member', email_news: rnd() < 0.5,
        email_reminders: true, push_daily: true, free_day: null, free_match: null };
      db.members.push(m);
      if (rnd() < 0.45) db.subs[m.id] = 1 + Math.floor(rnd() * 2);
      db.emails.push({ id: db.emails.length + 1, user_id: m.id, kind: 'welcome', ref: 'welcome', created_at: m.created_at });
    });
    db.members.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    // Quelques parrainages, récompenses et paiements
    db.members.slice(0, 9).forEach(function (m, i) {
      var sp = db.members[10 + (i % 4)];
      m.referred_by = sp.id;
      db.rewards.push({ id: uid(), user_id: sp.id, kind: 'analyses', plan: null, days: null, amount: 2, source: 'referral_signup', note: null,
        status: rnd() < 0.5 ? 'used' : 'available', created_at: m.created_at, expires_at: null, claimed_at: null, used_at: null });
      db.rewards.push({ id: uid(), user_id: m.id, kind: 'analyses', plan: null, days: null, amount: 2, source: 'welcome_bonus', note: null,
        status: 'available', created_at: m.created_at, expires_at: null, claimed_at: null, used_at: null });
    });
    db.members.filter(premiumOn).forEach(function (m) {
      var plan = pick(['week', 'month', 'month', 'quarter', 'year']);
      var cur = (P.countries && P.countries[m.country]) || 'XAF';
      var p = { id: uid(), user_id: m.id, provider: 'manual', plan: plan, days: (P.plans[plan] || {}).days, currency: cur,
        amount: price(plan, cur) || 3000, status: 'paid', created_at: ago(rnd() * 20), note: 'Orange Money' };
      p.paid_at = p.created_at;
      db.payments.push(p);
      db.emails.push({ id: db.emails.length + 1, user_id: m.id, kind: 'receipt', ref: p.id, created_at: p.paid_at });
    });
    db.rewards.push({ id: uid(), user_id: db.members[3].id, kind: 'premium', plan: 'month', days: 30, amount: null, source: 'gift',
      note: 'Merci pour tes retours !', status: 'sent', created_at: ago(2), expires_at: ago(-28), claimed_at: null, used_at: null });
    db.rewards.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    db.payments.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });
    db.emails.sort(function (a, b) { return a.created_at < b.created_at ? 1 : -1; });

    var byId = function (id) { return db.members.filter(function (m) { return m.id === id; })[0]; };
    var named = function (rows) {
      return rows.map(function (r) { var m = byId(r.user_id); return Object.assign({}, r, { member: m ? { name: m.name, email: m.email } : null }); });
    };
    var fail = function (c) { var e = new Error(c); e.code = c; return Promise.reject(e); };
    var log = function (action, target, detail) { db.log.unshift({ id: db.log.length + 1, action: action, target: target, detail: detail || {}, created_at: new Date().toISOString(), user_id: target }); };
    var link = function (r) { return location.origin + '/fr/recompenses.html?r=' + r.id + '&t=demo'; };
    var page = function (rows, b, n) { var o = +(b.offset || 0); return rows.slice(o, o + (n || 50)); };
    var later = function (v) { return new Promise(function (res) { setTimeout(function () { res(JSON.parse(JSON.stringify(v))); }, 220); }); };

    var actions = {
      me: function () { return { ok: true, admin: true }; },
      stats: function () {
        var now = Date.now();
        var since = function (r, d) { return now - new Date(r.created_at) < d * 864e5; };
        var today = new Date(); today.setHours(0, 0, 0, 0);
        var rev = {};
        db.payments.filter(function (p) { return p.status === 'paid' && since(p, 30); }).forEach(function (p) { rev[p.currency] = (rev[p.currency] || 0) + p.amount; });
        var days = [];
        for (var i = 13; i >= 0; i--) {
          var d0 = new Date(today.getTime() - i * 864e5);
          var d1 = new Date(d0.getTime() + 864e5);
          days.push({ d: d0.toISOString().slice(0, 10), n: db.members.filter(function (m) { var c = new Date(m.created_at); return c >= d0 && c < d1; }).length });
        }
        return { ok: true, stats: {
          members: db.members.length, new_today: db.members.filter(function (m) { return new Date(m.created_at) >= today; }).length,
          new_7d: db.members.filter(function (m) { return since(m, 7); }).length,
          active_7d: db.members.filter(function (m) { return now - new Date(m.last_seen) < 7 * 864e5; }).length,
          premium: db.members.filter(premiumOn).length, push: Object.keys(db.subs).length,
          referred_30d: db.members.filter(function (m) { return m.referred_by && since(m, 30); }).length,
          payments_30d: db.payments.filter(function (p) { return p.status === 'paid' && since(p, 30); }).length, revenue_30d: rev,
          gifts_pending: db.rewards.filter(function (r) { return r.status === 'sent'; }).length,
          rewards_open: db.rewards.filter(function (r) { return r.status === 'available'; }).length,
          rewards_30d: db.rewards.filter(function (r) { return since(r, 30); }).length,
          emails_today: db.emails.filter(function (e) { return new Date(e.created_at) >= today; }).length,
          emails_30d: db.emails.filter(function (e) { return since(e, 30); }).length, signups_14d: days } };
      },
      members: function (b) {
        var q = String(b.q || '').toLowerCase();
        var rows = db.members.filter(function (m) {
          if (q && m.name.toLowerCase().indexOf(q) < 0 && m.email.indexOf(q) < 0 && m.ref_code !== q.toUpperCase()) return false;
          if (b.filter === 'premium') return premiumOn(m);
          if (b.filter === 'free') return !premiumOn(m);
          if (b.filter === 'referred') return !!m.referred_by;
          return true;
        }).map(function (m) {
          var sp = byId(m.referred_by);
          return Object.assign({}, m, { referred_by_name: sp ? sp.name : null, push: !!db.subs[m.id],
            referrals: db.members.filter(function (f) { return f.referred_by === m.id; }).length });
        });
        return { ok: true, members: page(rows, b, b.limit || 30), total: rows.length };
      },
      member: function (b) {
        var m = byId(b.id);
        if (!m) return fail('unknown');
        return { ok: true, member: m, devices: db.subs[m.id] || 0,
          rewards: db.rewards.filter(function (r) { return r.user_id === m.id; }),
          payments: db.payments.filter(function (p) { return p.user_id === m.id; }),
          friends: db.members.filter(function (f) { return f.referred_by === m.id; }),
          emails: db.emails.filter(function (e) { return e.user_id === m.id; }) };
      },
      gift: function (b) {
        var m = byId(b.id);
        if (!m) return fail('unknown');
        var r = { id: uid(), user_id: m.id, kind: b.kind === 'analyses' ? 'analyses' : 'premium', source: 'gift', note: b.note || null,
          status: 'sent', created_at: new Date().toISOString(), expires_at: ago(-30), claimed_at: null, used_at: null };
        if (r.kind === 'premium') { r.plan = b.plan; r.days = (P.plans[b.plan] || {}).days; } else r.amount = Math.max(1, Math.min(100, b.amount | 0));
        db.rewards.unshift(r);
        db.emails.unshift({ id: db.emails.length + 1, user_id: m.id, kind: 'gift', ref: r.id, created_at: r.created_at });
        log('gift', m.id, { kind: r.kind, plan: r.plan || null, amount: r.amount || null, emailed: false });
        return { ok: true, reward: r.id, link: link(r), emailed: false, pushed: !!db.subs[m.id], label: giftLabel(r) };
      },
      resend_gift: function (b) {
        var r = db.rewards.filter(function (x) { return x.id === b.reward; })[0];
        if (!r || r.source !== 'gift' || (r.status !== 'sent' && r.status !== 'expired')) return fail('not_resendable');
        r.status = 'sent';
        r.expires_at = ago(-30);
        log('resend_gift', r.user_id, { reward: r.id });
        return { ok: true, link: link(r), emailed: false, pushed: !!db.subs[r.user_id] };
      },
      cancel_reward: function (b) {
        var r = db.rewards.filter(function (x) { return x.id === b.reward; })[0];
        if (!r || (r.status !== 'sent' && r.status !== 'available')) return fail('not_cancellable');
        r.status = 'cancelled';
        log('cancel_reward', r.user_id, { reward: r.id });
        return { ok: true };
      },
      manual_payment: function (b) {
        var m = byId(b.id);
        if (!m) return fail('unknown');
        var days = (P.plans[b.plan] || {}).days || 0;
        var start = premiumOn(m) ? new Date(m.premium_until).getTime() : Date.now();
        m.premium_until = new Date(start + days * 864e5).toISOString();
        var p = { id: uid(), user_id: m.id, provider: 'manual', plan: b.plan, days: days, currency: b.currency, amount: +b.amount,
          status: 'paid', created_at: new Date().toISOString(), paid_at: new Date().toISOString(), note: b.note || null };
        db.payments.unshift(p);
        db.emails.unshift({ id: db.emails.length + 1, user_id: m.id, kind: 'receipt', ref: p.id, created_at: p.paid_at });
        log('manual_payment', m.id, { plan: b.plan, currency: b.currency, amount: +b.amount });
        return { ok: true, payment: p.id, premium_until: m.premium_until };
      },
      end_premium: function (b) {
        var m = byId(b.id);
        if (!m) return fail('unknown');
        log('end_premium', m.id, { was: m.premium_until });
        m.premium_until = new Date().toISOString();
        return { ok: true };
      },
      rewards: function (b) {
        var rows = db.rewards.filter(function (r) {
          return (!b.status || r.status === b.status) && (!b.source || (b.source === 'gift' ? r.source === 'gift' : r.source !== 'gift'));
        });
        return { ok: true, rewards: named(page(rows, b)) };
      },
      payments: function (b) { return { ok: true, payments: named(page(db.payments, b)) }; },
      emails: function (b) { return { ok: true, emails: named(page(db.emails, b)) }; },
      log: function (b) { return { ok: true, log: named(page(db.log, b, 60)) }; },
      settings: function () { return { ok: true, referral: db.referral }; },
      settings_set: function (b) { db.referral = b.referral; log('settings', null, { referral: b.referral }); return { ok: true, referral: db.referral }; },
      push_test: function () { return { ok: true, sent: 0 }; },
      broadcast: function (b) {
        var n = Object.keys(db.subs).reduce(function (s, k) { return s + db.subs[k]; }, 0);
        log('broadcast', null, { title: b.title, body: b.body, sent: n });
        return { ok: true, sent: n, devices: n };
      },
      email_test: function () { return { ok: false }; }
    };
    return {
      call: function (b) {
        var f = actions[b.action];
        if (!f) return fail('action');
        var out = f(b);
        return out && out.then ? out : later(out);
      }
    };
  })();

  var api = function (action, body) {
    var b = Object.assign({ action: action }, body || {});
    return PB.acct.demo ? Demo.call(b) : PB.acct.fn('admin', b);
  };

  // =====================================================================================================
  // Fenêtre commune (fiche, menu ⋮, formulaires, confirmation)
  // =====================================================================================================
  var sheet = $('#adm-sheet');
  var sheetBody = $('#adm-sheet-body');
  var sheetTitle = $('#adm-sheet-title');
  var onClose = null;
  var open = function (title, html, after) {
    sheetTitle.textContent = title;
    sheetBody.innerHTML = html;
    sheetBody.scrollTop = 0;
    if (!sheet.open) { if (sheet.showModal) sheet.showModal(); else sheet.setAttribute('open', ''); }
    if (after) after(sheetBody);
  };
  var close = function () {
    if (sheet.open) { if (sheet.close) sheet.close(); else sheet.removeAttribute('open'); }
  };
  sheet.addEventListener('close', function () { var f = onClose; onClose = null; if (f) f(); });
  $('#adm-close').addEventListener('click', close);
  sheet.addEventListener('click', function (e) { if (e.target === sheet) close(); });
  // Écran de confirmation dans la fenêtre : « Oui » lance l'action, « Annuler » revient à l'écran d'avant
  var confirmIn = function (title, text, okLabel, danger, run, back) {
    open(title, '<p class="adm-confirm">' + text + '</p><div class="adm-sheet-actions">' +
      '<button class="btn' + (danger ? ' danger' : '') + '" type="button" data-ok>' + esc(okLabel) + '</button>' +
      '<button class="btn ghost" type="button" data-no>Annuler</button></div>', function (b) {
      $('[data-no]', b).addEventListener('click', function () { if (back) back(); else close(); });
      var ok = $('[data-ok]', b);
      ok.addEventListener('click', function () {
        ok.disabled = true;
        run().catch(function (e) { ok.disabled = false; toast(errText(e)); });
      });
    });
  };
  var busy = function (btn, on) { if (btn) { btn.disabled = on; btn.classList.toggle('is-busy', on); } };
  var copy = function (text) {
    var done = function () { toast('Lien copié'); };
    if (navigator.clipboard && navigator.clipboard.writeText) return navigator.clipboard.writeText(text).then(done, function () { win.prompt('Copie ce lien :', text); });
    win.prompt('Copie ce lien :', text);
  };
  // Lien d'un cadeau (à partager si l'e-mail n'est pas parti)
  var linkBlock = function (url, name) {
    var msg = 'Bonjour ' + (name || '').split(' ')[0] + ' ! Probalis t’a fait un cadeau. Ouvre ce lien pour l’activer : ' + url;
    return '<div class="adm-link"><input class="num" readonly value="' + esc(url) + '" aria-label="Lien du cadeau">' +
      '<div class="adm-sheet-actions two"><button class="btn ghost" type="button" data-copy="' + esc(url) + '">' + ic('copy') + 'Copier</button>' +
      '<a class="btn wa" target="_blank" rel="noopener" href="https://wa.me/?text=' + encodeURIComponent(msg) + '">' + ic('chat') + 'WhatsApp</a></div></div>';
  };
  sheetBody.addEventListener('click', function (e) {
    var c = e.target.closest('[data-copy]');
    if (c) copy(c.getAttribute('data-copy'));
  });

  // =====================================================================================================
  // Membres : liste, menu ⋮, fiche, cadeau, paiement, arrêt du Premium
  // =====================================================================================================
  var avatar = function (m) {
    return m.avatar_url ? '<span class="adm-av"><img src="' + esc(m.avatar_url) + '" alt="" loading="lazy" referrerpolicy="no-referrer"></span>'
      : '<span class="adm-av">' + esc(initials(m.name || m.email)) + '</span>';
  };
  var memberTags = function (m) {
    var t = [];
    t.push(premiumOn(m) ? '<span class="adm-tag gold">' + ic('crown') + 'Premium · ' + esc(day(m.premium_until)) + '</span>' : '<span class="adm-tag">Gratuit</span>');
    if (m.bonus_analyses > 0) t.push('<span class="adm-tag open">' + ic('zap') + m.bonus_analyses + '</span>');
    if (m.referrals > 0) t.push('<span class="adm-tag">' + ic('users') + m.referrals + '</span>');
    if (m.push) t.push('<span class="adm-tag" title="Notifications activées">' + ic('bell') + '</span>');
    if (m.role === 'admin') t.push('<span class="adm-tag night">Admin</span>');
    return t.join('');
  };
  var memberRow = function (m) {
    var el = doc.createElement('article');
    el.className = 'adm-item member';
    el.innerHTML = avatar(m) +
      '<button class="ai-main" type="button" data-open><b>' + esc(m.name || '—') + '</b><small>' + esc(m.email || '') + '</small>' +
      '<small class="ai-sub">Inscrit le ' + esc(day(m.created_at)) + (m.referred_by_name ? ' · parrainé par ' + esc(m.referred_by_name) : '') + '</small>' +
      '<span class="ai-tags">' + memberTags(m) + '</span></button>' +
      '<button class="round ai-more" type="button" data-menu aria-label="Actions pour ' + esc(m.name || m.email) + '">' + ic('more') + '</button>';
    $('[data-open]', el).addEventListener('click', function () { showMember(m.id); });
    $('[data-menu]', el).addEventListener('click', function () { menu(m); });
    return el;
  };
  var menu = function (m, back) {
    var items = [
      ['gift-premium', 'crown', 'Offrir le Premium', 'Une des 5 formules, par e-mail avec un bouton « Activer la récompense »'],
      ['gift-analyses', 'zap', 'Offrir des analyses de match', 'Le membre choisit les matchs qu’il ouvre'],
      ['pay', 'card', 'Paiement WhatsApp reçu', 'Active le Premium et envoie le reçu'],
      ['open', 'user', 'Voir la fiche', 'Récompenses, paiements, filleuls, e-mails']
    ];
    if (premiumOn(m)) items.push(['end', 'x', 'Arrêter le Premium', 'Jusqu’ici : ' + day(m.premium_until)]);
    open(m.name || m.email, '<div class="adm-menu">' + items.map(function (it) {
      return '<button type="button" class="am-row' + (it[0] === 'end' ? ' danger' : '') + '" data-act="' + it[0] + '"><span class="am-ic">' + ic(it[1]) +
        '</span><span class="am-txt"><b>' + esc(it[2]) + '</b><small>' + esc(it[3]) + '</small></span></button>';
    }).join('') + '</div>', function (b) {
      $$('[data-act]', b).forEach(function (btn) {
        btn.addEventListener('click', function () {
          var a = btn.getAttribute('data-act');
          var again = function () { menu(m, back); };
          if (a === 'gift-premium') giftForm(m, 'premium', again);
          else if (a === 'gift-analyses') giftForm(m, 'analyses', again);
          else if (a === 'pay') payForm(m, again);
          else if (a === 'open') showMember(m.id);
          else if (a === 'end') endPremium(m, again);
        });
      });
    });
  };

  var planCards = function (name, cur, checked) {
    return '<div class="plan-pick" role="radiogroup" aria-label="Formule">' + DATA.plans.map(function (p) {
      var v = price(p, cur);
      return '<label class="pp"><input type="radio" name="' + name + '" value="' + p + '"' + (p === checked ? ' checked' : '') + '>' +
        '<b>' + esc(DUR[p] || p) + '</b><small>' + (v != null ? esc(cash(v, cur)) : '') + '</small></label>';
    }).join('') + '</div>';
  };
  var curOf = function (m) { return (P.countries && P.countries[m.country]) || 'XAF'; };

  var giftForm = function (m, kind, back) {
    var first = (m.name || '').split(' ')[0];
    var cur = curOf(m);
    var body = kind === 'premium'
      ? '<p class="note">Valeur indiquée en ' + esc(cur) + '. Le temps offert s’ajoute au Premium en cours.</p>' + planCards('plan', cur, 'month')
      : '<div class="stepper"><button type="button" class="round" data-step="-1" aria-label="Une de moins">−</button>' +
        '<input class="num" name="amount" type="number" min="1" max="100" value="3" inputmode="numeric" aria-label="Nombre d’analyses">' +
        '<button type="button" class="round" data-step="1" aria-label="Une de plus">+</button></div>' +
        '<div class="adm-chips small">' + [2, 3, 5, 10].map(function (n) { return '<button type="button" data-n="' + n + '">' + n + '</button>'; }).join('') + '</div>';
    open(kind === 'premium' ? 'Offrir le Premium' : 'Offrir des analyses',
      '<form class="adm-sheet-form" novalidate><p class="adm-who">' + avatar(m) + '<span><b>' + esc(m.name || '—') + '</b><small>' + esc(m.email || '') + '</small></span></p>' + body +
      '<label class="adm-field"><span>Petit mot (facultatif, dans l’e-mail)</span><textarea name="note" maxlength="280" rows="2" placeholder="Ex. : Merci de faire connaître Probalis, ' + esc(first) + ' !"></textarea></label>' +
      '<p class="note">' + esc(first || 'Le membre') + ' reçoit un e-mail avec le bouton « Activer la récompense » (et une notification si son téléphone est abonné). Le cadeau l’attend 30 jours.</p>' +
      '<div class="adm-sheet-actions"><button class="btn" type="submit" data-go></button><button class="btn ghost" type="button" data-back>Retour</button></div></form>',
      function (b) {
        var form = $('form', b);
        var go = $('[data-go]', b);
        var label = function () {
          if (kind === 'premium') { var p = (form.querySelector('input[name=plan]:checked') || {}).value; go.innerHTML = ic('gift') + 'Offrir le ' + esc(pass(p)); }
          else { var n = Math.max(1, Math.min(100, +form.amount.value || 1)); go.innerHTML = ic('gift') + 'Offrir ' + esc(analyses(n)); }
        };
        form.addEventListener('input', label);
        form.addEventListener('change', label);
        $$('[data-step]', b).forEach(function (s) {
          s.addEventListener('click', function () { form.amount.value = Math.max(1, Math.min(100, (+form.amount.value || 0) + +s.getAttribute('data-step'))); label(); });
        });
        $$('[data-n]', b).forEach(function (s) { s.addEventListener('click', function () { form.amount.value = s.getAttribute('data-n'); label(); }); });
        $('[data-back]', b).addEventListener('click', back);
        label();
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var payload = { id: m.id, kind: kind, note: form.note.value.trim() };
          if (kind === 'premium') payload.plan = (form.querySelector('input[name=plan]:checked') || {}).value;
          else payload.amount = Math.max(1, Math.min(100, +form.amount.value || 0));
          busy(go, true);
          api('gift', payload).then(function (r) {
            refreshSoon();
            open('Cadeau envoyé', '<div class="adm-done"><span class="adm-ok-ic">' + ic('check') + '</span><b>' + esc(r.label || giftLabel(payload)) + '</b>' +
              '<small>pour ' + esc(m.name || m.email) + '</small></div>' +
              '<ul class="adm-sent"><li class="' + (r.emailed ? 'ok' : 'no') + '">' + ic(r.emailed ? 'check' : 'x') + (r.emailed ? 'E-mail envoyé' : 'E-mail pas envoyé (l’envoi des e-mails n’est pas encore réglé)') + '</li>' +
              '<li class="' + (r.pushed ? 'ok' : 'no') + '">' + ic(r.pushed ? 'check' : 'x') + (r.pushed ? 'Notification envoyée' : 'Pas de notification (téléphone non abonné)') + '</li></ul>' +
              '<p class="note">Tu peux aussi lui envoyer ce lien sur WhatsApp. Il ne marche qu’avec son compte.</p>' + linkBlock(r.link, m.name) +
              '<div class="adm-sheet-actions"><button class="btn ghost" type="button" data-x>Fermer</button></div>', function (b2) {
              $('[data-x]', b2).addEventListener('click', close);
            });
          }, function (err) { busy(go, false); toast(errText(err)); });
        });
      });
  };

  var payForm = function (m, back) {
    var cur = curOf(m);
    var curOpts = DATA.currencies.map(function (c) { return '<option value="' + c + '"' + (c === cur ? ' selected' : '') + '>' + c + '</option>'; }).join('');
    open('Paiement WhatsApp reçu',
      '<form class="adm-sheet-form" novalidate><p class="adm-who">' + avatar(m) + '<span><b>' + esc(m.name || '—') + '</b><small>' + esc(m.email || '') + '</small></span></p>' +
      '<div data-plans>' + planCards('plan', cur, 'month') + '</div>' +
      '<div class="adm-two"><label class="adm-field"><span>Monnaie</span><select name="currency">' + curOpts + '</select></label>' +
      '<label class="adm-field"><span>Montant reçu</span><input class="num" name="amount" type="number" min="0" step="any" inputmode="decimal" required></label></div>' +
      '<label class="adm-field"><span>Note (facultatif)</span><input name="note" maxlength="280" placeholder="Ex. : Orange Money, réf. 12345"></label>' +
      '<p class="note">Le Premium s’active tout de suite et s’ajoute au temps restant. Le reçu part par e-mail, et son parrain éventuel reçoit ses analyses.</p>' +
      '<div class="adm-sheet-actions"><button class="btn" type="submit" data-go></button><button class="btn ghost" type="button" data-back>Retour</button></div></form>',
      function (b) {
        var form = $('form', b);
        var go = $('[data-go]', b);
        var touched = false;
        var plan = function () { return (form.querySelector('input[name=plan]:checked') || {}).value; };
        var sync = function (e) {
          if (e && e.target === form.amount) touched = true;
          if (e && e.target === form.currency) {
            var keep = plan();
            $('[data-plans]', b).innerHTML = planCards('plan', form.currency.value, keep);
            touched = false;
          }
          if (!touched || (e && e.target && e.target.name === 'plan')) { var v = price(plan(), form.currency.value); form.amount.value = v != null ? v : ''; touched = false; }
          go.innerHTML = ic('card') + 'Enregistrer · ' + esc(pass(plan())) + (form.amount.value ? ' · ' + esc(cash(+form.amount.value, form.currency.value)) : '');
        };
        form.addEventListener('input', sync);
        form.addEventListener('change', sync);
        $('[data-back]', b).addEventListener('click', back);
        sync();
        form.addEventListener('submit', function (e) {
          e.preventDefault();
          var payload = { id: m.id, plan: plan(), currency: form.currency.value, amount: +form.amount.value, note: form.note.value.trim() };
          if (!(payload.amount > 0)) { toast(ERR.amount); form.amount.focus(); return; }
          var again = function () { payForm(m, back); };
          confirmIn('Confirmer le paiement', 'Enregistrer <b>' + esc(cash(payload.amount, payload.currency)) + '</b> reçus de <b>' + esc(m.name || m.email) +
            '</b> pour le <b>' + esc(pass(payload.plan)) + '</b> ?', 'Oui, enregistrer', false, function () {
            return api('manual_payment', payload).then(function (r) {
              refreshSoon();
              toast('Paiement enregistré · Premium jusqu’au ' + day(r.premium_until));
              showMember(m.id);
            });
          }, again);
        });
      });
  };

  var endPremium = function (m, back) {
    confirmIn('Arrêter le Premium', 'Le Premium de <b>' + esc(m.name || m.email) + '</b> (jusqu’au ' + esc(day(m.premium_until)) +
      ') s’arrête tout de suite. Aucun remboursement n’est fait ici.', 'Oui, arrêter', true, function () {
      return api('end_premium', { id: m.id }).then(function () { refreshSoon(); toast('Premium arrêté'); showMember(m.id); });
    }, back);
  };

  var rewardRow = function (r, withMember) {
    var el = doc.createElement('article');
    el.className = 'adm-item reward ' + r.kind;
    var st = RSTATUS[r.status] || [r.status, ''];
    var who = withMember && r.member ? esc(r.member.name || r.member.email || '') + ' · ' : '';
    el.innerHTML = '<span class="ai-ic">' + ic(r.kind === 'premium' ? 'crown' : 'zap') + '</span>' +
      '<div class="ai-main"><b>' + esc(giftLabel(r)) + '</b><small>' + who + esc(SOURCE[r.source] || r.source) + ' · ' + esc(day(r.created_at)) + '</small>' +
      (r.note ? '<small class="ai-note">« ' + esc(r.note) + ' »</small>' : '') + '<span class="ai-tags">' + pill(st) +
      (r.status === 'sent' && r.expires_at ? '<span class="adm-tag">expire le ' + esc(day(r.expires_at)) + '</span>' : '') + '</span></div>';
    var acts = doc.createElement('div');
    acts.className = 'ai-acts';
    if (r.source === 'gift' && (r.status === 'sent' || r.status === 'expired')) {
      var rs = doc.createElement('button');
      rs.type = 'button';
      rs.className = 'btn ghost small';
      rs.innerHTML = ic('refresh') + 'Renvoyer';
      rs.addEventListener('click', function () {
        busy(rs, true);
        api('resend_gift', { reward: r.id }).then(function (res) {
          busy(rs, false);
          refreshSoon();
          var name = r.member ? r.member.name : '';
          open('Cadeau renvoyé', '<ul class="adm-sent"><li class="' + (res.emailed ? 'ok' : 'no') + '">' + ic(res.emailed ? 'check' : 'x') +
            (res.emailed ? 'Nouvel e-mail envoyé (l’ancien lien ne marche plus)' : 'E-mail pas envoyé : partage le nouveau lien') + '</li></ul>' +
            linkBlock(res.link, name) + '<div class="adm-sheet-actions"><button class="btn ghost" type="button" data-x>Fermer</button></div>',
          function (b) { $('[data-x]', b).addEventListener('click', close); });
        }, function (e) { busy(rs, false); toast(errText(e)); });
      });
      acts.appendChild(rs);
    }
    if (r.status === 'sent' || r.status === 'available') {
      var cn = doc.createElement('button');
      cn.type = 'button';
      cn.className = 'btn ghost small danger-ink';
      cn.innerHTML = ic('x') + 'Annuler';
      cn.addEventListener('click', function () {
        var wasOpen = sheet.open;
        confirmIn('Annuler la récompense', 'Annuler <b>' + esc(giftLabel(r)) + '</b>' + (r.member ? ' de <b>' + esc(r.member.name || '') + '</b>' : '') +
          ' ? Elle disparaît de son onglet Récompenses.', 'Oui, annuler', true, function () {
          return api('cancel_reward', { reward: r.id }).then(function () {
            refreshSoon();
            toast('Récompense annulée');
            if (wasOpen && r.user_id) showMember(r.user_id); else { close(); Panes.rewards.reload(); }
          });
        }, wasOpen && r.user_id ? function () { showMember(r.user_id); } : null);
      });
      acts.appendChild(cn);
    }
    if (acts.children.length) el.appendChild(acts);
    return el;
  };
  var paymentRow = function (p, withMember) {
    var el = doc.createElement('article');
    el.className = 'adm-item pay';
    var who = withMember && p.member ? esc(p.member.name || p.member.email || '') + ' · ' : '';
    el.innerHTML = '<span class="ai-ic">' + ic('card') + '</span><div class="ai-main"><b>' + esc(pass(p.plan)) + ' · <span class="num">' + esc(cash(p.amount, p.currency)) + '</span></b>' +
      '<small>' + who + esc(PROVIDER[p.provider] || p.provider) + ' · ' + esc(dt(p.paid_at || p.created_at)) + '</small>' +
      (p.note ? '<small class="ai-note">' + esc(p.note) + '</small>' : '') + '<span class="ai-tags">' + pill(PSTATUS[p.status] || [p.status, '']) + '</span></div>';
    return el;
  };
  var emailRow = function (e, withMember) {
    var el = doc.createElement('article');
    el.className = 'adm-item mail';
    el.innerHTML = '<span class="ai-ic">' + ic('mail') + '</span><div class="ai-main"><b>' + esc(EMAIL[e.kind] || e.kind) + '</b><small>' +
      (withMember && e.member ? esc(e.member.name || e.member.email || '') + ' · ' : '') + esc(dt(e.created_at)) + '</small></div>';
    return el;
  };
  var logRow = function (l) {
    var el = doc.createElement('article');
    el.className = 'adm-item log';
    var d = l.detail || {};
    var bits = [];
    if (d.plan) bits.push(pass(d.plan));
    if (d.kind === 'analyses' && d.amount) bits.push(analyses(d.amount));
    if (d.amount && d.currency) bits.push(cash(d.amount, d.currency));
    if (d.title) bits.push('« ' + d.title + ' »');
    if (d.sent != null) bits.push(d.sent + ' téléphone(s)');
    if (d.emailed === false) bits.push('sans e-mail');
    el.innerHTML = '<span class="ai-ic">' + ic(l.action === 'manual_payment' ? 'card' : l.action === 'broadcast' ? 'bell' : l.action === 'settings' ? 'users' : 'gift') + '</span>' +
      '<div class="ai-main"><b>' + esc(ACTION[l.action] || l.action) + '</b><small>' + (l.member ? esc(l.member.name || l.member.email || '') + ' · ' : '') +
      esc(dt(l.created_at)) + '</small>' + (bits.length ? '<small class="ai-note">' + esc(bits.join(' · ')) + '</small>' : '') + '</div>';
    return el;
  };

  // Fiche d'un membre
  var showMember = function (id) {
    open('Fiche du membre', '<div class="adm-wait"><span class="sk sk-block" style="height: 120px"></span><span class="sk sk-block" style="height: 200px"></span></div>');
    api('member', { id: id }).then(function (r) {
      var m = r.member;
      var fr = r.friends || [];
      var facts = [
        ['Premium', premiumOn(m) ? 'jusqu’au ' + day(m.premium_until) : 'Gratuit'],
        ['Analyses offertes', String(m.bonus_analyses || 0)],
        ['Jours d’utilisation', (m.active_days || 0) + (m.last_seen ? ' · dernier : ' + day(m.last_seen) : '')],
        ['Inscrit le', day(m.created_at)],
        ['Code de parrainage', m.ref_code || '—'],
        ['Filleuls', String(fr.length)],
        ['Téléphones abonnés', String(r.devices || 0)],
        ['Langue · pays', (m.lang || '—').toUpperCase() + ' · ' + (m.country || '—')],
        ['E-mails d’actualité', m.email_news ? 'oui' : 'non']
      ];
      open(m.name || m.email || 'Membre',
        '<div class="adm-card-head">' + avatar(m) + '<div><b>' + esc(m.name || '—') + '</b><small>' + esc(m.email || '') + '</small></div></div>' +
        '<div class="adm-sheet-actions grid"><button class="btn" type="button" data-a="gift-premium">' + ic('crown') + 'Offrir le Premium</button>' +
        '<button class="btn ghost" type="button" data-a="gift-analyses">' + ic('zap') + 'Offrir des analyses</button>' +
        '<button class="btn ghost" type="button" data-a="pay">' + ic('card') + 'Paiement reçu</button>' +
        (premiumOn(m) ? '<button class="btn ghost danger-ink" type="button" data-a="end">' + ic('x') + 'Arrêter le Premium</button>' : '') + '</div>' +
        '<dl class="adm-facts">' + facts.map(function (f) { return '<div><dt>' + esc(f[0]) + '</dt><dd>' + esc(f[1]) + '</dd></div>'; }).join('') + '</dl>' +
        '<h3 class="adm-h">Récompenses</h3><div class="adm-list" data-l="rewards"></div>' +
        '<h3 class="adm-h">Paiements</h3><div class="adm-list" data-l="payments"></div>' +
        '<h3 class="adm-h">Filleuls</h3><div class="adm-list" data-l="friends"></div>' +
        '<h3 class="adm-h">E-mails reçus</h3><div class="adm-list" data-l="emails"></div>',
        function (b) {
          var back = function () { showMember(id); };
          $$('[data-a]', b).forEach(function (btn) {
            btn.addEventListener('click', function () {
              var a = btn.getAttribute('data-a');
              if (a === 'gift-premium') giftForm(m, 'premium', back);
              else if (a === 'gift-analyses') giftForm(m, 'analyses', back);
              else if (a === 'pay') payForm(m, back);
              else if (a === 'end') endPremium(m, back);
            });
          });
          var fill = function (key, rows, make) {
            var c = $('[data-l="' + key + '"]', b);
            if (!rows.length) { c.innerHTML = '<p class="adm-none">Rien pour l’instant.</p>'; return; }
            rows.forEach(function (x) { c.appendChild(make(x)); });
          };
          fill('rewards', (r.rewards || []).map(function (x) { return Object.assign({ user_id: id }, x); }), function (x) { return rewardRow(x, false); });
          fill('payments', r.payments || [], function (x) { return paymentRow(x, false); });
          fill('friends', fr, function (f) {
            var el = doc.createElement('article');
            el.className = 'adm-item friend';
            el.innerHTML = avatar(f) + '<div class="ai-main"><b>' + esc(f.name || '—') + '</b><small>Inscrit le ' + esc(day(f.created_at)) + ' · ' +
              (f.active_days || 0) + ' jour(s) d’utilisation' + (premiumOn(f) ? ' · Premium' : '') + '</small></div>';
            return el;
          });
          fill('emails', r.emails || [], function (x) { return emailRow(x, false); });
        });
    }, function (e) {
      open('Fiche du membre', '<p class="adm-none">' + esc(errText(e)) + '</p>');
    });
  };

  // =====================================================================================================
  // Rubriques
  // =====================================================================================================
  var listPane = function (o) {
    // Liste avec « Voir plus » : o.action, o.key (champ de la réponse), o.row, o.list, o.more, o.body()
    var offset = 0;
    var list = $(o.list);
    var more = $(o.more);
    var load = function (append) {
      if (!append) { offset = 0; list.innerHTML = '<div class="adm-wait"><span class="sk sk-block" style="height: 74px"></span><span class="sk sk-block" style="height: 74px"></span><span class="sk sk-block" style="height: 74px"></span></div>'; }
      busy(more, true);
      return api(o.action, Object.assign({ offset: offset }, o.body ? o.body() : {})).then(function (r) {
        busy(more, false);
        var rows = r[o.key] || [];
        if (!append) list.textContent = '';
        rows.forEach(function (x) { list.appendChild(o.row(x)); });
        offset += rows.length;
        if (!append && !rows.length) list.innerHTML = '<p class="adm-none">' + esc(o.empty || 'Rien pour l’instant.') + '</p>';
        more.hidden = rows.length < (o.page || 50) || (r.total != null && offset >= r.total);
        if (o.after) o.after(r, offset);
      }, function (e) { busy(more, false); list.innerHTML = '<p class="adm-none">' + esc(errText(e)) + '</p>'; });
    };
    more.addEventListener('click', function () { load(true); });
    return { reload: function () { return load(false); } };
  };
  var mFilter = 'all';
  var mQ = '';
  var Panes = {
    dash: { reload: function () { return api('stats').then(function (r) { dash(r.stats || {}); }, function (e) { $('#kpis').innerHTML = '<p class="adm-none">' + esc(errText(e)) + '</p>'; }); } },
    members: listPane({ action: 'members', key: 'members', list: '#m-list', more: '#m-more', page: 30, empty: 'Aucun membre trouvé.',
      body: function () { return { q: mQ, filter: mFilter, limit: 30 }; }, row: memberRow,
      after: function (r) { $('#m-count').textContent = num(r.total || 0) + (r.total > 1 ? ' membres' : ' membre'); } }),
    payments: listPane({ action: 'payments', key: 'payments', list: '#p-list', more: '#p-more', empty: 'Aucun paiement pour l’instant.',
      row: function (p) { return paymentRow(p, true); } }),
    rewards: listPane({ action: 'rewards', key: 'rewards', list: '#r-list', more: '#r-more', empty: 'Aucune récompense ici.',
      body: function () { return { status: rStatus, source: rSource }; }, row: function (r) { return rewardRow(r, true); } }),
    emails: listPane({ action: 'emails', key: 'emails', list: '#e-list', more: '#e-more', empty: 'Aucun e-mail envoyé pour l’instant.',
      row: function (e) { return emailRow(e, true); } }),
    log: listPane({ action: 'log', key: 'log', list: '#l-list', more: '#l-more', page: 60, empty: 'Rien de fait depuis l’administration pour l’instant.', row: logRow }),
    settings: { reload: function () { return loadSettings(); } }
  };
  var rStatus = '';
  var rSource = '';
  var loaded = {};
  // Après une action : la rubrique ouverte se recharge, les autres au prochain passage
  var refreshSoon = function () { loaded = {}; loaded[current] = Date.now(); Panes[current].reload(); };

  // Tableau de bord
  var STATS;
  var kpi = function (label, value, sub, go, tone) {
    return '<button type="button" class="kpi' + (tone ? ' ' + tone : '') + '"' + (go ? ' data-kpi="' + go + '"' : ' disabled') + '><small>' + esc(label) + '</small>' +
      '<b class="num">' + esc(value) + '</b>' + (sub ? '<span>' + esc(sub) + '</span>' : '') + '</button>';
  };
  var pct = function (a, b) { return b ? Math.round(100 * a / b) + ' %' : '—'; };
  var dash = function (s) {
    STATS = s;
    var k = $('#kpis');
    k.innerHTML =
      kpi('Membres', num(s.members), '+' + num(s.new_today) + ' aujourd’hui · +' + num(s.new_7d) + ' en 7 jours', 'members:all') +
      kpi('Actifs sur 7 jours', num(s.active_7d), pct(s.active_7d, s.members) + ' des membres', 'members:all') +
      kpi('Premium en cours', num(s.premium), pct(s.premium, s.members) + ' des membres', 'members:premium', 'gold') +
      kpi('Notifications activées', num(s.push), 'membres avec un téléphone abonné', null) +
      kpi('Parrainés sur 30 jours', num(s.referred_30d), 'nouveaux venus par un lien d’invitation', 'members:referred') +
      kpi('Paiements sur 30 jours', num(s.payments_30d), null, 'payments') +
      kpi('Cadeaux pas encore ouverts', num(s.gifts_pending), 'en attente du clic dans l’e-mail', 'rewards:sent') +
      kpi('Récompenses à activer', num(s.rewards_open), 'reçues, pas encore utilisées', 'rewards:available') +
      kpi('E-mails envoyés', num(s.emails_today), 'aujourd’hui · ' + num(s.emails_30d) + ' sur 30 jours', 'emails');
    chart(s.signups_14d || []);
    var rev = s.revenue_30d || {};
    var keys = Object.keys(rev);
    $('#money-rows').innerHTML = keys.length ? keys.map(function (c) {
      return '<div class="mr"><span>' + esc(c) + '</span><b class="num">' + esc(cash(rev[c], c)) + '</b></div>';
    }).join('') : '<p class="adm-none">Aucun paiement sur 30 jours.</p>';
    var dev = $('#bc-devices');
    if (dev) dev.textContent = 'Envoyée à tous les téléphones qui ont activé les notifications (' + num(s.push) + ' membre(s) aujourd’hui). Pas d’e-mail.';
  };
  $('#kpis').addEventListener('click', function (e) {
    var b = e.target.closest('[data-kpi]');
    if (!b) return;
    var p = b.getAttribute('data-kpi').split(':');
    if (p[0] === 'members' && p[1]) setPressed('[data-filter]', 'data-filter', mFilter = p[1]);
    if (p[0] === 'rewards') { setPressed('[data-rstatus]', 'data-rstatus', rStatus = p[1] || ''); setPressed('[data-rsource]', 'data-rsource', rSource = ''); }
    loaded[p[0]] = 0;
    show(p[0], true);
  });
  // Inscriptions sur 14 jours : barres fines, valeur au survol ou au toucher, tableau pour les lecteurs d'écran
  var chart = function (days) {
    var bars = $('#bars');
    var axis = $('#bars-axis');
    var max = Math.max.apply(null, days.map(function (d) { return d.n; }).concat([1]));
    var total = days.reduce(function (s, d) { return s + d.n; }, 0);
    $('#chart-total').textContent = num(total);
    var lab = function (d) { return fWd.format(new Date(d.d + 'T12:00:00')); };
    bars.innerHTML = days.map(function (d, i) {
      var h = d.n ? Math.max(4, Math.round(100 * d.n / max)) : 0;
      var show = d.n && (d.n === max || i === days.length - 1);
      return '<span class="bar' + (i === days.length - 1 ? ' today' : '') + '" tabindex="0" data-tip="' + esc(lab(d) + ' · ' + d.n + (d.n > 1 ? ' inscriptions' : ' inscription')) + '">' +
        '<i style="height:' + h + '%"></i>' + (show ? '<em class="num">' + d.n + '</em>' : '') + '</span>';
    }).join('') + '<span class="bar-tip" aria-hidden="true" hidden></span>';
    axis.innerHTML = days.map(function (d, i) {
      return '<span>' + (i === 0 || i === 7 || i === days.length - 1 ? esc(i === days.length - 1 ? 'auj.' : String(new Date(d.d + 'T12:00:00').getDate())) : '') + '</span>';
    }).join('');
    $('#bars-table tbody').innerHTML = days.map(function (d) { return '<tr><th>' + esc(lab(d)) + '</th><td>' + d.n + '</td></tr>'; }).join('');
    bars.setAttribute('aria-label', 'Inscriptions des 14 derniers jours : ' + total + ' au total, au plus ' + max + ' en un jour');
  };
  (function () {
    var bars = $('#bars');
    var tipAt = function (bar) {
      var tip = $('.bar-tip', bars);
      if (!tip) return;
      if (!bar) { tip.hidden = true; return; }
      tip.textContent = bar.getAttribute('data-tip');
      tip.hidden = false;
      var bx = bars.getBoundingClientRect();
      var r = bar.getBoundingClientRect();
      var x = r.left + r.width / 2 - bx.left;
      var w = tip.offsetWidth;
      tip.style.left = Math.max(0, Math.min(bx.width - w, x - w / 2)) + 'px';
    };
    bars.addEventListener('pointerover', function (e) { tipAt(e.target.closest('.bar')); });
    bars.addEventListener('pointerleave', function () { tipAt(null); });
    bars.addEventListener('focusin', function (e) { tipAt(e.target.closest('.bar')); });
    bars.addEventListener('focusout', function () { tipAt(null); });
  })();

  // Membres : recherche (au fil de la frappe) et filtres
  var setPressed = function (sel, attr, val) { $$(sel).forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute(attr) === val)); }); };
  var qT;
  $('#m-q').addEventListener('input', function (e) {
    clearTimeout(qT);
    qT = setTimeout(function () { mQ = e.target.value.trim(); Panes.members.reload(); }, 300);
  });
  $$('[data-filter]').forEach(function (b) {
    b.addEventListener('click', function () { mFilter = b.getAttribute('data-filter'); setPressed('[data-filter]', 'data-filter', mFilter); Panes.members.reload(); });
  });
  $$('[data-rstatus]').forEach(function (b) {
    b.addEventListener('click', function () { rStatus = b.getAttribute('data-rstatus'); setPressed('[data-rstatus]', 'data-rstatus', rStatus); Panes.rewards.reload(); });
  });
  $$('[data-rsource]').forEach(function (b) {
    b.addEventListener('click', function () { rSource = b.getAttribute('data-rsource'); setPressed('[data-rsource]', 'data-rsource', rSource); Panes.rewards.reload(); });
  });
  // Raccourcis du tableau de bord : choisir un membre d'abord
  $$('.adm-quick [data-go]').forEach(function (b) {
    b.addEventListener('click', function () {
      show('members', true);
      toast(b.getAttribute('data-then') === 'pay' ? 'Cherche le membre, puis ⋮ → « Paiement WhatsApp reçu »' : 'Cherche le membre, puis ⋮ → « Offrir le Premium »');
      setTimeout(function () { $('#m-q').focus(); }, 60);
    });
  });

  // E-mails : test
  $$('[data-email-test]').forEach(function (b) {
    b.addEventListener('click', function () {
      busy(b, true);
      api('email_test', { lang: b.getAttribute('data-email-test') }).then(function (r) {
        busy(b, false);
        toast(r && r.ok ? 'E-mail de test envoyé à ton adresse' : 'E-mail non envoyé : vérifie les réglages GMAIL_SCRIPT_URL et GMAIL_SCRIPT_SECRET');
      }, function (e) { busy(b, false); toast(errText(e)); });
    });
  });

  // Réglages : barème du parrainage, annonce, notification de test
  var refForm = $('#ref-form');
  $$('[data-plan-label]', refForm).forEach(function (s) { s.textContent = 'Pass ' + (DUR[s.getAttribute('data-plan-label')] || s.textContent); });
  var loadSettings = function () {
    return api('settings').then(function (r) {
      var v = r.referral || {};
      ['signup', 'active', 'active_days', 'welcome', 'monthly_cap'].forEach(function (k) { if (refForm[k]) refForm[k].value = v[k] != null ? v[k] : ''; });
      DATA.plans.forEach(function (p) { var f = refForm['buy_' + p]; if (f) f.value = (v.purchase || {})[p] != null ? v.purchase[p] : ''; });
    }, function (e) { toast(errText(e)); });
  };
  refForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var btn = $('button[type=submit]', refForm);
    var v = { purchase: {} };
    ['signup', 'active', 'active_days', 'welcome', 'monthly_cap'].forEach(function (k) { v[k] = +refForm[k].value; });
    DATA.plans.forEach(function (p) { v.purchase[p] = +refForm['buy_' + p].value; });
    busy(btn, true);
    api('settings_set', { referral: v }).then(function () { busy(btn, false); toast('Barème enregistré'); }, function (er) { busy(btn, false); toast(errText(er)); });
  });
  var bcForm = $('#bc-form');
  bcForm.addEventListener('submit', function (e) {
    e.preventDefault();
    var title = bcForm.title.value.trim();
    var body = bcForm.body.value.trim();
    if (!title || !body) { toast(ERR.text); return; }
    var n = STATS ? STATS.push : null;
    confirmIn('Envoyer l’annonce', 'Envoyer « <b>' + esc(title) + '</b> » ' + (n != null ? 'aux téléphones de <b>' + num(n) + '</b> membre(s)' : 'à tous les téléphones abonnés') +
      ' ? Une annonce ne se rattrape pas.', 'Oui, envoyer', false, function () {
      return api('broadcast', { title: title, body: body, url: bcForm.url.value }).then(function (r) {
        close();
        bcForm.reset();
        toast('Annonce envoyée à ' + num(r.sent) + ' téléphone(s)');
        refreshSoon();
      });
    });
  });
  $('#push-test').addEventListener('click', function () {
    var b = $('#push-test');
    busy(b, true);
    api('push_test').then(function (r) {
      busy(b, false);
      toast(r.sent ? 'Notification de test envoyée' : 'Aucun téléphone abonné sur ton compte : active les notifications dans Mon compte');
    }, function (e) { busy(b, false); toast(errText(e)); });
  });

  // ---------- Onglets (flèches du clavier, rubrique gardée dans l'adresse) ----------
  var tabs = $$('.adm-tabs [role=tab]');
  var current = 'dash';
  var show = function (key, focus) {
    if (!Panes[key]) key = 'dash';
    current = key;
    tabs.forEach(function (t) {
      var on = t.getAttribute('data-tab') === key;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    });
    $$('.adm-pane').forEach(function (p) { p.hidden = p.id !== 'pane-' + key; });
    try { history.replaceState(history.state, '', '#' + key); } catch (e) {}
    if (!loaded[key] || Date.now() - loaded[key] > 60e3) { loaded[key] = Date.now(); Panes[key].reload(); }
  };
  tabs.forEach(function (t, i) {
    t.addEventListener('click', function () { show(t.getAttribute('data-tab')); });
    t.addEventListener('keydown', function (e) {
      var j = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
      if (j === null) return;
      e.preventDefault();
      var n = tabs[(j + tabs.length) % tabs.length];
      n.focus();
      show(n.getAttribute('data-tab'));
    });
  });

  // ---------- Installer Probalis Office (Android, ordinateur) : l'appli a son propre nom et son icône dorée ----------
  var install = $('#adm-install');
  var prompt = null;
  win.addEventListener('beforeinstallprompt', function (e) { e.preventDefault(); prompt = e; install.hidden = false; });
  win.addEventListener('appinstalled', function () { prompt = null; install.hidden = true; toast('Probalis Office est installée'); });
  install.addEventListener('click', function () {
    if (!prompt) return;
    prompt.prompt();
    prompt.userChoice.then(function () { prompt = null; install.hidden = true; }, function () {});
  });

  // ---------- Accès : connecté avec Google, et dans la liste ADMIN_EMAILS ----------
  var signoutBtn = $('#adm-signout');
  var signout = function () {
    PB.acct.api.signOut().then(function () { location.replace('/office/'); });
  };
  signoutBtn.addEventListener('click', signout);
  $$('[data-signout]').forEach(function (b) { b.addEventListener('click', signout); });
  // Connexion Google : on revient directement dans Office (et non dans « Mon compte »)
  $('#adm-signin').addEventListener('click', function () {
    var b = this;
    b.disabled = true;
    PB.acct.api.signIn('/office/').catch(function () { b.disabled = false; toast('Connexion impossible, réessaie.'); });
  });
  var start = function () {
    box.dataset.state = 'in';
    signoutBtn.hidden = !!PB.acct.demo;
    show((location.hash || '').slice(1) || 'dash');
  };
  if (PB.acct.demo) { start(); return; }
  var q = PB.params();
  if (q.error) { PB.cleanUrl(); toast('Connexion annulée.'); }
  var returning = /[?&]code=/.test(location.search);
  if (!returning && !PB.acct.hasToken()) { box.dataset.state = 'out'; return; }
  // Retour de Google (?code=…) : la session s'ouvre d'abord, puis on demande au serveur si ce compte est admin
  (returning ? PB.acct.api.session().catch(function () {}).then(function () { PB.cleanUrl(); }) : Promise.resolve())
    .then(function () {
      if (!PB.acct.hasToken()) { box.dataset.state = 'out'; return; }
      return api('me').then(start, function (e) {
        var c = e && (e.code || e.message);
        if (c === 'auth') { box.dataset.state = 'out'; return; }
        box.dataset.state = 'denied';
        signoutBtn.hidden = false;
        if (c !== 'forbidden') $('#adm-denied-text').textContent = errText(e);
      });
    });
})();
