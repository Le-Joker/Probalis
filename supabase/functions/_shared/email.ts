// E-mails envoyés par les fonctions (bienvenue, reçu, cadeau, récompense, Premium activé).
// Deux façons d'envoyer, selon les secrets enregistrés dans Supabase :
//  - Gmail, par un petit programme Google Apps Script (GMAIL_SCRIPT_URL + GMAIL_SCRIPT_SECRET) : pour démarrer
//    sans nom de domaine (environ 100 e-mails par jour) ;
//  - Resend (RESEND_API_KEY + EMAIL_FROM), quand Probalis aura son nom de domaine.
// Gmail est utilisé s'il est configuré.
// Les modèles viennent de emails.json, généré par « python -m probalis.site.emails generate » :
// {{nom}} est remplacé par un texte protégé, {{{nom}}} par du HTML préparé par notre code (même règle qu'en Python).
import templates from "./emails.json" with { type: "json" };
import { rest, SITE_URL } from "./http.ts";

type Kind = keyof typeof templates;
const VAR = /\{\{\{(\w+)\}\}\}|\{\{(\w+)\}\}/g;
const ESC: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" };
const esc = (s: string) => s.replace(/[&<>"']/g, (c) => ESC[c]);

export function fill(tpl: string, values: Record<string, unknown>, asHtml = true): string {
  const out = tpl.replace(VAR, (_m, raw, key) => {
    if (raw) return String(values[raw] ?? "");
    const v = String(values[key] ?? "");
    return asHtml ? esc(v) : v;
  });
  return asHtml ? out : out.replace(/\n{3,}/g, "\n\n");
}

export function links(site: string, lang: string): Record<string, string> {
  return {
    site_url: site,
    home_url: `${site}/${lang}/`,
    account_url: `${site}/${lang}/compte.html`,
    premium_url: `${site}/${lang}/premium.html`,
    responsible_url: `${site}/${lang}/jeu-responsable.html`,
    rewards_url: `${site}/${lang}/recompenses.html`,
  };
}

export const firstName = (name: string | null | undefined, email: string) =>
  (name ?? "").trim().split(" ")[0] || email.split("@")[0];

export const fmtDate = (iso: string, lang: string) =>
  new Intl.DateTimeFormat(lang === "en" ? "en-GB" : "fr-FR", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" })
    .format(new Date(iso));

/** Note l'envoi dans email_log ; renvoie false s'il avait déjà été fait (jamais deux fois le même e-mail). */
export async function claim(userId: string, kind: string, ref = ""): Promise<boolean> {
  const rows = await rest<unknown[]>("POST", "email_log?on_conflict=user_id,kind,ref", [{ user_id: userId, kind, ref }],
    "resolution=ignore-duplicates,return=representation");
  return Array.isArray(rows) && rows.length > 0;
}

export async function unclaim(userId: string, kind: string, ref = ""): Promise<void> {
  const q = new URLSearchParams({ user_id: `eq.${userId}`, kind: `eq.${kind}`, ref: `eq.${ref}` });
  await rest("DELETE", `email_log?${q}`).catch(() => {});
}

export const gmailConfigured = () => !!(Deno.env.get("GMAIL_SCRIPT_URL") && Deno.env.get("GMAIL_SCRIPT_SECRET"));
export const resendConfigured = () => !!(Deno.env.get("RESEND_API_KEY") && Deno.env.get("EMAIL_FROM"));
/** Un moyen d'envoi est-il configuré ? (sinon les fonctions ne réessaient pas : rien ne partira) */
export const emailConfigured = () => !!SITE_URL && (gmailConfigured() || resendConfigured());

type Mail = { to: string; subject: string; html: string; text: string };

async function viaGmail(mail: Mail): Promise<boolean> {
  const reply = Deno.env.get("CONTACT_EMAIL");
  try {
    const r = await fetch(Deno.env.get("GMAIL_SCRIPT_URL")!, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ secret: Deno.env.get("GMAIL_SCRIPT_SECRET"), messages: [{ ...mail, replyTo: reply || undefined }] }),
      redirect: "follow",
    });
    const out = await r.json().catch(() => null);
    if (!r.ok || !out?.ok || out.sent !== 1) {
      console.error("Gmail (Apps Script) a refusé l'e-mail", r.status, JSON.stringify(out)?.slice(0, 300));
      return false;
    }
    return true;
  } catch (e) {
    console.error("Gmail (Apps Script) injoignable", e);
    return false;
  }
}

async function viaResend(mail: Mail, idempotencyKey: string): Promise<boolean> {
  const body: Record<string, unknown> = { from: Deno.env.get("EMAIL_FROM"), to: [mail.to], subject: mail.subject,
    html: mail.html, text: mail.text };
  const reply = Deno.env.get("CONTACT_EMAIL");
  if (reply) body.reply_to = reply;
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${Deno.env.get("RESEND_API_KEY")}`, "Content-Type": "application/json",
      "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(body),
  });
  if (!r.ok) console.error("Resend a refusé l'e-mail", r.status, await r.text());
  return r.ok;
}

export async function sendEmail(kind: Kind, lang: string, to: string, values: Record<string, unknown>,
  idempotencyKey: string): Promise<boolean> {
  if (!emailConfigured()) {
    console.log("E-mails non configurés (Gmail ou Resend, et SITE_URL) : rien n'est envoyé.");
    return false;
  }
  const byLang = templates[kind] as Record<string, { subject: string; html: string; text: string }>;
  const t = byLang[lang] ?? byLang.fr;
  const v = { ...links(SITE_URL, lang), ...values };
  const mail: Mail = { to, subject: fill(t.subject, v, false), html: fill(t.html, v), text: fill(t.text, v, false) };
  return gmailConfigured() ? await viaGmail(mail) : await viaResend(mail, idempotencyKey);
}
