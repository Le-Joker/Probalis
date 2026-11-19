// Crée un paiement Premium et renvoie l'adresse de la page de paiement sécurisée (Stripe ou Flutterwave).
import { firstName } from "../_shared/email.ts";
import { getProfile, getUser, json, lang, preflight, readJson, rest } from "../_shared/http.ts";
import { flutterwaveCheckout, offer, type Payment, planLabel, stripeCheckout } from "../_shared/payments.ts";

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const user = await getUser(req);
  if (!user) return json({ error: "auth" }, 401);
  const body = await readJson(req);
  const l = lang(body.lang);
  const country = typeof body.country === "string" && /^[A-Z]{2}$/.test(body.country) ? body.country : "";
  const o = offer(String(body.plan ?? ""), country, l);
  if (!o) return json({ error: "plan" }, 400);
  try {
    const profile = await getProfile(user.id);
    if (!profile) return json({ error: "profile" }, 404);
    if (!profile.is_adult) return json({ error: "adult_required" }, 403);
    const email = profile.email ?? user.email ?? "";
    if (o.provider === "stripe" && !Deno.env.get("STRIPE_SECRET_KEY")) return json({ error: "stripe_not_configured" }, 503);
    if (o.provider === "flutterwave" && !Deno.env.get("FLW_SECRET_KEY")) return json({ error: "flutterwave_not_configured" }, 503);
    if (o.provider === "flutterwave" && !email) return json({ error: "email_required" }, 400);

    const rows = await rest<Payment[]>("POST", "payments", {
      user_id: user.id, provider: o.provider, plan: o.plan, days: o.days, currency: o.currency, amount: o.amount,
      country: country || null, lang: l,
    }, "return=representation");
    const pay = rows[0];
    const label = planLabel(o.plan, l);
    const url = o.provider === "stripe"
      ? await stripeCheckout(pay, email || undefined, label)
      : await flutterwaveCheckout(pay, email, firstName(profile.name, email), label, o.options);
    return json({ url, provider: o.provider });
  } catch (e) {
    console.error(e);
    return json({ error: "server" }, 500);
  }
});
