// Outils communs des fonctions Probalis : réponses, base de données (API REST) et utilisateur connecté.
// Aucune bibliothèque externe : seulement fetch, pour des fonctions rapides et faciles à relire.

export const SUPABASE_URL = (Deno.env.get("SUPABASE_URL") ?? "").replace(/\/$/, "");
const SERVICE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "";
const ANON_KEY = Deno.env.get("SUPABASE_ANON_KEY") ?? "";
export const SITE_URL = (Deno.env.get("SITE_URL") ?? "").replace(/\/$/, "");

export const cors: Record<string, string> = {
  "Access-Control-Allow-Origin": "*", // l'accès est protégé par le jeton de connexion, pas par des cookies
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), { status, headers: { ...cors, "Content-Type": "application/json" } });
}

export function preflight(req: Request): Response | null {
  return req.method === "OPTIONS" ? new Response("ok", { headers: cors }) : null;
}

function keyHeaders(key: string): Record<string, string> {
  const h: Record<string, string> = { apikey: key };
  if (key.startsWith("eyJ")) h.Authorization = `Bearer ${key}`; // anciennes clés (JWT) ; les clés sb_secret_ vont seulement dans apikey
  return h;
}

/** Appel à la base avec la clé secrète (ignore les règles de sécurité : à n'utiliser que côté serveur). */
export async function rest<T = any>(method: string, path: string, body?: unknown, prefer?: string): Promise<T> {
  const headers: Record<string, string> = { ...keyHeaders(SERVICE_KEY), "Content-Type": "application/json" };
  if (prefer) headers.Prefer = prefer;
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await r.text();
  if (!r.ok) throw new Error(`base ${method} ${path.split("?")[0]} : ${r.status} ${text.slice(0, 300)}`);
  return (text ? JSON.parse(text) : null) as T;
}

export type User = { id: string; email?: string; user_metadata?: Record<string, string> };

/** Utilisateur connecté d'après son jeton (envoyé automatiquement par le site), ou null. */
export async function getUser(req: Request): Promise<User | null> {
  const auth = req.headers.get("Authorization") ?? "";
  if (!auth.startsWith("Bearer ")) return null;
  const r = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
    headers: { apikey: ANON_KEY || SERVICE_KEY, Authorization: auth },
  });
  if (!r.ok) return null;
  const u = await r.json();
  return u && u.id ? (u as User) : null;
}

export type Profile = {
  id: string;
  email: string | null;
  name: string | null;
  lang: "fr" | "en";
  is_adult: boolean;
  premium_until: string | null;
  welcome_sent_at: string | null;
};

export async function getProfile(id: string): Promise<Profile | null> {
  const rows = await rest<Profile[]>("GET", `profiles?id=eq.${encodeURIComponent(id)}&select=*`);
  return rows[0] ?? null;
}

export async function readJson(req: Request): Promise<Record<string, any>> {
  try {
    return await req.json();
  } catch {
    return {};
  }
}

/** Comparaison en temps constant (signatures, jetons). */
export function same(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function hmacHex(secret: string, message: string): Promise<string> {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" },
    false, ["sign"]);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(message));
  return Array.from(new Uint8Array(sig)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const lang = (v: unknown): "fr" | "en" => (v === "en" ? "en" : "fr");
