// Désinscription des alertes sans se connecter, avec un lien signé (le lien en bas de chaque alerte).
//  - POST {u, k, t} depuis la page Mon compte du site (le lien de l'e-mail y mène) ;
//  - POST « en un clic » des messageries (Gmail, Outlook…) grâce à l'en-tête List-Unsubscribe ;
//  - GET : renvoie vers la page Mon compte du site (Supabase n'affiche pas de pages HTML).
// k = « news » (grand choc demain) ou « reminders » (rappel avant la fin du Premium).
import { cors, hmacHex, json, preflight, rest, same, SITE_URL } from "../_shared/http.ts";

const FIELD: Record<string, string> = { news: "email_news", reminders: "email_reminders" };

async function valid(u: string, k: string, t: string): Promise<boolean> {
  const secret = Deno.env.get("UNSUBSCRIBE_SECRET") ?? "";
  if (!secret || !FIELD[k] || !/^[0-9a-f-]{36}$/i.test(u) || !t) return false;
  const expected = (await hmacHex(secret, `${u}:${k}`)).slice(0, 32);
  return same(t, expected);
}

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  const url = new URL(req.url);
  let u = url.searchParams.get("u") ?? "";
  let k = url.searchParams.get("k") ?? "";
  let t = url.searchParams.get("t") ?? "";

  if (req.method === "GET") {
    const l = url.searchParams.get("l") === "en" ? "en" : "fr";
    const q = new URLSearchParams({ desabo: k, u, t });
    return new Response(null, { status: 303, headers: { ...cors, Location: `${SITE_URL}/${l}/compte.html?${q}` } });
  }
  if (req.method !== "POST") return json({ error: "method" }, 405);

  if ((req.headers.get("Content-Type") ?? "").includes("application/json")) {
    const body = await req.json().catch(() => ({}));
    u = String(body.u ?? u);
    k = String(body.k ?? k);
    t = String(body.t ?? t);
  }
  if (!(await valid(u, k, t))) return json({ error: "invalid" }, 400);
  try {
    await rest("PATCH", `profiles?id=eq.${u}`, { [FIELD[k]]: false });
    return json({ ok: true });
  } catch (e) {
    console.error(e);
    return json({ error: "server" }, 500);
  }
});
