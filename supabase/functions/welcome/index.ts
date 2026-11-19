// E-mail de bienvenue, envoyé une seule fois, juste après la première connexion Google.
import { firstName, sendEmail } from "../_shared/email.ts";
import { getUser, json, lang, preflight, readJson, rest } from "../_shared/http.ts";

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const user = await getUser(req);
  if (!user) return json({ error: "auth" }, 401);
  const body = await readJson(req);
  const l = lang(body.lang);
  try {
    // « Réserve » l'envoi : seul le premier appel trouve welcome_sent_at vide (pas de doublon si on clique deux fois)
    const rows = await rest<{ email: string | null; name: string | null }[]>(
      "PATCH", `profiles?id=eq.${user.id}&welcome_sent_at=is.null`,
      { welcome_sent_at: new Date().toISOString(), lang: l }, "return=representation");
    const p = rows[0];
    if (!p) return json({ ok: true, already: true });
    const email = p.email ?? user.email;
    if (!email) return json({ ok: true, sent: false });
    const sent = await sendEmail("welcome", l, email, { name: firstName(p.name, email) }, `welcome-${user.id}`);
    const configured = !!(Deno.env.get("RESEND_API_KEY") && Deno.env.get("EMAIL_FROM"));
    if (!sent && configured) await rest("PATCH", `profiles?id=eq.${user.id}`, { welcome_sent_at: null }); // on réessaiera
    return json({ ok: true, sent });
  } catch (e) {
    console.error(e);
    return json({ error: "server" }, 500);
  }
});
