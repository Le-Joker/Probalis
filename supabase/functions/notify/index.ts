// Fonction « notify » : appelée une fois par jour par la tâche des e-mails (GitHub Actions), avec la clé secrète.
//  - notification « Les analyses du jour sont prêtes » aux téléphones abonnés (une fois par jour au plus) ;
//  - ménage : cadeaux non ouverts expirés, récompenses du parrainage pas encore annoncées.
import { json, preflight, readJson, rest, same, SUPABASE_URL } from "../_shared/http.ts";
import { notifyRewards, pushSubs } from "../_shared/notify.ts";

type Msg = { title: string; body: string; url?: string };

/** La clé reçue est-elle la clé secrète du projet ? (seule elle peut lire app_secrets) */
async function isServiceKey(k: string): Promise<boolean> {
  if (!k || k.length < 20) return false;
  const env = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
  if (env && same(k, env)) return true;
  const h: Record<string, string> = { apikey: k };
  if (k.startsWith("eyJ")) h.Authorization = `Bearer ${k}`;
  try {
    const r = await fetch(`${SUPABASE_URL}/rest/v1/app_secrets?select=key&limit=1`, { headers: h });
    await r.body?.cancel();
    return r.ok;
  } catch {
    return false;
  }
}

const clean = (m: unknown): Msg | null => {
  const o = (m ?? {}) as Record<string, unknown>;
  const title = String(o.title ?? "").slice(0, 80);
  const body = String(o.body ?? "").slice(0, 240);
  const url = String(o.url ?? "/");
  return title && body ? { title, body, url: url.startsWith("/") && !url.startsWith("//") ? url : "/" } : null;
};

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const bearer = (req.headers.get("Authorization") ?? "").replace(/^Bearer\s+/i, "");
  const key = req.headers.get("x-probalis-key") || bearer || req.headers.get("apikey") || "";
  if (!(await isServiceKey(key))) return json({ error: "auth" }, 401);
  const body = await readJson(req);
  if (body.action !== "daily") return json({ error: "action" }, 400);
  const out: Record<string, unknown> = {};
  try {
    const now = new Date().toISOString();
    // 1) Cadeaux jamais ouverts : expirés
    const expired = await rest<unknown[]>("PATCH", `rewards?status=eq.sent&expires_at=lt.${now}`, { status: "expired" },
      "return=representation");
    out.expired = expired.length;

    // 2) Récompenses pas encore annoncées (un envoi a pu échouer)
    const late = await rest<{ id: string }[]>("GET",
      `rewards?notified_at=is.null&source=neq.gift&created_at=lt.${new Date(Date.now() - 5 * 60_000).toISOString()}&select=id&limit=50`);
    if (late.length) await notifyRewards(late.map((r) => r.id));
    out.announced = late.length;

    // 3) Notification du jour, une seule fois par jour
    const fr = clean(body.messages?.fr);
    const en = clean(body.messages?.en);
    const day = typeof body.day === "string" && /^\d{4}-\d{2}-\d{2}$/.test(body.day) ? body.day : now.slice(0, 10);
    if (fr && en) {
      const mark = await rest<unknown[]>("POST", "app_secrets?on_conflict=key", [{ key: `daily_push_${day}`, value: { at: now } }],
        "resolution=ignore-duplicates,return=representation");
      if (!mark.length) {
        out.daily = "déjà envoyée aujourd'hui";
      } else {
        const off = new Set((await rest<{ id: string }[]>("GET", "profiles?push_daily=is.false&select=id&limit=100000")).map((p) => p.id));
        const subs = (await rest<{ id: number; user_id: string; endpoint: string; p256dh: string; auth: string; lang: string }[]>(
          "GET", "push_subs?select=id,user_id,endpoint,p256dh,auth,lang&limit=20000")).filter((s) => !off.has(s.user_id));
        out.daily = await pushSubs(subs, (l) => ({ ...(l === "en" ? en : fr), tag: "daily" }));
        // Les marques des jours passés ne servent plus
        await rest("DELETE", `app_secrets?key=like.daily_push_*&key=neq.daily_push_${day}`).catch(() => {});
      }
    }
    return json({ ok: true, ...out });
  } catch (e) {
    console.error(e);
    return json({ error: "server", ...out }, 500);
  }
});
