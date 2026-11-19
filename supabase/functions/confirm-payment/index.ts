// Au retour de la page de paiement : vérifie le paiement auprès de Stripe ou Flutterwave et active le Premium
// tout de suite (le webhook le fait aussi, au cas où la personne ferme la page trop tôt).
import { getUser, json, preflight, readJson } from "../_shared/http.ts";
import { finalize, flutterwaveConfirm, stripeConfirm } from "../_shared/payments.ts";

Deno.serve(async (req) => {
  const pre = preflight(req);
  if (pre) return pre;
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const user = await getUser(req);
  if (!user) return json({ error: "auth" }, 401);
  const body = await readJson(req);
  try {
    const found = body.provider === "stripe"
      ? await stripeConfirm(String(body.session_id ?? ""))
      : body.provider === "flutterwave"
      ? await flutterwaveConfirm(String(body.transaction_id ?? ""))
      : null;
    if (!found) return json({ ok: false, status: "pending" });
    if (found.payment.user_id !== user.id) return json({ error: "forbidden" }, 403);
    const g = await finalize(found.payment.id, found.ref);
    return json({ ok: true, premium_until: g?.premium_until ?? null });
  } catch (e) {
    console.error(e);
    return json({ error: "server" }, 500);
  }
});
