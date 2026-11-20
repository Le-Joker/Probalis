/* Gardien des chiffres Premium : Cloudflare Pages Function, écrite par probalis/site/build.py dans
   functions/lk/[[path]].js (ne pas modifier le fichier écrit : il est refait à chaque construction).

   Tout ce qui est sous /lk/ (les vrais blocs de chiffres et les données complètes) n'est envoyé qu'après avoir
   vérifié le compte auprès de Supabase, avec le jeton de connexion envoyé par l'appli :
   - Premium en cours : tout ;
   - compte gratuit : /lk/<langue>/free.json (le n° 1 de chaque liste de paris) et /lk/<langue>/m/<match>.json,
     seulement pour le match de son analyse gratuite du jour ;
   - sans compte, jeton faux ou expiré : refusé (401), compte sans droit : refusé (403).
   Les réponses ne sont gardées nulle part (no-store). Le résultat de la vérification est gardé 60 s au plus,
   côté serveur seulement.

   Les fichiers eux-mêmes ne sont pas dans /lk/ mais dans un dossier au nom tiré au hasard à chaque construction
   (DIR), connu de ce seul fichier : aucune adresse écrite autrement (//lk/…, /%6ck/…, majuscules) ne peut donc
   les atteindre sans passer par ici. Ils y sont compressés (.gz) : on les décompresse avant de répondre. */
const SB_URL = '__SB_URL__';
const SB_KEY = '__SB_KEY__';
const DIR = '__LK_DIR__';
const DAY = 864e5;
const PATH = /^\/lk\/(?:(?:fr|en)\/(?:(free)|m\/([a-z0-9-]{1,160})|(?:match\/)?[a-z0-9-]{1,160})|data\/[a-z0-9-]{1,40})\.json$/;
const BEARER = /^Bearer\s+([A-Za-z0-9._~+\/=-]{20,4096})$/;

const deny = (status) => new Response(status === 401 ? 'Connexion requise' : status === 404 ? 'Introuvable' : 'Accès refusé', {
  status,
  headers: { 'Content-Type': 'text/plain; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex' }
});

const sha256 = async (s) => {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, '0')).join('');
};

const ymd = (t) => new Date(t).toISOString().slice(0, 10);
// Le jour de l'analyse gratuite vient du téléphone (minuit à l'heure locale) : à un jour près du jour UTC
const recent = (d) => {
  if (!d) return false;
  const now = Date.now();
  return [ymd(now - DAY), ymd(now), ymd(now + DAY)].includes(String(d).slice(0, 10));
};
const premium = (p) => !!p.premium_until && Date.parse(p.premium_until) > Date.now();

// Profil du compte : Supabase vérifie lui-même le jeton (signature, expiration) et ne renvoie que la ligne du compte
async function profile(token, ctx, fresh) {
  const key = new Request('https://lk-auth.probalis.invalid/' + (await sha256(token)));
  let cache = null;
  try { cache = caches.default; } catch (e) { cache = null; }
  if (cache && !fresh) {
    const hit = await cache.match(key);
    if (hit) return hit.json();
  }
  let r;
  try {
    r = await fetch(SB_URL + '/rest/v1/profiles?select=premium_until,free_day,free_match,extra_matches&limit=1', {
      headers: { apikey: SB_KEY, Authorization: 'Bearer ' + token, Accept: 'application/json' }
    });
  } catch (e) {
    return null;
  }
  if (!r.ok) return null;
  const rows = await r.json().catch(() => null);
  const p = Array.isArray(rows) && rows[0] ? rows[0] : null;
  if (p && cache) {
    ctx.waitUntil(cache.put(key, new Response(JSON.stringify(p), {
      headers: { 'Content-Type': 'application/json', 'Cache-Control': 'max-age=60' }
    })).catch(() => {}));
  }
  return p;
}

export async function onRequest(ctx) {
  const { request, env } = ctx;
  if (request.method !== 'GET' && request.method !== 'HEAD') return deny(405);
  const url = new URL(request.url);
  const m = PATH.exec(url.pathname);
  if (!m) return deny(404);
  if (!SB_URL || !SB_KEY || !DIR || DIR === 'lk') return deny(403);
  const auth = BEARER.exec(request.headers.get('Authorization') || '');
  if (!auth) return deny(401);

  // Premium : tout ; compte gratuit : le n° 1 de chaque liste, le match de son analyse du jour et ceux ouverts avec
  // une analyse offerte (parrainage, cadeau)
  const extra = (p) => Array.isArray(p.extra_matches) && p.extra_matches.includes(m[2]);
  const allowed = (p) => premium(p) || !!m[1] || (!!m[2] && ((p.free_match === m[2] && recent(p.free_day)) || extra(p)));
  let p = await profile(auth[1], ctx, false);
  // Le profil a pu changer depuis la dernière vérification (analyse gratuite choisie, Premium acheté) : on revérifie
  if (p && !allowed(p)) p = await profile(auth[1], ctx, true);
  if (!p) return deny(401);
  if (!allowed(p)) return deny(403);

  const res = await env.ASSETS.fetch(new Request(new URL('/' + DIR + url.pathname.slice(3) + '.gz', url.origin).toString(), { method: 'GET' }));
  if (!res.ok) return deny(404);
  const buf = await res.arrayBuffer();
  const bytes = new Uint8Array(buf, 0, Math.min(2, buf.byteLength));
  let body;
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    body = new Blob([buf]).stream().pipeThrough(new DecompressionStream('gzip'));
  } else if (bytes[0] === 0x7b) {
    body = buf;  // déjà décompressé en route
  } else {
    return deny(404);
  }
  return new Response(request.method === 'HEAD' ? null : body, {
    status: 200,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'private, no-store',
      'Vary': 'Authorization',
      'X-Robots-Tag': 'noindex',
      'X-Content-Type-Options': 'nosniff'
    }
  });
}
