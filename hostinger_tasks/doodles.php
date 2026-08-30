<?php
// Z-Dot Doodle Gallery — approval app with comments.
// Auth-gated (same session as auth.php). Owner: NinjaNerd (CTO) · 2026-08-30.
session_start();
if (!isset($_SESSION['user'])) { header('Location: auth.html'); exit; }
$me = $_SESSION['user'];
function esc($s){ return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
$who = esc($me['username'] ?? ($me['member'] ?? 'team'));
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Z-Dot — Doodle Gallery</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; background:#0b1220; color:#dbe7ff; line-height:1.5; }
  .wrap { max-width:1240px; margin:0 auto; padding:22px 16px 70px; }
  header { text-align:center; padding:14px 0 4px; }
  header h1 { font-size:1.55rem; color:#fff; letter-spacing:1px; }
  header .tag { color:#7fd1ff; font-size:.8rem; letter-spacing:3px; margin-top:5px; }
  .nav { margin-top:12px; display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
  .nav a { background:#1565c0; color:#fff; text-decoration:none; padding:7px 14px; border-radius:8px; font-size:.82rem; }
  .nav a:hover { background:#1a6fd8; }
  .nav a.alt { background:#0e2a1e; border:1px solid #1f5a3f; color:#7ee2a8; }
  .who { background:#12395a; border:1px solid #2f5a8a; color:#9fd8ff; padding:7px 14px; border-radius:8px; font-size:.82rem; }
  .stats { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:18px; }
  .stat { border-radius:20px; padding:5px 14px; font-size:.78rem; border:1px solid #2f3a5a; background:#101d33; color:#a9c2e5; }
  .stat b { color:#fff; }
  .stat.s-all b{color:#fff} .stat.s-approved b{color:#7ee2a8} .stat.s-needs_changes b{color:#f0d97a}
  .stat.s-rejected b{color:#ff8f7a} .stat.s-pending b{color:#7fd1ff} .stat.s-notes b{color:#c9a7ff}
  .tools { display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin-top:14px; }
  .tools button, .tools a { background:#101d33; border:1px solid #2f3a5a; color:#9fd8ff; padding:7px 14px; border-radius:8px; font-size:.8rem; cursor:pointer; text-decoration:none; }
  .tools button:hover, .tools a:hover { background:#1a2c47; }
  .tabs { display:flex; gap:6px; justify-content:center; flex-wrap:wrap; margin-top:16px; }
  .tab { background:#101d33; border:1px solid #2f3a5a; color:#a9c2e5; padding:5px 13px; border-radius:18px; font-size:.78rem; cursor:pointer; }
  .tab.active { background:#1565c0; border-color:#1565c0; color:#fff; }
  .tab .n { opacity:.7; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; margin-top:18px; }
  .card { background:#101d33; border:1px solid #1f3a5f; border-radius:14px; overflow:hidden; display:flex; flex-direction:column; transition:border-color .2s, transform .1s; }
  .card:hover { border-color:#3a5a8a; transform:translateY(-1px); }
  .thumb { background:#0a1322; padding:10px; display:flex; align-items:center; justify-content:center; min-height:150px; cursor:pointer; }
  .thumb img { max-width:100%; max-height:150px; border-radius:6px; }
  .card-body { padding:10px 12px 12px; display:flex; flex-direction:column; gap:8px; flex:1; }
  .card-title { font-size:.85rem; color:#fff; font-weight:600; display:flex; justify-content:space-between; gap:8px; align-items:flex-start; }
  .badge { font-size:.62rem; font-weight:700; letter-spacing:1px; padding:3px 9px; border-radius:20px; white-space:nowrap; border:1px solid; flex-shrink:0; margin-top:1px; }
  .b-pending{background:#1c2433;color:#9fb3cc;border-color:#33405a}
  .b-approved{background:#0e2a1e;color:#7ee2a8;border-color:#1f5a3f}
  .b-needs_changes{background:#2a2413;color:#f0d97a;border-color:#5a4a2f}
  .b-rejected{background:#2a1212;color:#ff8f7a;border-color:#5a2f2f}
  .ccount { font-size:.72rem; color:#6f8db0; }
  .ccount b { color:#c9a7ff; }
  .actions { display:flex; gap:5px; margin-top:2px; }
  .actions button { flex:1; font-size:.72rem; padding:6px 4px; border-radius:7px; border:1px solid #2f3a5a; background:#0d1626; color:#a9c2e5; cursor:pointer; }
  .actions button:hover { background:#1a2c47; }
  .actions .aprove:hover{background:#0e2a1e;color:#7ee2a8;border-color:#1f5a3f}
  .actions .achg:hover{background:#2a2413;color:#f0d97a;border-color:#5a4a2f}
  .actions .arej:hover{background:#2a1212;color:#ff8f7a;border-color:#5a2f2f}
  .quick-note { display:flex; gap:5px; }
  .quick-note input { flex:1; background:#0d1626; border:1px solid #2f3a5a; color:#dbe7ff; padding:6px 8px; border-radius:7px; font-size:.75rem; }
  .quick-note input::placeholder{color:#5a7195}
  .quick-note button { background:#1565c0; border:none; color:#fff; border-radius:7px; padding:0 10px; font-size:.75rem; cursor:pointer; }
  .loading,.errbox,.empty { text-align:center; padding:40px 0; color:#6f8db0; font-size:.9rem; }
  .errbox{color:#ffb3a0}
  .empty{color:#5a7195}
  .updated { text-align:center; font-size:.7rem; color:#4a6385; margin-top:14px; }
  /* lightbox */
  .lb { position:fixed; inset:0; background:rgba(4,8,16,.93); display:none; align-items:center; justify-content:center; z-index:50; padding:14px; }
  .lb.open { display:flex; }
  .lb-box { background:#101d33; border:1px solid #2f4a7a; border-radius:16px; max-width:860px; width:100%; max-height:94vh; overflow-y:auto; padding:18px; }
  .lb-top { display:flex; justify-content:space-between; align-items:flex-start; gap:10px; }
  .lb-title { font-size:1.05rem; color:#fff; font-weight:700; }
  .lb-file { font-size:.72rem; color:#5a7195; margin-top:2px; }
  .lb-close { background:none; border:none; color:#7d8aa3; font-size:1.5rem; cursor:pointer; line-height:1; }
  .lb-close:hover { color:#fff; }
  .lb-img { background:#0a1322; border-radius:10px; margin:12px 0; display:flex; justify-content:center; padding:12px; }
  .lb-img img { max-width:100%; max-height:56vh; border-radius:8px; }
  .lb-nav { display:flex; gap:8px; margin-bottom:10px; }
  .lb-nav button { flex:1; background:#0d1626; border:1px solid #2f3a5a; color:#9fd8ff; border-radius:8px; padding:8px; cursor:pointer; font-size:.8rem; }
  .lb-nav button:hover { background:#1a2c47; }
  .lb-status-actions { display:flex; gap:6px; margin:10px 0; }
  .lb-status-actions button { flex:1; font-size:.8rem; padding:9px 6px; border-radius:8px; border:1px solid #2f3a5a; background:#0d1626; color:#a9c2e5; cursor:pointer; }
  .lb-status-actions button:hover{filter:brightness(1.3)}
  h4 { color:#7fd1ff; font-size:.8rem; letter-spacing:1.5px; margin:14px 0 8px; border-bottom:1px solid #1f3a5f; padding-bottom:6px; }
  .comment { border:1px solid #1f3a5f; border-radius:10px; padding:8px 11px; margin-bottom:8px; background:#0d1626; }
  .comment .cm-head { display:flex; justify-content:space-between; gap:8px; font-size:.7rem; color:#6f8db0; }
  .comment .cm-author { color:#9fd8ff; font-weight:600; }
  .comment .cm-text { margin-top:4px; font-size:.85rem; color:#dbe7ff; white-space:pre-wrap; word-break:break-word; }
  .comment .cm-del { background:none; border:none; color:#7a4a4a; cursor:pointer; font-size:.75rem; }
  .comment .cm-del:hover { color:#ff8f7a; }
  .no-comments { color:#5a7195; font-size:.8rem; font-style:italic; }
  .add-comment { display:flex; gap:6px; margin-top:6px; }
  .add-comment textarea { flex:1; background:#0d1626; border:1px solid #2f3a5a; color:#dbe7ff; border-radius:8px; padding:8px; font-size:.82rem; resize:vertical; min-height:52px; font-family:inherit; }
  .add-comment button { background:#1565c0; border:none; color:#fff; border-radius:8px; padding:0 14px; cursor:pointer; font-size:.8rem; }
  .add-comment button:hover { background:#1a6fd8; }
  .history { font-size:.68rem; color:#4a6385; margin-top:8px; }
  .history span { margin-right:10px; }
  .toast { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); background:#1565c0; color:#fff; padding:9px 18px; border-radius:20px; font-size:.8rem; z-index:99; opacity:0; transition:opacity .25s; pointer-events:none; }
  .toast.show { opacity:1; }
  /* notes panel */
  .notes-panel { display:none; margin-top:18px; }
  .notes-panel.open { display:block; }
  .notes-group { background:#101d33; border:1px solid #1f3a5f; border-radius:12px; padding:12px 14px; margin-bottom:10px; }
  .notes-group h3 { font-size:.88rem; color:#fff; display:flex; justify-content:space-between; gap:8px; align-items:center; }
  .notes-group .st { font-size:.62rem; }
  .notes-group ul { list-style:none; margin-top:6px; }
  .notes-group li { font-size:.82rem; color:#c6d6f2; padding:4px 0 4px 12px; border-left:2px solid #2f4a7a; margin-bottom:4px; }
  .notes-group li .meta { color:#5a7195; font-size:.7rem; }
  @media (max-width:560px){
    .grid { grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }
    .thumb { min-height:110px; }
    .thumb img { max-height:110px; }
    .card-title { font-size:.76rem; }
    .actions button { font-size:.66rem; padding:5px 2px; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>🎨 Z-DOT DOODLE GALLERY</h1>
    <div class="tag">APPROVAL + FEEDBACK · PRIVATE · TEAM ONLY</div>
    <div class="nav">
      <a href="index.html">📋 Task Dashboard</a>
      <a href="progress.php">📊 Progress</a>
      <a class="alt" href="doodle_api.php?action=export">⬇ Export Notes</a>
      <span class="who">🔒 <?php echo $who; ?></span>
    </div>
  </header>

  <div class="stats" id="stats"></div>

  <div class="tools">
    <button id="btn-notes">📝 Team Notes</button>
    <button id="btn-refresh">⟳ Refresh</button>
  </div>

  <div class="tabs" id="tabs"></div>

  <div id="grid" class="grid"><div class="loading">Loading doodles…</div></div>
  <div id="errbox" class="errbox" style="display:none"></div>
  <div id="empty" class="empty" style="display:none">No doodles in this filter.</div>

  <div class="notes-panel" id="notes-panel"></div>

  <div class="updated" id="updated"></div>
</div>

<!-- lightbox -->
<div class="lb" id="lb">
  <div class="lb-box">
    <div class="lb-top">
      <div>
        <div class="lb-title" id="lb-title"></div>
        <div class="lb-file" id="lb-file"></div>
      </div>
      <button class="lb-close" id="lb-close">✕</button>
    </div>
    <div class="lb-nav">
      <button id="lb-prev">← Prev</button>
      <button id="lb-next">Next →</button>
    </div>
    <div class="lb-img"><img id="lb-img" alt="doodle"></div>
    <div class="lb-status-actions" id="lb-actions"></div>
    <h4>💬 FEEDBACK / NOTES</h4>
    <div id="lb-comments"></div>
    <div class="add-comment">
      <textarea id="lb-comment-text" placeholder="What do you like / not like? What should change? (Zerric's notes drive the team)"></textarea>
      <button id="lb-comment-send">Add note</button>
    </div>
    <div class="history" id="lb-history"></div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
'use strict';
let STATE = { csrf:'', member:'', is_zerric:false, doodles:[], filtered:[], filter:'all', notesMode:false, currentIdx:-1 };
const STATUSES = ['pending','approved','needs_changes','rejected'];
const STATUS_LABEL = { pending:'PENDING', approved:'APPROVED', needs_changes:'NEEDS CHANGES', rejected:'REJECTED' };
const FILTERS = [
  {key:'all', label:'All'},
  {key:'pending', label:'Pending'},
  {key:'needs_changes', label:'Needs Changes'},
  {key:'approved', label:'Approved'},
  {key:'rejected', label:'Rejected'},
  {key:'notes', label:'With Notes'}
];

const $ = id => document.getElementById(id);
function esc(s){ const d=document.createElement('div'); d.textContent=String(s); return d.innerHTML; }
function toast(msg){ const t=$('toast'); t.textContent=msg; t.classList.add('show'); clearTimeout(t._h); t._h=setTimeout(()=>t.classList.remove('show'),2200); }

async function api(action, payload){
  const opts = { method:'GET', headers:{'Accept':'application/json'} };
  if (payload){
    opts.method='POST';
    opts.headers['Content-Type']='application/json';
    opts.headers['X-CSRF-Token']=STATE.csrf;
    opts.body=JSON.stringify(payload);
  }
  const r = await fetch('doodle_api.php?action='+encodeURIComponent(action), opts);
  const t = await r.text();
  let j=null; try{ j=t?JSON.parse(t):null; }catch(e){ j=null; }
  if (!r.ok) throw new Error((j&&j.error)||('HTTP '+r.status));
  return j;
}

// ── loading + rendering ────────────────────────────────────────────────
async function load(){
  try{
    const j = await api('list');
    STATE.csrf=j.csrf; STATE.member=j.member; STATE.is_zerric=!!j.is_zerric;
    STATE.doodles=j.doodles;
    applyFilter(); renderStats(); renderTabs(); renderGrid(); renderNotes();
    $('updated').textContent = 'updated '+(j.updated||j.server_time||'').replace('T',' ').replace('Z',' UTC');
    $('errbox').style.display='none';
  }catch(e){
    if (String(e.message).indexOf('401')>=0 || String(e.message).indexOf('not logged in')>=0){ window.location.href='auth.html'; return; }
    $('errbox').textContent='Error: '+e.message; $('errbox').style.display='block';
  }
}

function countOf(key){
  if (key==='all') return STATE.doodles.length;
  if (key==='notes') return STATE.doodles.filter(d=>d.comments.length>0).length;
  return STATE.doodles.filter(d=>d.status===key).length;
}
function applyFilter(){
  const f=STATE.filter;
  STATE.filtered = STATE.doodles.filter(d=>{
    if (f==='all') return true;
    if (f==='notes') return d.comments.length>0;
    return d.status===f;
  });
}
function renderStats(){
  const s=$('stats'); s.innerHTML='';
  const items=[
    ['all','TOTAL',countOf('all'),'s-all'],
    ['pending','PENDING',countOf('pending'),'s-pending'],
    ['needs_changes','NEEDS CHANGES',countOf('needs_changes'),'s-needs_changes'],
    ['approved','APPROVED',countOf('approved'),'s-approved'],
    ['rejected','REJECTED',countOf('rejected'),'s-rejected'],
    ['notes','NOTES',countOf('notes'),'s-notes']
  ];
  for (const [k,label,n,cls] of items){
    const el=document.createElement('span');
    el.className='stat '+cls;
    el.innerHTML='<b>'+n+'</b> '+label;
    s.appendChild(el);
  }
}
function renderTabs(){
  const t=$('tabs'); t.innerHTML='';
  for (const f of FILTERS){
    const b=document.createElement('button');
    b.className='tab'+(STATE.filter===f.key?' active':'');
    b.textContent=f.label+' ('+countOf(f.key)+')';
    b.onclick=()=>{ STATE.filter=f.key; STATE.notesMode=false; $('notes-panel').classList.remove('open'); $('btn-notes').textContent='📝 Team Notes'; renderTabs(); applyFilter(); renderGrid(); };
    t.appendChild(b);
  }
}
function statusBadge(st){
  return '<span class="badge b-'+st+'">'+STATUS_LABEL[st]+'</span>';
}
function renderGrid(){
  const g=$('grid'); g.innerHTML='';
  $('empty').style.display = STATE.filtered.length?'none':'block';
  STATE.filtered.forEach((d,idx)=>{
    const card=document.createElement('div');
    card.className='card';
    const realIdx = STATE.doodles.indexOf(d);
    card.innerHTML =
      '<div class="thumb"><img loading="lazy" src="doodle_media/'+esc(d.file)+'" alt="'+esc(d.title)+'"></div>'+
      '<div class="card-body">'+
        '<div class="card-title"><span>'+esc(d.title)+'</span>'+statusBadge(d.status)+'</div>'+
        '<div class="ccount">💬 <b>'+d.comments.length+'</b> note'+(d.comments.length===1?'':'s')+'</div>'+
        '<div class="actions">'+
          '<button data-st="approved" class="aprove">✅ Approve</button>'+
          '<button data-st="needs_changes" class="achg">🔁 Fix</button>'+
          '<button data-st="rejected" class="arej">❌ Reject</button>'+
        '</div>'+
        '<div class="quick-note"><input placeholder="Quick note…" data-note><button data-note-send>Add</button></div>'+
      '</div>';
    card.querySelector('.thumb').onclick=()=>openLightbox(realIdx);
    card.querySelectorAll('.actions button').forEach(btn=>{
      btn.onclick=async ()=>{ await setStatus(d, btn.dataset.st); };
    });
    const inp=card.querySelector('[data-note]');
    const send=card.querySelector('[data-note-send]');
    const doNote=async ()=>{ const t=inp.value.trim(); if(!t) return; try{ await api('comment',{id:d.file,text:t}); inp.value=''; toast('Note added'); load(); }catch(e){ toast(e.message); } };
    send.onclick=doNote; inp.onkeydown=e=>{ if(e.key==='Enter') doNote(); };
  });
}
async function setStatus(d, st){
  try{
    await api('set_status',{id:d.file,status:st});
    d.status=st; toast('Marked: '+STATUS_LABEL[st]);
    load();
  }catch(e){ toast(e.message); }
}

// ── lightbox ────────────────────────────────────────────────────────────
function openLightbox(idx){
  STATE.currentIdx=idx;
  const d=STATE.doodles[idx];
  $('lb').classList.add('open');
  $('lb-title').textContent=d.title;
  $('lb-file').textContent=d.file;
  $('lb-img').src='doodle_media/'+encodeURIComponent(d.file);
  renderLbActions(); renderLbComments(); renderLbHistory();
}
function closeLightbox(){ $('lb').classList.remove('open'); STATE.currentIdx=-1; }
function stepLb(dir){
  if (STATE.currentIdx<0) return;
  let i=STATE.currentIdx+dir;
  if (i<0) i=STATE.doodles.length-1;
  if (i>=STATE.doodles.length) i=0;
  openLightbox(i);
}
function renderLbActions(){
  const d=STATE.doodles[STATE.currentIdx];
  const box=$('lb-actions'); box.innerHTML='';
  for (const st of STATUSES){
    const b=document.createElement('button');
    b.textContent=(st==='approved'?'✅ ':st==='needs_changes'?'🔁 ':st==='rejected'?'❌ ':'⏳ ')+STATUS_LABEL[st];
    if (d.status===st) b.style.outline='2px solid #7fd1ff';
    b.onclick=async ()=>{ try{ await api('set_status',{id:d.file,status:st}); toast('Marked: '+STATUS_LABEL[st]); load(); }catch(e){ toast(e.message); } };
    box.appendChild(b);
  }
}
function renderLbComments(){
  const d=STATE.doodles[STATE.currentIdx];
  const box=$('lb-comments'); box.innerHTML='';
  if (!d.comments.length){ const p=document.createElement('div'); p.className='no-comments'; p.textContent='No notes yet. Add the first one below.'; box.appendChild(p); return; }
  d.comments.forEach((c,i)=>{
    const el=document.createElement('div'); el.className='comment';
    const head=document.createElement('div'); head.className='cm-head';
    const who=document.createElement('span'); who.className='cm-author'; who.textContent=c.author+' · '+(c.ts||'').replace('T',' ').replace('Z','');
    head.appendChild(who);
    const canDel=(c.author===STATE.member)||STATE.is_zerric;
    if (canDel){
      const del=document.createElement('button'); del.className='cm-del'; del.textContent='✕';
      del.onclick=async ()=>{ try{ await api('delete_comment',{id:d.file,idx:i}); toast('Note deleted'); load(); }catch(e){ toast(e.message); } };
      head.appendChild(del);
    }
    const txt=document.createElement('div'); txt.className='cm-text'; txt.textContent=c.text;
    el.appendChild(head); el.appendChild(txt); box.appendChild(el);
  });
}
function renderLbHistory(){
  const d=STATE.doodles[STATE.currentIdx];
  const h=$('lb-history'); h.innerHTML='';
  (d.history||[]).forEach(ev=>{
    const s=document.createElement('span');
    s.textContent=ev.who+' '+(ev.action||'')+' · '+(ev.ts||'').replace('T',' ').replace('Z','');
    h.appendChild(s);
  });
}
$('lb-close').onclick=closeLightbox;
$('lb-prev').onclick=()=>stepLb(-1);
$('lb-next').onclick=()=>stepLb(1);
$('lb').addEventListener('click',e=>{ if(e.target===$('lb')) closeLightbox(); });
$('lb-comment-send').onclick=async ()=>{
  const d=STATE.doodles[STATE.currentIdx];
  const t=$('lb-comment-text').value.trim();
  if(!t) return;
  try{ await api('comment',{id:d.file,text:t}); $('lb-comment-text').value=''; toast('Note added'); load(); }catch(e){ toast(e.message); }
};
document.addEventListener('keydown',e=>{
  if ($('lb').classList.contains('open')){
    if (e.key==='Escape') closeLightbox();
    else if (e.key==='ArrowLeft') stepLb(-1);
    else if (e.key==='ArrowRight') stepLb(1);
  }
});

// ── team notes panel ─────────────────────────────────────────────────────
function renderNotes(){
  const p=$('notes-panel'); p.innerHTML='';
  const withNotes = STATE.doodles.filter(d=>d.comments.length>0).slice().reverse();
  if (!withNotes.length){
    p.innerHTML='<div class="empty">No notes yet — once Zerric (or anyone) adds feedback it shows up here grouped by doodle.</div>';
    return;
  }
  for (const d of withNotes){
    const g=document.createElement('div'); g.className='notes-group';
    const h=document.createElement('h3');
    h.innerHTML='<span>'+esc(d.title)+'</span>'+statusBadge(d.status);
    const ul=document.createElement('ul');
    d.comments.slice().reverse().forEach(c=>{
      const li=document.createElement('li');
      const m=document.createElement('div'); m.className='meta';
      m.textContent=c.author+' · '+(c.ts||'').replace('T',' ').replace('Z','');
      const tx=document.createElement('div'); tx.textContent=c.text;
      li.appendChild(m); li.appendChild(tx); ul.appendChild(li);
    });
    g.appendChild(h); g.appendChild(ul); p.appendChild(g);
  }
}
$('btn-notes').onclick=()=>{
  STATE.notesMode=!STATE.notesMode;
  const p=$('notes-panel'); p.classList.toggle('open', STATE.notesMode);
  $('btn-notes').textContent = STATE.notesMode ? '🗂 Close Notes' : '📝 Team Notes';
  if (STATE.notesMode) renderNotes();
};
$('btn-refresh').onclick=()=>{ load(); toast('Refreshed'); };

load();
setInterval(()=>{ if (!$('lb').classList.contains('open')) load(); }, 60000);
</script>
</body>
</html>
