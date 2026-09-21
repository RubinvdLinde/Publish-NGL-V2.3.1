const STATE_KEY='ngl-user-state-v1';
const LEGACY_STATE_KEYS=['ngl-state-v21','ngl-state-v2','ngl-state-v1'];
const APP_VERSION='2.3.1';
const TIERS=['S','A','B','C','D','E','U'];
const TIER_COLORS={S:'#ff747d',A:'#ffad63',B:'#ffd45f',C:'#bce66b',D:'#69d89f',E:'#72cfff',U:'#cfd4dc'};
const CONSOLE_IMAGES={"Nintendo Switch": "console-images/nintendo-switch.jpg", "Nintendo Switch 2": "console-images/nintendo-switch-2.jpg", "Super Nintendo": "console-images/super-nintendo.jpg", "Nintendo Wii": "console-images/nintendo-wii.jpg", "Nintendo Wii U": "console-images/nintendo-wii-u.jpg", "Game Boy": "console-images/game-boy.jpg", "Nintendo GameCube": "console-images/nintendo-gamecube.jpg"};
let baseGames=[];
let state={overrides:{},tierOrder:{S:[],A:[],B:[],C:[],D:[],E:[],U:[]},customGames:[],recent:[]};
let currentView='home';
let backlogMode='unplayed';
let deferredInstall=null;

const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const encodePath=s=>encodeURIComponent(s).replace(/%2F/g,'/');
const statusName=s=>({unplayed:'Not Played',playing:'Have Played',played:'Finished',dropped:'Stopped'}[s]||s);

function toast(msg){const t=$('#toast');t.textContent=msg;t.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>t.classList.remove('show'),1800)}
function loadState(){try{let raw=localStorage.getItem(STATE_KEY);if(!raw){for(const k of LEGACY_STATE_KEYS){raw=localStorage.getItem(k);if(raw){localStorage.setItem(STATE_KEY,raw);break}}}const x=raw?JSON.parse(raw):null;if(x)state={...state,...x,tierOrder:{...state.tierOrder,...(x.tierOrder||{})}}}catch(e){console.warn(e)}}
function saveState(){localStorage.setItem(STATE_KEY,JSON.stringify(state))}
function allRawGames(){return [...baseGames,...state.customGames]}
function normalizeState(){
  const ids=new Set(allRawGames().map(g=>String(g.id))), seen=new Set();
  const next={S:[],A:[],B:[],C:[],D:[],E:[],U:[]};
  for(const t of TIERS){for(const id of state.tierOrder[t]||[]){const sid=String(id);if(ids.has(sid)&&!seen.has(sid)){next[t].push(sid);seen.add(sid)}}}
  for(const id of ids)if(!seen.has(id))next.U.push(id);
  state.tierOrder=next;
  for(const id of Object.keys(state.overrides||{}))if(!ids.has(String(id)))delete state.overrides[id];
  saveState();
}
function tierOf(id){id=String(id);return TIERS.find(t=>(state.tierOrder[t]||[]).includes(id))||'U'}
function gameById(id){id=String(id);const raw=allRawGames().find(g=>String(g.id)===id);if(!raw)return null;const ov=state.overrides[id]||{};return {...raw,...ov,id,tier:tierOf(id)}}
function allGames(){return allRawGames().map(g=>gameById(g.id))}
function coverUrl(g){return g.coverData|| (g.cover?`covers/${encodePath(g.cover)}?cv=${encodeURIComponent(g.coverVersion||APP_VERSION)}`:`icons/icon-512.png?v=${APP_VERSION}`)}
function moveToTier(id,tier,beforeId=null){
  id=String(id);tier=TIERS.includes(tier)?tier:'U';
  for(const t of TIERS)state.tierOrder[t]=(state.tierOrder[t]||[]).filter(x=>String(x)!==id);
  const arr=state.tierOrder[tier];
  if(beforeId){const idx=arr.indexOf(String(beforeId));idx>=0?arr.splice(idx,0,id):arr.push(id)}else arr.push(id);
  saveState();renderAll();
}
function setOverride(id,patch){id=String(id);state.overrides[id]={...(state.overrides[id]||{}),...patch};state.recent=[id,...(state.recent||[]).filter(x=>x!==id)].slice(0,20);saveState()}

function stat(label,val){return `<div class="stat"><strong>${esc(val)}</strong><span>${esc(label)}</span></div>`}
function miniCard(g){return `<article class="mini-card" data-open-game="${esc(g.id)}" title="${esc(g.title)}"><img src="${coverUrl(g)}" alt="${esc(g.title)}"><b>${esc(g.title)}</b><small>${g.score!=null?`Your score ${g.score}`:esc(g.platformCode||g.platform)}</small></article>`}
function gameCard(g){return `<article class="game-card" data-open-game="${esc(g.id)}"><img loading="lazy" src="${coverUrl(g)}" alt="${esc(g.title)}">${g.score!=null?`<span class="score-badge">${g.score}</span>`:''}<span class="format-badge">${g.format==='Physical'?'P':g.format==='Digital'?'D':'?'}</span><h3>${esc(g.title)}</h3><p>${esc(g.platformCode||g.platform)} · ${esc(statusName(g.status))}</p></article>`}

function renderHome(){
  const games=allGames();
  const playedAny=games.filter(g=>g.status!=='unplayed').length;
  const finished=games.filter(g=>g.status==='played').length;
  const unplayed=games.filter(g=>g.status==='unplayed').length;
  const physical=games.filter(g=>g.format==='Physical').length;
  $('#homeStats').innerHTML=stat('Games',games.length)+stat('Played',playedAny)+stat('Finished',finished)+stat('Physical',physical);

  const playing=games.filter(g=>g.status==='playing');
  $('#playingStrip').innerHTML=playing.length?playing.map(miniCard).join(''):'<div class="empty">Nothing marked as Have Played.</div>';

  const top=games.filter(g=>Number.isFinite(g.score)).sort((a,b)=>b.score-a.score||Number(a.id)-Number(b.id)).slice(0,12);
  $('#topStrip').innerHTML=top.map(miniCard).join('');

  const byConsole={};
  games.forEach(g=>{
    const key=g.platform;
    if(!byConsole[key])byConsole[key]={total:0,played:0,finished:0};
    byConsole[key].total++;
    if(g.status!=='unplayed')byConsole[key].played++;
    if(g.status==='played')byConsole[key].finished++;
  });

  const platformOrder=['Nintendo Switch','Nintendo Switch 2','Nintendo GameCube','Nintendo Wii','Nintendo Wii U','Super Nintendo','Game Boy'];
  $('#consoleProgress').innerHTML=platformOrder.filter(p=>byConsole[p]).map(p=>{
    const x=byConsole[p], pct=x.total?Math.round(x.played/x.total*100):0;
    const img=(CONSOLE_IMAGES[p]||'icons/icon-512.png')+`?v=${APP_VERSION}`;
    return `<article class="console-progress-card">
      <div class="console-art"><img src="${img}" alt="${esc(p)}"></div>
      <div class="console-card-body">
        <div class="console-card-title"><h3>${esc(p)}</h3><strong>${x.played}/${x.total}</strong></div>
        <div class="console-progress-track"><i style="width:${pct}%"></i></div>
        <div class="console-card-meta"><span>${pct}% played</span><span>${x.finished} finished</span></div>
      </div>
    </article>`;
  }).join('');

  const counts={};
  games.forEach(g=>counts[g.platform]=(counts[g.platform]||0)+1);
  const max=Math.max(...Object.values(counts),1);
  $('#platformBreakdown').innerHTML=Object.entries(counts).sort((a,b)=>b[1]-a[1]).map(([p,n])=>`<div class="break-row"><span>${esc(p)}</span><div class="bar"><i style="width:${n/max*100}%"></i></div><b>${n}</b></div>`).join('');
  bindOpenGame();
}
function populatePlatformFilter(){const s=$('#platformFilter'),cur=s.value;const platforms=[...new Set(allGames().map(g=>g.platform))].sort();s.innerHTML='<option value="">All platforms</option>'+platforms.map(p=>`<option ${p===cur?'selected':''}>${esc(p)}</option>`).join('')}
function renderLibrary(){
  populatePlatformFilter();let games=allGames();const q=$('#librarySearch').value.trim().toLowerCase(),p=$('#platformFilter').value,st=$('#statusFilter').value,fmt=$('#formatFilter').value,sort=$('#sortFilter').value;
  games=games.filter(g=>(!q||g.title.toLowerCase().includes(q))&&(!p||g.platform===p)&&(!st||g.status===st)&&(!fmt||g.format===fmt));
  if(sort==='title')games.sort((a,b)=>a.title.localeCompare(b.title));else if(sort==='score-desc')games.sort((a,b)=>(b.score??-1)-(a.score??-1)||a.title.localeCompare(b.title));else if(sort==='meta-desc')games.sort((a,b)=>(b.metaScore??-1)-(a.metaScore??-1)||a.title.localeCompare(b.title));else games.sort((a,b)=>Number(a.id)-Number(b.id));
  $('#libraryCount').textContent=`${games.length} game${games.length===1?'':'s'}`;$('#libraryGrid').innerHTML=games.map(gameCard).join('');bindOpenGame();
}
function renderBacklog(){
  const games=allGames(),u=games.filter(g=>g.status==='unplayed').length,p=games.filter(g=>g.status==='playing').length,d=games.filter(g=>g.status==='dropped').length;
  $('#backlogStats').innerHTML=stat('Not Played',u)+stat('Have Played',p)+stat('Stopped',d);$$('#backlogTabs button').forEach(b=>b.classList.toggle('active',b.dataset.backlog===backlogMode));
  const list=games.filter(g=>g.status===backlogMode).sort((a,b)=>(b.metaScore??-1)-(a.metaScore??-1)||a.title.localeCompare(b.title));$('#backlogGrid').innerHTML=list.length?list.map(gameCard).join(''):'<div class="empty">No games here.</div>';bindOpenGame();
}
function renderTier(){
  const board=$('#tierBoard');let html='';
  for(const t of TIERS){const ids=state.tierOrder[t]||[];html+=`<section class="tier-row"><div class="tier-label" style="background:${TIER_COLORS[t]}">${t==='U'?'U':t}</div><div class="tier-zone" data-tier="${t}">`;ids.forEach((id,i)=>{const g=gameById(id);if(!g)return;html+=`<div class="tier-card" data-tier-game="${esc(id)}" title="${esc(g.title)}"><img draggable="false" src="${coverUrl(g)}" alt="${esc(g.title)}">${t!=='U'?`<span class="tier-rank">#${i+1}</span>`:''}</div>`});html+='</div></section>'}
  board.innerHTML=html;const ranked=TIERS.filter(t=>t!=='U').reduce((n,t)=>n+state.tierOrder[t].length,0);$('#rankedCount').textContent=`${ranked}/${allGames().length} ranked`;bindTierDrag();
}
function renderAll(){renderHome();renderLibrary();renderTier();renderBacklog()}

function bindOpenGame(){$$('[data-open-game]').forEach(el=>el.onclick=()=>openGame(el.dataset.openGame))}
function openGame(id){
  const g=gameById(id);if(!g)return;const dlg=$('#gameDialog');
  $('#gameDialogContent').innerHTML=`<div class="game-detail-head"><img src="${coverUrl(g)}" alt=""><div><p class="eyebrow">${esc(g.platform)}</p><h2>${esc(g.title)}</h2><div class="meta-line"><span class="tag">${esc(g.format)}</span>${g.metaScore!=null?`<span class="tag">Meta ${g.metaScore}</span>`:''}<span class="tag">Tier ${g.tier}</span>${g.timePlayed!=null?`<span class="tag">${g.timePlayed}h played</span>`:''}</div>${(g.mainExtra!=null||g.completionist!=null)?`<div class="time-summary">${g.mainExtra!=null?`<span><b>${g.mainExtra}h</b>Main + Extra</span>`:''}${g.completionist!=null?`<span><b>${g.completionist}h</b>Completionist</span>`:''}</div>`:''}</div></div><div class="form-grid"><label>My score<input id="editScore" type="number" min="0" max="100" value="${g.score??''}" placeholder="0–100"></label><label>Status<select id="editStatus">${['unplayed','playing','played','dropped'].map(s=>`<option value="${s}" ${g.status===s?'selected':''}>${statusName(s)}</option>`).join('')}</select></label><label>Format<select id="editFormat">${['Physical','Digital','Unknown'].map(x=>`<option ${g.format===x?'selected':''}>${x}</option>`).join('')}</select></label><label>Tier<select id="editTier">${TIERS.map(t=>`<option value="${t}" ${g.tier===t?'selected':''}>${t==='U'?'Unranked':t}</option>`).join('')}</select></label><label class="full">Notes<textarea id="editNotes" rows="3" placeholder="Your notes…">${esc(g.notes||'')}</textarea></label></div><div class="dialog-actions">${g.custom?'<button type="button" id="deleteCustom" class="ghost">Delete</button>':''}<button type="button" id="closeGame" class="ghost">Cancel</button><button type="button" id="saveGame" class="primary">Save</button></div>`;
  $('#closeGame').onclick=()=>dlg.close();$('#saveGame').onclick=()=>{const raw=$('#editScore').value.trim();const score=raw===''?null:Math.max(0,Math.min(100,Number(raw)));setOverride(id,{score,status:$('#editStatus').value,format:$('#editFormat').value,notes:$('#editNotes').value});const nt=$('#editTier').value;if(nt!==g.tier)moveToTier(id,nt);else renderAll();dlg.close();toast('Game updated')};
  if($('#deleteCustom'))$('#deleteCustom').onclick=()=>{if(confirm('Delete this custom game?')){state.customGames=state.customGames.filter(x=>String(x.id)!==String(id));for(const t of TIERS)state.tierOrder[t]=state.tierOrder[t].filter(x=>String(x)!==String(id));delete state.overrides[id];saveState();dlg.close();renderAll();toast('Game deleted')}};
  dlg.showModal();
}

function bindTierDrag(){
  $$('.tier-card').forEach(card=>card.addEventListener('pointerdown',e=>startTierPointer(e,card)));
}
function startTierPointer(e,card){
  if(e.button!==undefined&&e.button!==0)return;const id=card.dataset.tierGame,startX=e.clientX,startY=e.clientY,startTime=Date.now();let active=false,ghost=null,targetCard=null,targetZone=null;
  card.setPointerCapture?.(e.pointerId);
  const clearMarks=()=>{$$('.drop-before').forEach(x=>x.classList.remove('drop-before'));$$('.drop-zone').forEach(x=>x.classList.remove('drop-zone'))};
  const move=ev=>{const dist=Math.hypot(ev.clientX-startX,ev.clientY-startY);if(!active&&dist<8)return;if(!active){active=true;card.classList.add('drag-source');ghost=card.querySelector('img').cloneNode();ghost.className='drag-ghost';document.body.appendChild(ghost)}ev.preventDefault();ghost.style.left=ev.clientX+'px';ghost.style.top=ev.clientY+'px';clearMarks();const el=document.elementFromPoint(ev.clientX,ev.clientY);targetCard=el?.closest?.('.tier-card');targetZone=el?.closest?.('.tier-zone');if(targetCard&&targetCard!==card){targetCard.classList.add('drop-before');targetZone=targetCard.closest('.tier-zone')}else if(targetZone)targetZone.classList.add('drop-zone')};
  const up=ev=>{document.removeEventListener('pointermove',move,{capture:true});document.removeEventListener('pointerup',up,{capture:true});document.removeEventListener('pointercancel',up,{capture:true});clearMarks();card.classList.remove('drag-source');ghost?.remove();if(active&&targetZone){moveToTier(id,targetZone.dataset.tier,targetCard&&targetCard!==card?targetCard.dataset.tierGame:null)}else if(!active&&Date.now()-startTime<500){openGame(id)}};
  document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',up,{capture:true});document.addEventListener('pointercancel',up,{capture:true});
}

function showView(name){currentView=name;$$('.view').forEach(v=>v.classList.toggle('active',v.id===`view-${name}`));$$('.nav-btn').forEach(b=>b.classList.toggle('active',b.dataset.view===name));window.scrollTo({top:0,behavior:'smooth'})}
function exportBackup(){const payload={app:'Nintendo Games Library',version:3,exportedAt:new Date().toISOString(),state};const blob=new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`NGL-backup-${new Date().toISOString().slice(0,10)}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);toast('Backup exported')}
async function importBackup(file){try{const obj=JSON.parse(await file.text());const incoming=obj.state||obj;if(!incoming.tierOrder)throw new Error();state={...state,...incoming,tierOrder:{...state.tierOrder,...incoming.tierOrder}};normalizeState();renderAll();toast('Backup imported')}catch{alert('That file is not a valid NGL backup.')}}
async function cacheAllCovers(){
  if(!('caches'in window)){toast('Offline cache unavailable');return}
  const btn=$('#offlineBtn');btn.disabled=true;
  const games=baseGames.filter(g=>g.cover);
  try{
    const cache=await caches.open('ngl-manual-covers-v1');let done=0;
    for(const g of games){
      const url=coverUrl(g);
      try{const r=await fetch(url,{cache:'no-store'});if(r.ok)await cache.put(url,r.clone())}catch{}
      done++;if(done%10===0)btn.textContent=`Downloading ${done}/${games.length}…`;
    }
    btn.textContent='All covers downloaded for offline use';toast('Offline covers ready');
  }finally{btn.disabled=false}
}
async function clearOfflineCovers(){
  if('caches'in window)await caches.delete('ngl-manual-covers-v1');
  $('#offlineBtn').textContent='Download all covers for offline use (~121 MB)';
  toast('Offline covers removed');
}

function bindStaticEvents(){
  $$('.nav-btn').forEach(b=>b.onclick=()=>showView(b.dataset.view));$$('[data-nav]').forEach(b=>b.onclick=()=>showView(b.dataset.nav));
  ['librarySearch','platformFilter','statusFilter','formatFilter','sortFilter'].forEach(id=>$('#'+id).addEventListener(id==='librarySearch'?'input':'change',renderLibrary));
  $$('#backlogTabs button').forEach(b=>b.onclick=()=>{backlogMode=b.dataset.backlog;renderBacklog()});
  $('#settingsBtn').onclick=()=>$('#settingsDialog').showModal();$$('[data-close]').forEach(b=>b.onclick=()=>$('#'+b.dataset.close).close());
  $('#exportBtn').onclick=exportBackup;$('#importInput').onchange=e=>{if(e.target.files[0])importBackup(e.target.files[0]);e.target.value=''};$('#offlineBtn').onclick=cacheAllCovers;$('#clearOfflineBtn').onclick=clearOfflineCovers;
  $('#resetBtn').onclick=()=>{if(confirm('Reset all scores/status edits, custom games and tier rankings to the original library?')){localStorage.removeItem(STATE_KEY);location.reload()}};
  window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredInstall=e;$('#installBtn').classList.remove('hidden')});$('#installBtn').onclick=async()=>{if(deferredInstall){deferredInstall.prompt();await deferredInstall.userChoice;deferredInstall=null;$('#installBtn').classList.add('hidden')}};
}

const SPLASH_MIN_MS=1250;
const splashStarted=performance.now();
function dismissSplash(){
  const splash=$('#splashScreen');if(!splash)return;
  const wait=Math.max(0,SPLASH_MIN_MS-(performance.now()-splashStarted));
  setTimeout(()=>{splash.classList.add('hide');setTimeout(()=>splash.remove(),420)},wait);
}

async function init(){
  const [gamesResp,tierResp]=await Promise.all([
    fetch(`data/games.json?v=${APP_VERSION}`,{cache:'no-store'}),
    fetch(`data/tier-order.json?v=${APP_VERSION}`,{cache:'no-store'})
  ]);
  baseGames=await gamesResp.json();
  const initialTierOrder=await tierResp.json();
  const hadSavedState=!!localStorage.getItem(STATE_KEY)||LEGACY_STATE_KEYS.some(k=>!!localStorage.getItem(k));
  loadState();
  if(!hadSavedState){
    state.tierOrder={S:[],A:[],B:[],C:[],D:[],E:[],U:[],...initialTierOrder};
  }
  normalizeState();bindStaticEvents();renderAll();dismissSplash();
  // During laptop testing over plain HTTP, deliberately do not register a service worker.
  // This prevents an older local NGL version from serving stale files.
  // The service worker is enabled only on HTTPS, which is what the installed phone PWA will use.
  if('serviceWorker' in navigator){
    if(location.protocol==='https:'){
      navigator.serviceWorker.register(`sw.js?v=${APP_VERSION}`).catch(console.warn);
    }else if(location.hostname==='localhost'||location.hostname==='127.0.0.1'){
      navigator.serviceWorker.getRegistrations().then(rs=>rs.forEach(r=>r.unregister())).catch(()=>{});
    }
  }
}
init().catch(err=>{
  console.error(err);
  document.querySelector('#splashScreen')?.remove();
  const message=err&&err.message?err.message:String(err);
  document.body.innerHTML=`<main style="padding:30px;color:white;font-family:system-ui;background:#0d121c;min-height:100vh">
    <h1>NGL could not start</h1>
    <p>The app is being served, but one of its files could not be loaded.</p>
    <p style="color:#ffb4b4"><strong>Technical detail:</strong> ${esc(message)}</p>
    <p>Close this window and start <code>start_ngl_windows.bat</code> again. V2.3.1 uses port 8783 to avoid old browser caches.</p>
  </main>`;
});
