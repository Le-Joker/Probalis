/**
 * Probalis : envoi des e-mails par Gmail, avec Google Apps Script (gratuit, environ 100 e-mails par jour).
 *
 * À installer une seule fois, depuis le compte Gmail qui enverra les e-mails (guide pas à pas :
 * docs/07-recompenses-admin-notifications.md, partie « E-mails par Gmail ») :
 *  1. script.google.com > Nouveau projet > effacer le contenu et coller tout ce fichier > Enregistrer.
 *  2. Paramètres du projet (roue dentée) > Propriétés du script > Ajouter : nom SECRET, valeur = le long mot de passe
 *     inventé pour Probalis (au moins 24 caractères). Le même mot va dans le secret GMAIL_SCRIPT_SECRET.
 *  3. Exécuter > testEnvoi (une fois) : Google demande l'autorisation d'envoyer des e-mails en ton nom ; tu reçois un test.
 *  4. Déployer > Nouveau déploiement > Type : Application Web. Exécuter en tant que : Moi. Qui a accès : Tout le monde.
 *     L'adresse qui se termine par /exec va dans le secret GMAIL_SCRIPT_URL.
 *
 * Sécurité : sans le mot SECRET, le programme refuse tout. Il n'envoie qu'aux adresses reçues, au plus 50 par appel,
 * et s'arrête quand le quota du jour de Gmail est atteint. Il ne lit pas ta boîte mail.
 */
var MAX_PER_CALL = 50;

function doPost(e) {
  var out = { ok: false, sent: 0 };
  try {
    var req = JSON.parse(e.postData.contents);
    var secret = PropertiesService.getScriptProperties().getProperty('SECRET');
    if (!secret || secret.length < 24 || typeof req.secret !== 'string' || req.secret !== secret) {
      return reply({ ok: false, error: 'secret' });
    }
    var msgs = (req.messages || []).slice(0, MAX_PER_CALL);
    var results = [];
    for (var i = 0; i < msgs.length; i++) {
      var m = msgs[i];
      if (!valid(m)) { results.push(false); continue; }
      if (MailApp.getRemainingDailyQuota() < 1) { results.push(false); out.error = 'quota'; continue; }
      try {
        var opt = { to: m.to, subject: String(m.subject), body: String(m.text || ''), htmlBody: String(m.html), name: 'Probalis' };
        if (m.replyTo && valid({ to: m.replyTo, subject: 'x', html: 'x' })) opt.replyTo = m.replyTo;
        MailApp.sendEmail(opt);
        results.push(true);
        out.sent++;
      } catch (err) {
        results.push(false);
        out.error = String(err).slice(0, 200);
      }
    }
    out.ok = true;
    out.results = results;
    out.remaining = MailApp.getRemainingDailyQuota();
  } catch (err) {
    out.error = 'bad_request';
  }
  return reply(out);
}

function valid(m) {
  return !!m && typeof m.to === 'string' && /^[^\s@<>,;"]+@[^\s@<>,;"]+\.[^\s@<>,;"]+$/.test(m.to) &&
    !!m.subject && String(m.subject).length < 300 && !!m.html;
}

function reply(o) {
  return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON);
}

function doGet() {
  return reply({ ok: true });
}

// Test : envoie un e-mail à toi-même (menu Exécuter > testEnvoi). Sert aussi à donner l'autorisation d'envoyer.
function testEnvoi() {
  MailApp.sendEmail({ to: Session.getActiveUser().getEmail(), subject: 'Probalis : test d\'envoi', body: 'Ça marche ! Quota restant aujourd\'hui : ' + MailApp.getRemainingDailyQuota(), name: 'Probalis' });
}
