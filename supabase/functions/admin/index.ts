// Fonction « admin » : tout ce que fait l'administrateur depuis la page /admin/ du site.
// Réservée aux adresses du secret ADMIN_EMAILS (séparées par des virgules), vérifiées à chaque appel avec le jeton
// de connexion Google. Chaque action qui change quelque chose est notée dans admin_log.
import { CURRENCIES, finalize, PLANS } from "../_shared/payments.ts";
import { sendEmail } from "../_shared/email.ts";
import { getUser, json, preflight, readJson, rest, type User } from "../_shared/http.ts";
import { giftLabel, pushSubs, pushUser, sendGift } from "../_shared/notify.ts";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const GIFT_DAYS = 30; // un cadeau non ouvert expire au bout de 30 jours

function admins(): string[] {
  return (Deno.env.get("ADMIN_EMAILS") ?? "").split(",").map((s) => s.trim().toLowerCase()).filter(Boolean);
}

async function log(admin: User, action: string, target: string | null, detail: Record<string, unknown> = {}) {
  await rest("POST", "admin_log", [{ admin_id: admin.id, action, target, detail }]).catch((e) => console.error("journal", e));
}

function token(): string {
  const b = crypto.getRandomValues(new Uint8Array(24));
  return btoa(String.fromCharCode(...b)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

async function sha256Hex(s: string): Promise<string> {
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(d)).map((x) => x.toString(16).padStart(2, "0")).join("");
}

const int = (v: unknown, min: number, max: number, dflt: number) => {
  const n = Math.floor(Number(v));
  return Number.isFinite(n) ? Math.min(max, Math.max(min, n)) : dflt;
};
const text = (v: unknown, max: number) => String(v ?? "").trim().slice(0, max);
const enc = encodeURIComponent;

type RewardRow = {
  id: string; user_id: string; kind: string; plan: string | null; days: number | null; amount: number | null;
  source: string; ref: string; note: string | null; status: string; notified_at: string | null; expires_at: string | null;
};

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const user = await getUser(req);
  if (!user) return json({ error: "auth" }, 401);
  const list = admins();
  if (!list.length || !user.email || !list.includes(user.email.toLowerCase())) return json({ error: "forbidden" }, 403);
  const b = await readJson(req);
  const action = String(b.action ?? "");
  try {
    switch (action) {
      case "me": {
        // Le profil de l'admin est marqué (l'appli affiche alors le lien « Administration » dans Mon compte)
        await rest("PATCH", `profiles?id=eq.${user.id}&role=neq.admin`, { role: "admin" }).catch(() => {});
        return json({ ok: true, admin: true });
      }

      case "stats":
        return json({ ok: true, stats: await rest("POST", "rpc/admin_stats", {}) });

      case "members": {
        const filter = ["all", "premium", "free", "referred"].includes(String(b.filter)) ? String(b.filter) : "all";
        const rows = await rest<Record<string, unknown>[]>("POST", "rpc/admin_members", {
          p_q: text(b.q, 80), p_filter: filter, p_limit: int(b.limit, 1, 100, 30), p_offset: int(b.offset, 0, 1e6, 0),
        });
        return json({ ok: true, members: rows, total: rows[0]?.total ?? 0 });
      }

      case "member": {
        const id = String(b.id ?? "");
        if (!UUID.test(id)) return json({ error: "id" }, 400);
        const [profile, rewards, payments, friends, devices, emails] = await Promise.all([
          rest<Record<string, unknown>[]>("GET", `profiles?id=eq.${id}&select=id,email,name,avatar_url,country,lang,premium_until,` +
            "bonus_analyses,extra_matches,created_at,last_seen,active_days,ref_code,referred_by,role,email_news,email_reminders,push_daily,free_day,free_match"),
          rest("GET", `rewards?user_id=eq.${id}&select=id,kind,plan,days,amount,source,note,status,created_at,expires_at,claimed_at,used_at&order=created_at.desc&limit=40`),
          rest("GET", `payments?user_id=eq.${id}&select=id,provider,plan,days,currency,amount,status,created_at,paid_at,note&order=created_at.desc&limit=40`),
          rest("GET", `profiles?referred_by=eq.${id}&select=id,name,created_at,active_days,premium_until&order=created_at.desc&limit=100`),
          rest<unknown[]>("GET", `push_subs?user_id=eq.${id}&select=id`),
          rest("GET", `email_log?user_id=eq.${id}&select=kind,ref,created_at&order=created_at.desc&limit=30`),
        ]);
        if (!profile[0]) return json({ error: "unknown" }, 404);
        return json({ ok: true, member: profile[0], rewards, payments, friends, devices: devices.length, emails });
      }

      case "gift": {
        // Cadeau : Premium (une des 5 formules) ou analyses de match. Le membre reçoit un e-mail avec un lien.
        const id = String(b.id ?? "");
        if (!UUID.test(id)) return json({ error: "id" }, 400);
        const kind = b.kind === "analyses" ? "analyses" : "premium";
        const row: Record<string, unknown> = { user_id: id, kind, source: "gift", status: "sent", created_by: user.id,
          note: text(b.note, 280) || null, expires_at: new Date(Date.now() + GIFT_DAYS * 86400_000).toISOString() };
        if (kind === "premium") {
          const plan = String(b.plan ?? "");
          if (!Object.hasOwn(PLANS, plan)) return json({ error: "plan" }, 400);
          row.plan = plan;
          row.days = PLANS[plan].days;
        } else {
          row.amount = int(b.amount, 1, 100, 0);
          if (!row.amount) return json({ error: "amount" }, 400);
        }
        const tok = token();
        row.claim_hash = await sha256Hex(tok);
        const r = (await rest<RewardRow[]>("POST", "rewards", [row], "return=representation"))[0];
        const sent = await sendGift(r, tok);
        await log(user, "gift", id, { reward: r.id, kind, plan: row.plan ?? null, amount: row.amount ?? null, emailed: sent.emailed });
        return json({ ok: true, reward: r.id, link: sent.url, emailed: sent.emailed, pushed: sent.pushed,
          label: giftLabel(kind, (row.plan as string) ?? null, (row.amount as number) ?? null, "fr") });
      }

      case "resend_gift": {
        const rid = String(b.reward ?? "");
        if (!UUID.test(rid)) return json({ error: "id" }, 400);
        const tok = token();
        const rows = await rest<RewardRow[]>("PATCH", `rewards?id=eq.${rid}&source=eq.gift&status=in.(sent,expired)`, {
          status: "sent", claim_hash: await sha256Hex(tok), expires_at: new Date(Date.now() + GIFT_DAYS * 86400_000).toISOString(),
        }, "return=representation");
        if (!rows[0]) return json({ error: "not_resendable" }, 400);
        const sent = await sendGift(rows[0], tok);
        await log(user, "resend_gift", rows[0].user_id, { reward: rid, emailed: sent.emailed });
        return json({ ok: true, link: sent.url, emailed: sent.emailed, pushed: sent.pushed });
      }

      case "cancel_reward": {
        const rid = String(b.reward ?? "");
        if (!UUID.test(rid)) return json({ error: "id" }, 400);
        const rows = await rest<RewardRow[]>("PATCH", `rewards?id=eq.${rid}&status=in.(sent,available)`,
          { status: "cancelled", claim_hash: null }, "return=representation");
        if (!rows[0]) return json({ error: "not_cancellable" }, 400);
        await log(user, "cancel_reward", rows[0].user_id, { reward: rid });
        return json({ ok: true });
      }

      case "manual_payment": {
        // Paiement reçu sur WhatsApp : l'admin l'enregistre, le Premium s'active, le reçu part, le parrain est récompensé
        const id = String(b.id ?? "");
        const plan = String(b.plan ?? "");
        const currency = String(b.currency ?? "").toUpperCase();
        if (!UUID.test(id)) return json({ error: "id" }, 400);
        if (!Object.hasOwn(PLANS, plan)) return json({ error: "plan" }, 400);
        if (!CURRENCIES[currency]) return json({ error: "currency" }, 400);
        const amount = Number(b.amount ?? (CURRENCIES[currency] as Record<string, unknown>)[plan]);
        if (!(amount > 0 && amount < 1e9)) return json({ error: "amount" }, 400);
        const prof = (await rest<{ lang: string; country: string | null }[]>("GET", `profiles?id=eq.${id}&select=lang,country`))[0];
        if (!prof) return json({ error: "unknown" }, 404);
        const pay = (await rest<{ id: string }[]>("POST", "payments", [{
          user_id: id, provider: "manual", plan, days: PLANS[plan].days, currency, amount, country: prof.country,
          lang: prof.lang === "en" ? "en" : "fr", status: "pending", created_by: user.id, note: text(b.note, 280) || null,
        }], "return=representation"))[0];
        const done = await finalize(pay.id, `manual-${pay.id.slice(0, 8)}`);
        await log(user, "manual_payment", id, { payment: pay.id, plan, currency, amount });
        return json({ ok: true, payment: pay.id, premium_until: done?.premium_until ?? null });
      }

      case "end_premium": {
        const id = String(b.id ?? "");
        if (!UUID.test(id)) return json({ error: "id" }, 400);
        const rows = await rest<{ premium_until: string | null }[]>("GET", `profiles?id=eq.${id}&select=premium_until`);
        if (!rows[0]) return json({ error: "unknown" }, 404);
        await rest("PATCH", `profiles?id=eq.${id}`, { premium_until: new Date().toISOString() });
        await log(user, "end_premium", id, { was: rows[0].premium_until });
        return json({ ok: true });
      }

      case "rewards": {
        const status = ["sent", "available", "used", "expired", "cancelled"].includes(String(b.status)) ? `&status=eq.${b.status}` : "";
        const source = b.source === "gift" ? "&source=eq.gift" : b.source === "referral" ? "&source=neq.gift" : "";
        const rows = await rest<(RewardRow & { created_at: string })[]>("GET",
          `rewards?select=id,user_id,kind,plan,days,amount,source,note,status,created_at,expires_at,claimed_at,used_at${status}${source}` +
          `&order=created_at.desc&limit=50&offset=${int(b.offset, 0, 1e6, 0)}`);
        return json({ ok: true, rewards: await withNames(rows) });
      }

      case "payments": {
        const rows = await rest<{ user_id: string | null }[]>("GET",
          "payments?select=id,user_id,provider,plan,days,currency,amount,status,created_at,paid_at,note" +
          `&order=created_at.desc&limit=50&offset=${int(b.offset, 0, 1e6, 0)}`);
        return json({ ok: true, payments: await withNames(rows) });
      }

      case "emails": {
        const rows = await rest<{ user_id: string }[]>("GET",
          `email_log?select=id,user_id,kind,ref,created_at&order=created_at.desc&limit=50&offset=${int(b.offset, 0, 1e6, 0)}`);
        return json({ ok: true, emails: await withNames(rows) });
      }

      case "log": {
        const rows = await rest<{ target: string | null }[]>("GET",
          `admin_log?select=id,action,target,detail,created_at&order=created_at.desc&limit=60&offset=${int(b.offset, 0, 1e6, 0)}`);
        return json({ ok: true, log: await withNames(rows.map((r) => ({ ...r, user_id: r.target }))) });
      }

      case "settings": {
        const rows = await rest<{ value: unknown }[]>("GET", "settings?key=eq.referral&select=value");
        return json({ ok: true, referral: rows[0]?.value ?? null });
      }

      case "settings_set": {
        const r = (b.referral ?? {}) as Record<string, unknown>;
        const p = (r.purchase ?? {}) as Record<string, unknown>;
        const value = {
          signup: int(r.signup, 0, 100, 2), active: int(r.active, 0, 100, 3), active_days: int(r.active_days, 1, 60, 3),
          welcome: int(r.welcome, 0, 100, 2), monthly_cap: int(r.monthly_cap, 0, 1000, 10),
          purchase: Object.fromEntries(Object.keys(PLANS).map((k) => [k, int(p[k], 0, 100, 0)])),
        };
        await rest("POST", "settings?on_conflict=key", [{ key: "referral", value, updated_at: new Date().toISOString() }],
          "resolution=merge-duplicates");
        await log(user, "settings", null, { referral: value });
        return json({ ok: true, referral: value });
      }

      case "push_test": {
        const sent = await pushUser(user.id, () => ({ title: "Probalis · test", body: "Les notifications marchent sur ce téléphone.", url: "/office/", tag: "test" }));
        return json({ ok: true, sent });
      }

      case "broadcast": {
        // Notification à tous les téléphones abonnés (annonce). Rien n'est envoyé par e-mail.
        const title = text(b.title, 80);
        const body = text(b.body, 240);
        const url = String(b.url ?? "/");
        if (!title || !body) return json({ error: "text" }, 400);
        const subs = await rest<{ id: number; endpoint: string; p256dh: string; auth: string; lang: string }[]>(
          "GET", "push_subs?select=id,endpoint,p256dh,auth,lang&limit=20000");
        const sent = await pushSubs(subs, () => ({ title, body, url: url.startsWith("/") && !url.startsWith("//") ? url : "/", tag: "news" }));
        await log(user, "broadcast", null, { title, body, sent });
        return json({ ok: true, sent, devices: subs.length });
      }

      case "email_test": {
        if (!user.email) return json({ error: "email" }, 400);
        const ok = await sendEmail("welcome", b.lang === "en" ? "en" : "fr", user.email, { name: "Admin" }, `test-${Date.now()}`);
        return json({ ok });
      }
    }
    return json({ error: "action" }, 400);
  } catch (e) {
    console.error(action, e);
    return json({ error: "server" }, 500);
  }
});

/** Ajoute le nom et l'e-mail du membre à chaque ligne (une seule requête). */
async function withNames<T extends { user_id?: string | null }>(rows: T[]): Promise<(T & { member: { name: string | null; email: string | null } | null })[]> {
  const ids = [...new Set(rows.map((r) => r.user_id).filter((x): x is string => !!x && UUID.test(x)))];
  const people = ids.length
    ? await rest<{ id: string; name: string | null; email: string | null }[]>("GET", `profiles?id=in.(${ids.map(enc).join(",")})&select=id,name,email`)
    : [];
  const by = new Map(people.map((p) => [p.id, { name: p.name, email: p.email }]));
  return rows.map((r) => ({ ...r, member: r.user_id ? by.get(r.user_id) ?? null : null }));
}
