// Prévenir un membre : récompense du parrainage, cadeau de l'admin, Premium activé.
// Par e-mail (Gmail ou Resend, voir email.ts) et par notification sur ses téléphones abonnés (webpush.ts).
import { claim, firstName, fmtDate, sendEmail, unclaim } from "./email.ts";
import { rest, SITE_URL } from "./http.ts";
import { generateKeys, type Keys, type Message, send } from "./webpush.ts";

type L = "fr" | "en";
const lg = (v: unknown): L => (v === "en" ? "en" : "fr");

// ---------- Libellés ----------
const DURATION: Record<L, Record<string, string>> = {
  fr: { week: "7 jours", month: "30 jours", quarter: "3 mois", half: "6 mois", year: "1 an" },
  en: { week: "7-day", month: "30-day", quarter: "3-month", half: "6-month", year: "1-year" },
};

/** « Pass Premium 30 jours », « 5 analyses de match »… */
export function giftLabel(kind: string, plan: string | null, amount: number | null, l: L): string {
  if (kind === "premium") return l === "fr" ? `Pass Premium ${DURATION.fr[plan ?? ""] ?? ""}`.trim() : `${DURATION.en[plan ?? ""] ?? ""} Premium pass`.trim();
  const n = amount ?? 0;
  return l === "fr" ? `${n} analyse${n > 1 ? "s" : ""} de match` : `${n} match analys${n > 1 ? "es" : "is"}`;
}

// ---------- Notifications ----------
let keysCache: Keys | null = null;

/** Clés VAPID de Probalis : créées une seule fois, puis gardées dans app_secrets (jamais envoyées au téléphone,
 *  sauf la clé publique). */
export async function vapidKeys(): Promise<Keys> {
  if (keysCache) return keysCache;
  const read = async () => (await rest<{ value: Keys }[]>("GET", "app_secrets?key=eq.vapid&select=value"))[0]?.value ?? null;
  let k = await read();
  if (!k) {
    // Deux appels en même temps : la première clé écrite gagne, l'autre est ignorée
    await rest("POST", "app_secrets?on_conflict=key", [{ key: "vapid", value: await generateKeys() }],
      "resolution=ignore-duplicates");
    k = await read();
  }
  if (!k) throw new Error("clés de notification introuvables");
  return (keysCache = k);
}

type Sub = { id: number; endpoint: string; p256dh: string; auth: string; lang: string };

/** Envoie à une liste d'abonnements ; efface ceux qui n'existent plus. Renvoie le nombre de notifications parties. */
export async function pushSubs(subs: Sub[], msg: (l: L) => Message): Promise<number> {
  if (!subs.length) return 0;
  const keys = await vapidKeys();
  const subject = SITE_URL || "https://probalis.pages.dev";
  const ok: number[] = [];
  const gone: number[] = [];
  for (let i = 0; i < subs.length; i += 25) {
    const chunk = subs.slice(i, i + 25);
    const res = await Promise.all(chunk.map((s) => send(s, { ...msg(lg(s.lang)), lang: lg(s.lang) }, keys, subject)));
    res.forEach((r, j) => (r.ok ? ok : r.gone ? gone : []).push(chunk[j].id));
  }
  if (gone.length) await rest("DELETE", `push_subs?id=in.(${gone.join(",")})`).catch(() => {});
  if (ok.length) {
    await rest("PATCH", `push_subs?id=in.(${ok.join(",")})`, { last_ok: new Date().toISOString(), fails: 0 }).catch(() => {});
  }
  return ok.length;
}

export async function pushUser(userId: string, msg: (l: L) => Message): Promise<number> {
  const subs = await rest<Sub[]>("GET", `push_subs?user_id=eq.${userId}&select=id,endpoint,p256dh,auth,lang`);
  return pushSubs(subs, msg);
}

// ---------- Récompenses du parrainage ----------
type Reward = {
  id: string; user_id: string; kind: string; plan: string | null; days: number | null; amount: number | null;
  source: string; ref: string; note: string | null; status: string; notified_at: string | null; expires_at: string | null;
};
type Person = { id: string; email: string | null; name: string | null; lang: string; ref_code: string };

async function person(id: string): Promise<Person | null> {
  if (!/^[0-9a-f-]{36}$/i.test(id)) return null;
  const rows = await rest<Person[]>("GET", `profiles?id=eq.${id}&select=id,email,name,lang,ref_code`);
  return rows[0] ?? null;
}

const friendName = (p: Person | null, l: L) => (p ? firstName(p.name, p.email ?? "") : l === "fr" ? "Un ami" : "A friend");

/** Pourquoi le parrain reçoit ces analyses (phrase de l'e-mail et de la notification). */
async function why(r: Reward, l: L): Promise<string> {
  if (r.source === "referral_purchase") {
    const pay = (await rest<{ user_id: string | null; plan: string }[]>(
      "GET", `payments?id=eq.${r.ref}&select=user_id,plan`).catch(() => []))[0];
    const f = friendName(pay?.user_id ? await person(pay.user_id) : null, l);
    const pass = giftLabel("premium", pay?.plan ?? null, null, l);
    return l === "fr" ? `${f} vient de prendre un ${pass}, grâce à ton invitation.` : `${f} just got a ${pass}, thanks to your invitation.`;
  }
  const f = friendName(await person(r.ref), l);
  if (r.source === "referral_active") {
    return l === "fr" ? `${f} a utilisé Probalis plusieurs jours, grâce à ton invitation.` : `${f} has used Probalis on several days, thanks to your invitation.`;
  }
  return l === "fr" ? `${f} vient de s'inscrire sur Probalis avec ton lien.` : `${f} just signed up to Probalis with your link.`;
}

/** Annonce des récompenses toutes neuves (une seule fois chacune). Ne lève jamais d'erreur. */
export async function notifyRewards(ids: string[]): Promise<void> {
  const list = ids.filter((id) => /^[0-9a-f-]{36}$/i.test(id));
  if (!list.length) return;
  const rows = await rest<Reward[]>("GET", `rewards?id=in.(${list.join(",")})&notified_at=is.null&select=*`).catch(() => []);
  for (const r of rows) {
    try {
      // Réserve l'annonce : un autre appel en même temps ne la refera pas
      const took = await rest<unknown[]>("PATCH", `rewards?id=eq.${r.id}&notified_at=is.null`,
        { notified_at: new Date().toISOString() }, "return=representation");
      if (!took?.length) continue;
      const p = await person(r.user_id);
      if (!p) continue;
      const l = lg(p.lang);
      const n = r.amount ?? 0;
      if (r.source === "welcome_bonus") {
        await pushUser(p.id, (x) => ({
          title: x === "fr" ? `Bienvenue : +${n} analyses offertes` : `Welcome: +${n} free analyses`,
          body: x === "fr" ? "Ton ami t'a invité : elles t'attendent dans Récompenses." : "Your friend invited you: they're waiting in Rewards.",
          url: `/${x}/recompenses.html`, tag: "reward",
        }));
        continue;
      }
      const reason = await why(r, l);
      await pushUser(p.id, (x) => ({
        title: x === "fr" ? `+${n} analyses offertes` : `+${n} free analyses`,
        body: x === l ? reason : (x === "fr" ? "Grâce à ton invitation. Elles t'attendent dans Récompenses." : "Thanks to your invitation. They're waiting in Rewards."),
        url: `/${x}/recompenses.html`, tag: "reward",
      })).catch((e) => console.error("notification", e));
      if (!p.email || !(await claim(p.id, "reward", r.id))) continue;
      const ok = await sendEmail("reward", l, p.email, {
        name: firstName(p.name, p.email), amount: String(n), why: reason, invite_url: `${SITE_URL}/i/${p.ref_code}`,
      }, `reward-${r.id}`);
      if (!ok) await unclaim(p.id, "reward", r.id);
    } catch (e) {
      console.error("annonce de la récompense", r.id, e);
    }
  }
}

// ---------- Cadeau de l'admin ----------
/** E-mail « Un cadeau t'attend » avec le lien d'activation, et notification. Renvoie le lien (pour l'admin). */
export async function sendGift(r: Reward, token: string): Promise<{ url: string; emailed: boolean; pushed: number }> {
  const p = await person(r.user_id);
  const l = lg(p?.lang);
  const url = `${SITE_URL}/${l}/recompenses.html?r=${r.id}&t=${token}`;
  if (!p) return { url, emailed: false, pushed: 0 };
  const gift = giftLabel(r.kind, r.plan, r.amount, l);
  const pushed = await pushUser(p.id, (x) => ({
    title: x === "fr" ? "Un cadeau t'attend sur Probalis" : "A gift is waiting for you on Probalis",
    body: `${giftLabel(r.kind, r.plan, r.amount, x)}. ${x === "fr" ? "Touche pour l'activer." : "Tap to activate it."}`,
    url: `/${l}/recompenses.html?r=${r.id}&t=${token}`, tag: "gift",
  })).catch(() => 0);
  let emailed = false;
  if (p.email) {
    const note_html = noteHtml(r.note);
    emailed = await sendEmail("gift", l, p.email, {
      name: firstName(p.name, p.email), gift, note: r.note ?? "", note_html, claim_url: url,
      expires: r.expires_at ? fmtDate(r.expires_at, l) : "",
    }, `gift-${r.id}-${token.slice(0, 8)}`);
  }
  return { url, emailed, pushed };
}

const ESC: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" };

/** Petit mot de l'admin (même rendu que note_html en Python). */
function noteHtml(note: string | null): string {
  const n = (note ?? "").trim();
  if (!n) return "";
  return '<p style="margin:0 0 14px;padding:12px 14px;background:#F0FDF4;border-left:3px solid #22C55E;' +
    `border-radius:8px;font-style:italic;">« ${n.replace(/[&<>"']/g, (c) => ESC[c])} »</p>`;
}

/** Après l'activation d'un Premium offert : e-mail « Premium activé » et notification. */
export async function notifyPremiumOn(userId: string, r: { id: string; plan: string | null }, until: string): Promise<void> {
  const p = await person(userId);
  if (!p) return;
  const l = lg(p.lang);
  await pushUser(p.id, (x) => ({
    title: x === "fr" ? "Ton Premium est activé" : "Your Premium is on",
    body: (x === "fr" ? "Toutes les analyses sont ouvertes jusqu'au " : "Every analysis is open until ") + fmtDate(until, x) + ".",
    url: `/${x}/`, tag: "premium",
  })).catch(() => 0);
  if (!p.email || !(await claim(p.id, "premium_on", r.id))) return;
  const ok = await sendEmail("premium_on", l, p.email, {
    name: firstName(p.name, p.email), gift: giftLabel("premium", r.plan, null, l), until: fmtDate(until, l),
  }, `premium-on-${r.id}`);
  if (!ok) await unclaim(p.id, "premium_on", r.id);
}
