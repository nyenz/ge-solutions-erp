// PATH: erp-frontend/public/sw.js
// fix293 (David): lets the app be installed ("Download app") on a phone or laptop, with no Play Store.
// SAFE BY DESIGN: this helper saves NOTHING of the app or its data. Every page, file and API call goes to the server
// exactly as before, so an update is always seen at once and no old copy can ever be shown. Only when a page cannot be
// reached at all (no internet) does it show a small "No internet" page instead of the browser's error.
const OFFLINE = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Golden Seed - no internet</title><style>
html,body{margin:0;height:100%;background:#F8EBD0;font-family:'DM Sans',system-ui,sans-serif;color:#112F66}
.box{min-height:100%;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}
.card{max-width:420px;width:100%;background:linear-gradient(135deg,#4F8FE0 0%,#2A5AA3 38%,#1E4A8C 100%);color:#fff;border-radius:14px;
padding:28px 24px;border:1.5px solid rgba(255,255,255,.22);box-shadow:0 12px 30px rgba(17,47,102,.35),inset 0 1px 0 rgba(255,255,255,.12);
animation:up .5s cubic-bezier(.2,1,.3,1) both}
h1{margin:0 0 8px;font-size:18px;letter-spacing:2px;text-transform:uppercase}
p{margin:0 0 18px;font-size:14px;line-height:1.5;color:rgba(255,255,255,.88)}
button{font:900 12px/1 'DM Sans',system-ui,sans-serif;letter-spacing:1.5px;text-transform:uppercase;padding:12px 18px;border-radius:6px;
border:1.5px solid #F26A0D;background:#F26A0D;color:#112F66;cursor:pointer;box-shadow:0 4px 16px rgba(242,106,13,.32)}
@keyframes up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.card{animation:none}}
</style></head><body><div class="box"><div class="card"><h1>No internet</h1>
<p>Golden Seed needs the internet to open. Check the data or Wi-Fi, then press TRY AGAIN. Nothing you saved is lost.</p>
<button type="button" onclick="location.reload()">Try again</button></div></div></body></html>`;

self.addEventListener('install', () => { self.skipWaiting(); });
self.addEventListener('activate', (e) => {
    // remove any copies an older helper may have saved, then take charge of the open pages
    e.waitUntil(caches.keys().then((keys) => Promise.all(keys.map((k) => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (e) => {
    if (e.request.mode !== 'navigate' || e.request.method !== 'GET') return;   // files and API calls: the browser as usual
    e.respondWith(fetch(e.request).catch(() => new Response(OFFLINE, { headers: { 'content-type': 'text/html; charset=utf-8' } })));
});
