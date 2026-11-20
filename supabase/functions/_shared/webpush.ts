// Notifications web (Web Push) sans bibliothèque : signature VAPID (ES256) et chiffrement « aes128gcm »
// (RFC 8291 et RFC 8188), avec seulement WebCrypto. Ce fichier n'utilise ni Deno ni la base : il est testé
// tel quel avec Node (scratchpad, voir docs/07-recompenses-admin-notifications.md).

export type Keys = { publicKey: string; privateJwk: JsonWebKey };
export type Subscription = { endpoint: string; p256dh: string; auth: string };
export type Message = { title: string; body: string; url?: string; tag?: string; lang?: string };

const enc = new TextEncoder();

export function b64u(bytes: Uint8Array | ArrayBuffer): string {
  const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let s = "";
  for (let i = 0; i < b.length; i++) s += String.fromCharCode(b[i]);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function unb64u(s: string): Uint8Array {
  const t = s.replace(/-/g, "+").replace(/_/g, "/");
  const bin = atob(t + "=".repeat((4 - (t.length % 4)) % 4));
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function concat(...parts: Uint8Array[]): Uint8Array {
  const out = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
  let o = 0;
  for (const p of parts) {
    out.set(p, o);
    o += p.length;
  }
  return out;
}

/** Nouvelle paire de clés VAPID (à garder une fois pour toutes : changer de clé coupe tous les abonnements). */
export async function generateKeys(): Promise<Keys> {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]) as CryptoKeyPair;
  const raw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const jwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  return { publicKey: b64u(raw), privateJwk: jwk };
}

async function hkdf(salt: Uint8Array, ikm: Uint8Array, info: Uint8Array, bytes: number): Promise<Uint8Array> {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, bytes * 8));
}

/** Jeton VAPID : prouve au service de notifications (Google, Mozilla, Apple…) que l'envoi vient de Probalis. */
export async function vapidHeader(endpoint: string, keys: Keys, subject: string, ttlSeconds = 12 * 3600): Promise<string> {
  const aud = new URL(endpoint).origin;
  const header = b64u(enc.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const payload = b64u(enc.encode(JSON.stringify({ aud, exp: Math.floor(Date.now() / 1000) + ttlSeconds, sub: subject })));
  const key = await crypto.subtle.importKey("jwk", keys.privateJwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, enc.encode(`${header}.${payload}`));
  return `vapid t=${header}.${payload}.${b64u(sig)}, k=${keys.publicKey}`;
}

/** Chiffre le message pour un téléphone précis (seul ce téléphone peut le lire). */
export async function encrypt(sub: Subscription, plaintext: Uint8Array,
  fixed?: { salt: Uint8Array; serverKeys: CryptoKeyPair }): Promise<Uint8Array> {
  const uaPublic = unb64u(sub.p256dh);
  const authSecret = unb64u(sub.auth);
  if (uaPublic.length !== 65 || authSecret.length !== 16) throw new Error("abonnement invalide");
  const server = fixed?.serverKeys ??
    await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]) as CryptoKeyPair;
  const asPublic = new Uint8Array(await crypto.subtle.exportKey("raw", server.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPublic, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const shared = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: uaKey }, server.privateKey, 256));
  const ikm = await hkdf(authSecret, shared, concat(enc.encode("WebPush: info\0"), uaPublic, asPublic), 32);
  const salt = fixed?.salt ?? crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, enc.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, enc.encode("Content-Encoding: nonce\0"), 12);
  const key = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const padded = concat(plaintext, new Uint8Array([2])); // un seul bloc : délimiteur 0x02, sans remplissage
  const cipher = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, key, padded));
  const rs = new Uint8Array([0, 0, 16, 0]); // taille de bloc 4096
  return concat(salt, rs, new Uint8Array([asPublic.length]), asPublic, cipher);
}

export type SendResult = { ok: boolean; status: number; gone: boolean };

/** Envoie une notification. gone = l'abonnement n'existe plus (à effacer). */
export async function send(sub: Subscription, msg: Message, keys: Keys, subject: string,
  ttlSeconds = 24 * 3600): Promise<SendResult> {
  const body = await encrypt(sub, enc.encode(JSON.stringify(msg)));
  const headers: Record<string, string> = {
    Authorization: await vapidHeader(sub.endpoint, keys, subject),
    "Content-Encoding": "aes128gcm",
    "Content-Type": "application/octet-stream",
    TTL: String(ttlSeconds),
    Urgency: "normal",
  };
  if (msg.tag && /^[A-Za-z0-9_-]{1,32}$/.test(msg.tag)) headers.Topic = msg.tag;
  try {
    const r = await fetch(sub.endpoint, { method: "POST", headers, body });
    await r.body?.cancel();
    return { ok: r.ok, status: r.status, gone: r.status === 404 || r.status === 410 };
  } catch {
    return { ok: false, status: 0, gone: false };
  }
}
