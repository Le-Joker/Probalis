// Fonction « member » : ce que fait un membre connecté, en dehors des paiements.
//   start       une fois par jour : note le jour d'utilisation (parrainage : récompense au 3e jour de l'ami) et,
//               pour un nouveau compte venu d'un lien d'invitation, le relie à son parrain
//   claim       lien de l'e-mail cadeau ouvert : le cadeau passe dans l'onglet Récompenses
//   activate    le membre active une récompense (Premium prolongé, ou analyses ajoutées)
//   push_key    clé publique des notifications (sans compte)
//   push_sub    enregistre ce téléphone pour les notifications ; push_unsub l'enlève ; push_test en envoie une
// Toutes les règles (une fois seulement, limites, compte de moins de 3 jours…) sont vérifiées dans la base.
import { getUser, json, lang, preflight, readJson, rest } from "../_shared/http.ts";
import { notifyPremiumOn, notifyRewards, pushUser, vapidKeys } from "../_shared/notify.ts";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const DAY = /^\d{4}-\d{2}-\d{2}$/;
// Seuls les vrais services de notification des navigateurs (Chrome/Android, Firefox, Safari/iPhone, Edge)
const PUSH_HOST = /^(fcm\.googleapis\.com|android\.googleapis\.com|updates\.push\.services\.mozilla\.com|[a-z0-9-]+\.push\.apple\.com|web\.push\.apple\.com|[a-z0-9.-]+\.notify\.windows\.com)$/;
const B64U = /^[A-Za-z0-9_-]+$/;
const MAX_DEVICES = 8;

/** Code d'erreur lisible renvoyé par les fonctions SQL (« raise exception 'other_account' »…). */
const sqlCode = (e: unknown) => {
  const m = /(other_account|bad_link|unknown|not_available|date invalide)/.exec(String(e));
  return m ? m[1].replace(" ", "_") : "server";
};

const ids = (rows: unknown): string[] => (Array.isArray(rows) ? rows.map((r) => (typeof r === "string" ? r : Object.values(r ?? {})[0])) : [])
  .filter((x): x is string => typeof x === "string" && UUID.test(x));

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const body = await readJson(req);
  const action = String(body.action ?? "");
  try {
    if (action === "push_key") return json({ key: (await vapidKeys()).publicKey });

    const user = await getUser(req);
    if (!user) return json({ error: "auth" }, 401);

    if (action === "start") {
      const fresh: string[] = [];
      const code = typeof body.code === "string" ? body.code.trim() : "";
      if (/^[A-Za-z0-9]{4,12}$/.test(code)) {
        fresh.push(...ids(await rest("POST", "rpc/referral_attach", { p_user: user.id, p_code: code })));
      }
      if (typeof body.day === "string" && DAY.test(body.day)) {
        fresh.push(...ids(await rest("POST", "rpc/activity_ping", { p_user: user.id, p_day: body.day })));
      }
      if (fresh.length) await notifyRewards(fresh);
      return json({ ok: true, rewards: fresh.length });
    }

    if (action === "claim") {
      if (!UUID.test(String(body.id)) || typeof body.token !== "string" || !B64U.test(body.token) || body.token.length > 100) {
        return json({ error: "bad_link" }, 400);
      }
      try {
        const rows = await rest<{ status: string; kind: string }[]>("POST", "rpc/claim_reward",
          { p_user: user.id, p_id: body.id, p_token: body.token });
        return json({ ok: true, ...(rows[0] ?? {}) });
      } catch (e) {
        return json({ error: sqlCode(e) }, 400);
      }
    }

    if (action === "activate") {
      if (!UUID.test(String(body.id))) return json({ error: "unknown" }, 400);
      let row: { kind: string; plan: string | null; premium_until: string | null; bonus_analyses: number; applied: boolean };
      try {
        row = (await rest<typeof row[]>("POST", "rpc/apply_reward", { p_user: user.id, p_id: body.id }))[0];
      } catch (e) {
        return json({ error: sqlCode(e) }, 400);
      }
      if (row?.applied && row.kind === "premium" && row.premium_until) {
        await notifyPremiumOn(user.id, { id: String(body.id), plan: row.plan }, row.premium_until).catch((e) => console.error(e));
      }
      return json({ ok: true, ...row });
    }

    if (action === "push_sub") {
      const s = body.sub ?? {};
      const endpoint = String(s.endpoint ?? "");
      const p256dh = String(s.keys?.p256dh ?? "");
      const auth = String(s.keys?.auth ?? "");
      let host = "";
      try {
        const u = new URL(endpoint);
        host = u.protocol === "https:" ? u.hostname : "";
      } catch { /* adresse invalide */ }
      if (!PUSH_HOST.test(host) || endpoint.length > 1000 || !B64U.test(p256dh) || p256dh.length > 200 ||
        !B64U.test(auth) || auth.length > 100) {
        return json({ error: "bad_subscription" }, 400);
      }
      await rest("POST", "push_subs?on_conflict=endpoint",
        [{ user_id: user.id, endpoint, p256dh, auth, lang: lang(body.lang), fails: 0 }], "resolution=merge-duplicates");
      // Au plus quelques appareils par compte : les plus anciens s'en vont
      const mine = await rest<{ id: number }[]>("GET", `push_subs?user_id=eq.${user.id}&select=id&order=created_at.desc`);
      const extra = mine.slice(MAX_DEVICES).map((r) => r.id);
      if (extra.length) await rest("DELETE", `push_subs?id=in.(${extra.join(",")})`);
      return json({ ok: true });
    }

    if (action === "push_unsub") {
      const endpoint = String(body.endpoint ?? "");
      if (endpoint) {
        await rest("DELETE", `push_subs?user_id=eq.${user.id}&endpoint=eq.${encodeURIComponent(endpoint)}`);
      }
      return json({ ok: true });
    }

    if (action === "push_test") {
      const sent = await pushUser(user.id, (l) => ({
        title: l === "fr" ? "Notifications activées" : "Notifications are on",
        body: l === "fr" ? "Tu recevras ici tes récompenses et l'annonce des analyses du jour." : "You'll get your rewards and today's analyses here.",
        url: `/${l}/compte.html`, tag: "test",
      }));
      return json({ ok: true, sent });
    }

    return json({ error: "action" }, 400);
  } catch (e) {
    console.error(action, e);
    return json({ error: "server" }, 500);
  }
});
