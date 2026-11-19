/* Service worker Probalis : pages à jour en priorité, version enregistrée si le réseau traîne ou manque. */
const VERSION = '__VERSION__';
const CORE = `probalis-core-${VERSION}`;
const PAGES = 'probalis-pages';
const CRESTS = 'probalis-crests';
const PRECACHE = ['/assets/style.css', '/assets/app.js', '/manifest.webmanifest',
  '/icons/icone-192.png', '/icons/probalis-icone.svg', '__FONTS__'];
const SLOW_MS = 3500;   // au-delà, on montre la dernière version enregistrée et on met à jour en arrière-plan
const MAX_PAGES = 40;
const MAX_CRESTS = 600;

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CORE).then((c) => c.addAll(PRECACHE)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then((keys) => Promise.all(
    keys.filter((k) => k !== CORE && k !== PAGES && k !== CRESTS).map((k) => caches.delete(k))
  )).then(() => self.clients.claim()));
});

const trim = (name, max) => caches.open(name).then((c) => c.keys().then((keys) =>
  Promise.all(keys.slice(0, Math.max(0, keys.length - max)).map((k) => c.delete(k)))));

const offlinePage = (lang) => new Response(
  `<!doctype html><html lang="${lang}"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">` +
  `<title>Probalis</title><body style="font-family:system-ui,sans-serif;background:#F3F5F8;color:#0B1F3A;text-align:center;padding:4rem 1.5rem">` +
  `<h1 style="font-size:1.3rem">${lang === 'fr' ? 'Hors connexion' : 'Offline'}</h1>` +
  `<p>${lang === 'fr' ? 'Cette page n’a pas encore été enregistrée sur ton téléphone. Reconnecte-toi puis réessaie.'
    : 'This page hasn’t been saved on your phone yet. Reconnect and try again.'}</p>` +
  `<p><a href="/${lang}/" style="color:#15803D;font-weight:700">Probalis</a></p></body></html>`,
  { headers: { 'Content-Type': 'text/html; charset=utf-8' } });

// Pages : réseau d'abord ; si la connexion est lente, la version enregistrée s'affiche au bout de 3,5 s
// pendant que la nouvelle se télécharge pour la prochaine fois.
function page(e, req, url) {
  const key = url.origin + url.pathname;
  const lang = url.pathname.split('/')[1] === 'en' ? 'en' : 'fr';
  const net = fetch(req).then((res) => {
    if (res.ok && res.type === 'basic') {
      const copy = res.clone();
      e.waitUntil(caches.open(PAGES).then((c) => c.put(key, copy)).then(() => trim(PAGES, MAX_PAGES)));
    }
    return res;
  });
  const cached = caches.match(key);
  const slow = new Promise((resolve) => setTimeout(resolve, SLOW_MS)).then(() => cached).then((hit) => hit || net);
  return Promise.race([net, slow])
    .catch(() => cached.then((hit) => hit || caches.match(`${url.origin}/${lang}/`)).then((hit) => hit || offlinePage(lang)));
}

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.origin !== location.origin) {
    // Logos des équipes : gardés sur le téléphone (ils changent rarement)
    if (req.destination === 'image') {
      e.respondWith(caches.open(CRESTS).then((c) => c.match(req).then((hit) => hit || fetch(req).then((res) => {
        if (res.ok || res.type === 'opaque') {
          c.put(req, res.clone());
          e.waitUntil(trim(CRESTS, MAX_CRESTS));
        }
        return res;
      }))));
    }
    return;
  }

  if (req.mode === 'navigate' || req.destination === 'document' || req.headers.get('X-Probalis-Nav') ||
      url.pathname.endsWith('.html') || url.pathname.endsWith('/')) {
    e.respondWith(page(e, req, url));
    return;
  }

  if (url.pathname.startsWith('/data/')) return;  // données : toujours fraîches
  e.respondWith(caches.match(req, { ignoreSearch: true }).then((hit) => hit || fetch(req)));
});
