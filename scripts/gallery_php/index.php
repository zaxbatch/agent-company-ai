<?php
// Z-Dot Approval Gallery — dynamic: content from data/items.json, decisions server-side.
$stamp = gmdate('Y-m-d H:i \U\T\C');
?>
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>Z-Dot Approval Gallery</title>
<style>
:root{--bg:#0b0e14;--panel:#141924;--line:#232b3a;--tx:#e7ecf3;--dim:#8e9bb0;
--accent:#6db3f2;--ok:#2ecc71;--rv:#f1c40f;--no:#e74c3c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:30px 28px 16px;border-bottom:1px solid var(--line);
 position:sticky;top:0;background:rgba(11,14,20,.96);backdrop-filter:blur(8px);z-index:9}
h1{margin:0 0 4px;font-size:26px;letter-spacing:-.02em}
.sub{color:var(--dim);margin:0;font-size:13.5px}
nav{margin-top:13px;display:flex;gap:8px;flex-wrap:wrap}
nav a{color:var(--accent);text-decoration:none;border:1px solid var(--line);
 padding:4px 11px;border-radius:999px;font-size:13px}
nav a:hover{border-color:var(--accent)}
.bar{display:flex;gap:10px;align-items:center;margin-top:13px;flex-wrap:wrap}
.count{font-size:13px;color:var(--dim)}
.count b{color:var(--tx)}
input.who{background:#0f1420;border:1px solid var(--line);color:var(--tx);
 border-radius:7px;padding:6px 9px;font:13px inherit;width:150px}
button.act{background:transparent;border:1px solid var(--line);color:var(--accent);
 border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}
button.act:hover{border-color:var(--accent)}
main{padding:8px 28px 70px;max-width:1240px;margin:0 auto}
section{padding:24px 0;border-bottom:1px solid var(--line)}
section:last-child{border:0}
h2{margin:0 0 2px;font-size:20px}
.blurb{color:var(--dim);margin:0 0 15px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
 overflow:hidden;display:flex;flex-direction:column}
.card[data-decision="approve"]{border-color:var(--ok);box-shadow:0 0 0 1px var(--ok) inset}
.card[data-decision="revise"]{border-color:var(--rv);box-shadow:0 0 0 1px var(--rv) inset}
.card[data-decision="reject"]{border-color:var(--no);box-shadow:0 0 0 1px var(--no) inset}
.media{background:#0e121a;display:flex;align-items:center;justify-content:center;min-height:100px}
.media img,.media video{display:block;width:100%;max-height:300px;object-fit:contain}
.media audio{width:100%;padding:6px}
.body{padding:13px;display:flex;flex-direction:column;gap:8px;flex:1}
h3{margin:0;font-size:15px}
.meta{margin:0;color:var(--dim);font-size:12.5px}
details summary{cursor:pointer;color:var(--accent);font-size:12.5px}
.proof{font-size:12.5px;color:#b9c4d4;margin:6px 0 0}
.extra{margin:0;font-size:13px}.extra a{color:var(--accent);text-decoration:none}
.decide{display:flex;gap:6px;margin-top:auto;padding-top:6px}
.btn{flex:1;border:1px solid var(--line);background:#0f1420;color:var(--tx);
 border-radius:7px;padding:7px 6px;font-size:13px;cursor:pointer}
.btn:hover{background:#182133}
.btn.on.ok{background:var(--ok);border-color:var(--ok);color:#04180d;font-weight:600}
.btn.on.rv{background:var(--rv);border-color:var(--rv);color:#1c1503;font-weight:600}
.btn.on.no{background:var(--no);border-color:var(--no);color:#fff;font-weight:600}
.note{width:100%;background:#0f1420;border:1px solid var(--line);color:var(--tx);
 border-radius:7px;padding:7px;font:12.5px/1.4 inherit;resize:vertical}
.note:focus{outline:none;border-color:var(--accent)}
.stamp{margin:0;font-size:11.5px;color:var(--ok);min-height:15px}
footer{padding:20px 28px 40px;color:var(--dim);font-size:12.5px;border-top:1px solid var(--line)}
.err{color:#e74c3c;padding:20px;font-size:14px}
</style></head>
<body>
<header>
  <h1>Z-Dot Approval Gallery</h1>
  <p class="sub">Everything up for review. Decisions save to the server, so everyone sees the same thing.</p>
  <nav id="nav"></nav>
  <div class="bar">
    <span class="count" id="counts">loading…</span>
    <input class="who" id="who" placeholder="your name" />
    <button class="act" id="refresh">Refresh from live site</button>
    <button class="act" id="export">Export JSON</button>
    <button class="act" id="copy">Copy summary</button>
  </div>
</header>
<main id="main"><p class="err">Loading…</p></main>
<footer>
  Dynamic gallery · items served from the server manifest, decisions persisted server-side
  (<code>data/decisions.json</code>). "Refresh from live site" pulls new songs/doodles straight
  from the SnowSnakes API. Rendered <?php echo htmlspecialchars($stamp); ?>.
</footer>
<script>
const API = 'api.php';
let ITEMS = [], DEC = {};

const whoEl = document.getElementById('who');
whoEl.value = localStorage.getItem('zdot-who') || '';
whoEl.onchange = () => localStorage.setItem('zdot-who', whoEl.value.trim());

const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
  c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

function media(it){
  const u = esc(it.url);
  if (it.kind === 'audio') return `<audio controls preload="metadata" src="${u}"></audio>`;
  if (it.kind === 'video') return `<video controls preload="metadata" playsinline src="${u}"></video>`;
  if (it.kind === 'image') return `<a href="${u}" target="_blank" rel="noopener"><img loading="lazy" src="${u}" alt=""></a>`;
  return '';
}
function extraLinks(it){
  if (!it.extra || !it.extra.length) return '';
  return '<p class="extra">' + it.extra.map(([t,u]) =>
    `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(t)}</a>`).join(' · ') + '</p>';
}
function card(it){
  return `<article class="card" data-id="${esc(it.id)}">
  <div class="media">${media(it)}</div>
  <div class="body">
    <h3>${esc(it.title)}</h3>
    <p class="meta">${esc(it.meta)}</p>
    ${it.proof ? `<details><summary>verification</summary><p class="proof">${esc(it.proof)}</p></details>` : ''}
    ${extraLinks(it)}
    <div class="decide">
      <button class="btn ok" data-d="approve">Approve</button>
      <button class="btn rv" data-d="revise">Revise</button>
      <button class="btn no" data-d="reject">Reject</button>
    </div>
    <textarea class="note" rows="2" placeholder="Note (optional) — what to change or why"></textarea>
    <p class="stamp"></p>
  </div></article>`;
}

function render(){
  const cats = [];
  ITEMS.forEach(it => { if (!cats.includes(it.category)) cats.push(it.category); });
  document.getElementById('nav').innerHTML = cats.map(c => {
    const a = c.toLowerCase().replace(/[^a-z0-9]+/g,'-');
    return `<a href="#${a}">${esc(c)}</a>`;
  }).join('');
  document.getElementById('main').innerHTML = cats.map(c => {
    const a = c.toLowerCase().replace(/[^a-z0-9]+/g,'-');
    const items = ITEMS.filter(i => i.category === c);
    return `<section id="${a}"><h2>${esc(c)}</h2>
      <p class="blurb">${items.length} item${items.length===1?'':'s'}</p>
      <div class="grid">${items.map(card).join('')}</div></section>`;
  }).join('');
  wire();
  paint();
}

function paint(){
  const n = {approve:0, revise:0, reject:0};
  document.querySelectorAll('.card').forEach(card => {
    const id = card.dataset.id, rec = DEC[id] || {}, d = rec.decision;
    if (d) { card.dataset.decision = d; n[d]++; } else { delete card.dataset.decision; }
    card.querySelectorAll('.btn').forEach(b => b.classList.toggle('on', b.dataset.d === d));
    const ta = card.querySelector('.note');
    if (document.activeElement !== ta) ta.value = rec.note || '';
    card.querySelector('.stamp').textContent = d
      ? d.toUpperCase() + (rec.by ? ' · ' + rec.by : '') + (rec.at ? ' · ' + rec.at.slice(0,16).replace('T',' ') : '')
      : '';
  });
  const tot = n.approve + n.revise + n.reject;
  document.getElementById('counts').innerHTML = tot
    ? `<b>${n.approve}</b> approved · <b>${n.revise}</b> revise · <b>${n.reject}</b> rejected · <b>${tot}</b>/${ITEMS.length} decided`
    : `no decisions yet · ${ITEMS.length} items`;
}

async function save(id, decision, note){
  const body = {id, decision, note: note || '', by: whoEl.value.trim() || 'anon'};
  try {
    const r = await fetch(API + '?action=decide', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
    const j = await r.json();
    if (!j.ok) { alert('Save failed: ' + (j.error || r.status)); return; }
    if (decision) DEC[id] = {decision, note: body.note, by: body.by, at: new Date().toISOString()};
    else delete DEC[id];
    paint();
  } catch (e) { alert('Save failed: ' + e); }
}

function wire(){
  document.querySelectorAll('.card').forEach(card => {
    const id = card.dataset.id;
    card.querySelectorAll('.btn').forEach(b => {
      b.onclick = () => {
        const cur = (DEC[id] || {}).decision;
        const next = (cur === b.dataset.d) ? null : b.dataset.d;   // click again to clear
        save(id, next, card.querySelector('.note').value);
      };
    });
    card.querySelector('.note').onchange = e =>
      save(id, (DEC[id] || {}).decision, e.target.value);
  });
}

document.getElementById('refresh').onclick = async () => {
  const btn = document.getElementById('refresh');
  btn.disabled = true; btn.textContent = 'Refreshing…';
  try {
    const j = await (await fetch(API + '?action=refresh')).json();
    alert(j.ok ? `Added ${j.added} new item(s). Total ${j.total}.` : 'Refresh failed.');
    await load();
  } finally { btn.disabled = false; btn.textContent = 'Refresh from live site'; }
};

document.getElementById('export').onclick = async () => {
  const j = await (await fetch(API + '?action=decisions')).json();
  const rows = Object.entries(j).map(([id,v]) => ({
    id, decision: v.decision, note: v.note, by: v.by, at: v.at}));
  const b = new Blob([JSON.stringify({generated: new Date().toISOString(), decisions: rows}, null, 2)],
                     {type:'application/json'});
  const a = document.createElement('a'); a.href = URL.createObjectURL(b);
  a.download = 'zdot-gallery-decisions.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
};

document.getElementById('copy').onclick = async () => {
  const rows = ITEMS.map(it => {
    const r = DEC[it.id];
    return `${it.title}: ${r ? r.decision.toUpperCase() : 'undecided'}${r && r.note ? ' — ' + r.note : ''}`;
  });
  const txt = rows.join('\n');
  try { await navigator.clipboard.writeText(txt); alert('Copied:\n\n' + txt); }
  catch (e) { alert(txt); }
};

async function load(){
  ITEMS = await (await fetch(API + '?action=items')).json();
  DEC   = await (await fetch(API + '?action=decisions')).json();
  if (!Array.isArray(ITEMS) || !ITEMS.length) {
    document.getElementById('main').innerHTML =
      '<p class="err">No items in the manifest yet. Hit "Refresh from live site".</p>';
    document.getElementById('counts').textContent = 'no items';
    return;
  }
  render();
}
load();
</script>
</body></html>
