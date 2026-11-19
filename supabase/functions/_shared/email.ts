// E-mails envoyés par les fonctions (bienvenue, reçu d'achat) via Resend.
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

export async function sendEmail(kind: Kind, lang: string, to: string, values: Record<string, unknown>,
  idempotencyKey: string): Promise<boolean> {
  const key = Deno.env.get("RESEND_API_KEY");
  const from = Deno.env.get("EMAIL_FROM");
  if (!key || !from || !SITE_URL) {
    console.log("E-mails non configurés (RESEND_API_KEY, EMAIL_FROM ou SITE_URL manquant) : rien n'est envoyé.");
    return false;
  }
  const byLang = templates[kind] as Record<string, { subject: string; html: string; text: string }>;
  const t = byLang[lang] ?? byLang.fr;
  const v = { ...links(SITE_URL, lang), ...values };
  const body: Record<string, unknown> = {
    from,
    to: [to],
    subject: fill(t.subject, v, false),
    html: fill(t.html, v),
    text: fill(t.text, v, false),
  };
  const reply = Deno.env.get("CONTACT_EMAIL");
  if (reply) body.reply_to = reply;
  const r = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json", "Idempotency-Key": idempotencyKey },
    body: JSON.stringify(body),
  });
  if (!r.ok) console.error("Resend a refusé l'e-mail", kind, r.status, await r.text());
  return r.ok;
}
