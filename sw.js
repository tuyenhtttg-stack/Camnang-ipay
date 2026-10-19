/* Service worker: cho phép mở app khi không có mạng.
   Mỗi lần cập nhật index.html, tăng số phiên bản bên dưới (v1 → v2 ...) */
const CACHE = 'cam-nang-ipay-v2';
const ASSETS = ['./', './index.html', './manifest.webmanifest',
  './icons/icon-192.png', './icons/icon-512.png', './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png', './icons/favicon-64.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  if (req.mode === 'navigate') {
    // Trang chính: ưu tiên bản mới trên mạng, mất mạng thì dùng bản đã lưu
    e.respondWith(fetch(req).then(r => { const c = r.clone(); caches.open(CACHE).then(x => x.put('./index.html', c)); return r; })
      .catch(() => caches.match('./index.html')));
    return;
  }
  if (req.url.includes('/audio/')) {
    if (req.url.endsWith('.json')) {
      // Danh sách file giọng đọc: ưu tiên bản mới, mất mạng dùng bản đã lưu
      e.respondWith(fetch(req).then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); } return r; })
        .catch(() => caches.match(req)));
    } else {
      // File MP3: nghe 1 lần là lưu lại để nghe khi không có mạng
      e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => { if (r.ok) { const c = r.clone(); caches.open(CACHE).then(x => x.put(req, c)); } return r; })));
    }
    return;
  }
  e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});
