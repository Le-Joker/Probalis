// Avis de paiement envoyés directement par Stripe et Flutterwave (même si la personne ferme la page).
// Adresses à donner dans leurs tableaux de bord :
//   https://<projet>.supabase.co/functions/v1/payment-webhook?provider=stripe
//   https://<projet>.supabase.co/functions/v1/payment-webhook?provider=flutterwave
import { json, rest, same } from "../_shared/http.ts";
import { finalize, flutterwaveConfirm, getPayment, stripeConfirm, stripeSignatureOk } from "../_shared/payments.ts";

Deno.serve(async (req) => {
  if (req.method !== "POST") return json({ error: "method" }, 405);
  const provider = new URL(req.url).searchParams.get("provider");
  const raw = await req.text();
  try {
    if (provider === "stripe") {
      const secret = Deno.env.get("STRIPE_WEBHOOK_SECRET") ?? "";
      if (!secret || !(await stripeSignatureOk(raw, req.headers.get("Stripe-Signature") ?? "", secret))) {
        return json({ error: "signature" }, 400);
      }
      const event = JSON.parse(raw);
      const s = event.data?.object ?? {};
      if (event.type === "checkout.session.completed" || event.type === "checkout.session.async_payment_succeeded") {
        const found = await stripeConfirm(String(s.id ?? "")); // on relit la session chez Stripe
        if (found) await finalize(found.payment.id, found.ref);
      } else if (event.type === "checkout.session.expired" || event.type === "checkout.session.async_payment_failed") {
        const pay = await getPayment(String(s.client_reference_id ?? ""));
        if (pay && pay.status === "pending") {
          await rest("PATCH", `payments?id=eq.${pay.id}&status=eq.pending`,
            { status: event.type === "checkout.session.expired" ? "cancelled" : "failed" });
        }
      }
      return json({ received: true });
    }

    if (provider === "flutterwave") {
      const hash = Deno.env.get("FLW_WEBHOOK_HASH") ?? "";
      if (!hash || !same(req.headers.get("verif-hash") ?? "", hash)) return json({ error: "signature" }, 401);
      const event = JSON.parse(raw);
      const tx = event.data ?? {};
      if ((event.event === "charge.completed" || event.type === "charge.completed") && tx.id) {
        const found = await flutterwaveConfirm(String(tx.id)); // on vérifie toujours auprès de Flutterwave
        if (found) await finalize(found.payment.id, found.ref);
        else if (tx.status === "failed" && tx.tx_ref) {
          await rest("PATCH", `payments?id=eq.${encodeURIComponent(String(tx.tx_ref))}&status=eq.pending`, { status: "failed" })
            .catch(() => {});
        }
      }
      return json({ received: true });
    }

    return json({ error: "provider" }, 400);
  } catch (e) {
    console.error(e);
    return json({ error: "server" }, 500); // Stripe et Flutterwave réessaieront plus tard
  }
});
