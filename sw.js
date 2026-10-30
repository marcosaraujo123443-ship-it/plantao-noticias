/* Plantão Informa: permite instalar o site como app e abrir a última versão mesmo sem internet.
   Páginas e dados: sempre da rede primeiro (notícias frescas); cópia guardada só para quando estiver offline. */
const CACHE = 'plantao-v1';
const BASE = ['/', '/site.webmanifest', '/icon-192.png', '/icon-512.png', '/apple-touch-icon.png', '/favicon.png'];
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(BASE)).then(() => self.skipWaiting())); });
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const r = e.request, u = new URL(r.url);
  if (r.method !== 'GET' || u.origin !== location.origin || r.headers.has('range') || u.pathname.endsWith('.mp3')) return;
  const estatico = /\.(png|jpg|ico|webmanifest|woff2?)$/.test(u.pathname);
  if (estatico) {   // ícones e imagens: cópia guardada, atualizada em segundo plano
    e.respondWith(caches.match(r).then(c => {
      const rede = fetch(r).then(res => { if (res.ok) caches.open(CACHE).then(k => k.put(r, res.clone())); return res; });
      return c || rede;
    }));
    return;
  }
  e.respondWith(fetch(r).then(res => {
    if (res.ok && (r.mode === 'navigate' || u.pathname.endsWith('.json'))) { const cp = res.clone(); caches.open(CACHE).then(k => k.put(r, cp)); }
    return res;
  }).catch(() => caches.match(r, {ignoreSearch: true}).then(c => c || (r.mode === 'navigate' ? caches.match('/') : Response.error()))));
});
