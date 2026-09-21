const SHELL_CACHE='ngl-shell-v231';
const OFFLINE_COVER_CACHE='ngl-manual-covers-v1';
const SHELL=['./','index.html','styles.css','app.js','manifest.webmanifest','data/games.json','data/tier-order.json','icons/icon-192.png','icons/icon-512.png','icons/icon-maskable-512.png','branding/ngl-logo.png','console-images/nintendo-switch.jpg','console-images/nintendo-switch-2.jpg','console-images/super-nintendo.jpg','console-images/nintendo-wii.jpg','console-images/nintendo-wii-u.jpg','console-images/game-boy.jpg','console-images/nintendo-gamecube.jpg'];
self.addEventListener('install',e=>e.waitUntil(caches.open(SHELL_CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith('ngl-shell-')&&k!==SHELL_CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  if(url.pathname.includes('/covers/')){
    e.respondWith(fetch(e.request).catch(async()=>{
      const c=await caches.open(OFFLINE_COVER_CACHE);
      return (await c.match(e.request)) || Response.error();
    }));
    return;
  }
  e.respondWith(fetch(e.request,{cache:'no-store'}).then(res=>{
    if(res.ok){const copy=res.clone();caches.open(SHELL_CACHE).then(c=>c.put(e.request,copy));}
    return res;
  }).catch(()=>caches.match(e.request).then(r=>r||caches.match('index.html'))));
});
