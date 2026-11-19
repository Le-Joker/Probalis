// Paiements Premium : Stripe (cartes, Apple Pay, Google Pay… dans le monde entier) et Flutterwave
// (mobile money et cartes en Afrique). Le prix et le moyen de paiement dépendent du pays choisi (prices.json,
// le même fichier que le site).
import prices from "./prices.json" with { type: "json" };
import { claim, fmtDate, firstName, sendEmail, unclaim } from "./email.ts";
import { hmacHex, rest, same, SITE_URL } from "./http.ts";

type Currency = { provider: "stripe" | "flutterwave"; decimals: number; week: number; month: number; options?: string };
export type Plan = "week" | "month";
export type Offer = { plan: Plan; days: number; currency: string; amount: number; provider: Currency["provider"]; options?: string };

const CURRENCIES = prices.currencies as Record<string, Currency>;
const COUNTRIES = prices.countries as Record<string, string>;

export function offer(plan: string, country: string, lang: "fr" | "en"): Offer | null {
  if (plan !== "week" && plan !== "month") return null;
  const code = COUNTRIES[country] ?? (prices.default_currency as Record<string, string>)[lang] ?? "EUR";
  const cur = CURRENCIES[code];
  if (!cur) return null;
  const days = (prices.plans as Record<string, { days: number }>)[plan].days;
  return { plan, days, currency: code, amount: cur[plan], provider: cur.provider, options: cur.options };
}

const minor = (amount: number, currency: string) => Math.round(amount * 10 ** (CURRENCIES[currency]?.decimals ?? 2));

export type Payment = {
  id: string;
  user_id: string | null;
  provider: "stripe" | "flutterwave";
  plan: Plan;
  days: number;
  currency: string;
  amount: number;
  lang: "fr" | "en";
  status: string;
  provider_ref: string | null;
  paid_at: string | null;
};

export async function getPayment(id: string): Promise<Payment | null> {
  if (!/^[0-9a-f-]{36}$/i.test(id)) return null;
  const rows = await rest<Payment[]>("GET", `payments?id=eq.${id}&select=*`);
  return rows[0] ?? null;
}

// ---------- Stripe ----------
const STRIPE = "https://api.stripe.com/v1";
const stripeKey = () => Deno.env.get("STRIPE_SECRET_KEY") ?? "";

async function stripe(method: string, path: string, form?: Record<string, string>, idem?: string) {
  const headers: Record<string, string> = { Authorization: `Bearer ${stripeKey()}` };
  if (form) headers["Content-Type"] = "application/x-www-form-urlencoded";
  if (idem) headers["Idempotency-Key"] = idem;
  const r = await fetch(`${STRIPE}${path}`, { method, headers, body: form ? new URLSearchParams(form) : undefined });
  const data = await r.json();
  if (!r.ok) throw new Error(`Stripe ${path} : ${r.status} ${JSON.stringify(data?.error ?? data).slice(0, 300)}`);
  return data;
}

export async function stripeCheckout(pay: Payment, email: string | undefined, label: string): Promise<string> {
  const lang = pay.lang;
  const form: Record<string, string> = {
    mode: "payment",
    locale: lang,
    client_reference_id: pay.id,
    success_url: `${SITE_URL}/${lang}/compte.html?paiement=ok&session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${SITE_URL}/${lang}/premium.html?paiement=annule`,
    "line_items[0][quantity]": "1",
    "line_items[0][price_data][currency]": pay.currency.toLowerCase(),
    "line_items[0][price_data][unit_amount]": String(minor(pay.amount, pay.currency)),
    "line_items[0][price_data][product_data][name]": label,
    "metadata[payment_id]": pay.id,
    "payment_intent_data[metadata][payment_id]": pay.id,
  };
  if (email) form.customer_email = email;
  // Pas de « payment_method_types » : Stripe propose les moyens activés dans le tableau de bord
  // (carte, Apple Pay, Google Pay, Link, et les moyens locaux selon le pays).
  const s = await stripe("POST", "/checkout/sessions", form, `checkout-${pay.id}`);
  await rest("PATCH", `payments?id=eq.${pay.id}`, { provider_ref: s.id });
  return s.url as string;
}

/** Vérifie une session Stripe auprès de Stripe (on ne croit jamais le navigateur sur parole). */
export async function stripeConfirm(sessionId: string): Promise<{ payment: Payment; ref: string } | null> {
  if (!/^cs_[A-Za-z0-9_]+$/.test(sessionId)) return null;
  const s = await stripe("GET", `/checkout/sessions/${sessionId}`);
  if (s.payment_status !== "paid") return null;
  const pay = await getPayment(s.client_reference_id ?? s.metadata?.payment_id ?? "");
  if (!pay || pay.provider !== "stripe") return null;
  if (s.currency !== pay.currency.toLowerCase() || s.amount_total < minor(pay.amount, pay.currency)) return null;
  return { payment: pay, ref: s.id };
}

/** Signature des webhooks Stripe : HMAC-SHA256 de « horodatage.corps » avec le secret du webhook. */
export async function stripeSignatureOk(raw: string, header: string, secret: string, toleranceSec = 300): Promise<boolean> {
  const parts = Object.fromEntries(
    header.split(",").map((p) => p.split("=")).filter((kv) => kv.length === 2).map(([k, v]) => [k.trim(), v.trim()]),
  );
  const t = Number(parts.t);
  if (!t || Math.abs(Date.now() / 1000 - t) > toleranceSec) return false;
  const expected = await hmacHex(secret, `${t}.${raw}`);
  return header.split(",").some((p) => p.trim().startsWith("v1=") && same(p.trim().slice(3), expected));
}

// ---------- Flutterwave ----------
const FLW = "https://api.flutterwave.com/v3";
const flwKey = () => Deno.env.get("FLW_SECRET_KEY") ?? "";

export async function flutterwaveCheckout(pay: Payment, email: string, name: string, label: string,
  options?: string): Promise<string> {
  const r = await fetch(`${FLW}/payments`, {
    method: "POST",
    headers: { Authorization: `Bearer ${flwKey()}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      tx_ref: pay.id,
      amount: pay.amount,
      currency: pay.currency,
      // Adresse sans « ? » : Flutterwave y ajoute status, tx_ref et transaction_id
      redirect_url: `${SITE_URL}/${pay.lang}/compte.html`,
      payment_options: options ?? "card",
      customer: { email, name },
      customizations: { title: "Probalis Premium", description: label, logo: `${SITE_URL}/icons/icone-192.png` },
      meta: { payment_id: pay.id },
    }),
  });
  const data = await r.json();
  if (!r.ok || data.status !== "success" || !data.data?.link) {
    throw new Error(`Flutterwave : ${r.status} ${JSON.stringify(data).slice(0, 300)}`);
  }
  return data.data.link as string;
}

/** Vérifie une transaction Flutterwave auprès de Flutterwave. */
export async function flutterwaveConfirm(transactionId: string): Promise<{ payment: Payment; ref: string } | null> {
  if (!/^\d+$/.test(transactionId)) return null;
  const r = await fetch(`${FLW}/transactions/${transactionId}/verify`, { headers: { Authorization: `Bearer ${flwKey()}` } });
  const data = await r.json();
  const tx = data?.data;
  if (!r.ok || data.status !== "success" || tx?.status !== "successful") return null;
  const pay = await getPayment(String(tx.tx_ref ?? ""));
  if (!pay || pay.provider !== "flutterwave") return null;
  if (tx.currency !== pay.currency || Number(tx.amount) < Number(pay.amount)) return null;
  return { payment: pay, ref: String(tx.id) };
}

// ---------- Activation du Premium et reçu ----------
const PLAN_LABEL = { fr: { week: "Pass 7 jours", month: "Pass 30 jours" }, en: { week: "7-day pass", month: "30-day pass" } };
const PROVIDER_LABEL = {
  fr: { stripe: "Carte ou portefeuille (Stripe)", flutterwave: "Mobile money ou carte (Flutterwave)" },
  en: { stripe: "Card or wallet (Stripe)", flutterwave: "Mobile money or card (Flutterwave)" },
};

export const planLabel = (plan: Plan, lang: "fr" | "en") => `Probalis Premium · ${PLAN_LABEL[lang][plan]}`;

export function money(amount: number, currency: string, lang: "fr" | "en"): string {
  const d = CURRENCIES[currency]?.decimals ?? 2;
  try {
    return new Intl.NumberFormat(lang === "en" ? "en-US" : "fr-FR", {
      style: "currency", currency, minimumFractionDigits: d, maximumFractionDigits: d,
    }).format(amount);
  } catch {
    return `${amount} ${currency}`;
  }
}

/** Active le Premium (une seule fois par paiement) puis envoie le reçu. */
export async function finalize(paymentId: string, ref: string): Promise<{ premium_until: string | null } | null> {
  const rows = await rest<{ user_id: string | null; premium_until: string | null; newly_paid: boolean }[]>(
    "POST", "rpc/grant_premium", { p_payment: paymentId, p_ref: ref });
  const g = rows?.[0];
  if (!g) return null;
  if (g.newly_paid && g.user_id) await sendReceipt(paymentId).catch((e) => console.error("reçu", e));
  return { premium_until: g.premium_until };
}

async function sendReceipt(paymentId: string): Promise<void> {
  const pay = await getPayment(paymentId);
  if (!pay?.user_id) return;
  const profiles = await rest<{ email: string | null; name: string | null; lang: string; premium_until: string | null }[]>(
    "GET", `profiles?id=eq.${pay.user_id}&select=email,name,lang,premium_until`);
  const p = profiles[0];
  if (!p?.email || !p.premium_until) return;
  if (!(await claim(pay.user_id, "receipt", pay.id))) return;
  const lang = p.lang === "en" ? "en" : "fr";
  const ok = await sendEmail("receipt", lang, p.email, {
    name: firstName(p.name, p.email),
    plan: PLAN_LABEL[lang][pay.plan],
    amount: money(Number(pay.amount), pay.currency, lang),
    provider: PROVIDER_LABEL[lang][pay.provider],
    date: fmtDate(pay.paid_at ?? new Date().toISOString(), lang),
    ref: `PB-${pay.id.slice(0, 8).toUpperCase()}`,
    until: fmtDate(p.premium_until, lang),
  }, `receipt-${pay.id}`);
  if (ok) await rest("PATCH", `payments?id=eq.${pay.id}`, { receipt_sent_at: new Date().toISOString() });
  else await unclaim(pay.user_id, "receipt", pay.id);
}
