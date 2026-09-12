#!/usr/bin/env python3
"""Build the approval gallery: every asset up for review, with decisions.

Each item gets Approve / Revise / Reject plus a note. Decisions and notes are
kept in localStorage (keyed by item id) so the page is static but stateful, and
can be exported as JSON to push into the checklist portal.

    scripts/build_approval_gallery.py --outdir /tmp/gallery
"""
from __future__ import annotations
import argparse, datetime, html, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gallery_items import ITEMS, CATEGORY_ORDER


def e(s):
    return html.escape(str(s or ""), quote=True)


def media(item):
    k, u = item["kind"], item["url"]
    if k == "audio":
        return f'<audio controls preload="metadata" src="{e(u)}"></audio>'
    if k == "video":
        return f'<video controls preload="metadata" playsinline src="{e(u)}"></video>'
    if k == "image":
        return f'<a href="{e(u)}" target="_blank" rel="noopener"><img loading="lazy" src="{e(u)}" alt=""></a>'
    return ""


def card(item):
    extra = ""
    if item.get("extra"):
        extra = " · ".join(
            f'<a href="{e(u)}" target="_blank" rel="noopener">{e(t)}</a>'
            for t, u in item["extra"])
    return f'''<article class="card" data-id="{e(item['id'])}">
  <div class="media">{media(item)}</div>
  <div class="body">
    <h3>{e(item['title'])}</h3>
    <p class="meta">{e(item['meta'])}</p>
    <details><summary>verification</summary><p class="proof">{e(item['proof'])}</p></details>
    {f'<p class="extra">{extra}</p>' if extra else ''}
    <div class="decide">
      <button class="btn ok" data-d="approve">Approve</button>
      <button class="btn rv" data-d="revise">Revise</button>
      <button class="btn no" data-d="reject">Reject</button>
    </div>
    <textarea class="note" rows="2" placeholder="Note (optional) — what to change or why"></textarea>
    <p class="stamp"></p>
  </div>
</article>'''


def build():
    sections = []
    for cat in CATEGORY_ORDER:
        items = [i for i in ITEMS if i["category"] == cat]
        if not items:
            continue
        anchor = cat.lower().replace(" ", "-").replace("(", "").replace(")", "")
        sections.append(
            f'<section id="{e(anchor)}"><h2>{e(cat)}</h2>'
            f'<p class="blurb">{len(items)} item{"s" if len(items) != 1 else ""}</p>'
            f'<div class="grid">{"".join(card(i) for i in items)}</div></section>')

    nav = " ".join(
        f'<a href="#{e(c.lower().replace(" ","-").replace("(","").replace(")",""))}">{e(c)}</a>'
        for c in CATEGORY_ORDER if any(i["category"] == c for i in ITEMS))

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return (DOC_HTML.replace("%%STAMP%%", e(stamp))
            .replace("%%NAV%%", nav)
            .replace("%%SECTIONS%%", "".join(sections)))


DOC_HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Z-Dot Approval Gallery</title>
<style>
:root{--bg:#0b0e14;--panel:#141924;--line:#232b3a;--tx:#e7ecf3;--dim:#8e9bb0;
--accent:#6db3f2;--ok:#2ecc71;--rv:#f1c40f;--no:#e74c3c}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
header{padding:32px 28px 18px;border-bottom:1px solid var(--line);
 position:sticky;top:0;background:rgba(11,14,20,.96);backdrop-filter:blur(8px);z-index:9}
h1{margin:0 0 4px;font-size:27px;letter-spacing:-.02em}
.sub{color:var(--dim);margin:0;font-size:14px}
nav{margin-top:14px;display:flex;gap:8px;flex-wrap:wrap}
nav a{color:var(--accent);text-decoration:none;border:1px solid var(--line);
 padding:4px 11px;border-radius:999px;font-size:13px}
nav a:hover{border-color:var(--accent)}
.bar{display:flex;gap:10px;align-items:center;margin-top:14px;flex-wrap:wrap}
.count{font-size:13px;color:var(--dim)}
.count b{color:var(--tx)}
button.act{background:transparent;border:1px solid var(--line);color:var(--accent);
 border-radius:8px;padding:6px 12px;font-size:13px;cursor:pointer}
button.act:hover{border-color:var(--accent)}
main{padding:8px 28px 70px;max-width:1240px;margin:0 auto}
section{padding:26px 0;border-bottom:1px solid var(--line)}
section:last-child{border:0}
h2{margin:0 0 2px;font-size:20px}
.blurb{color:var(--dim);margin:0 0 16px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;
 overflow:hidden;display:flex;flex-direction:column}
.card[data-decision="approve"]{border-color:var(--ok);box-shadow:0 0 0 1px var(--ok) inset}
.card[data-decision="revise"]{border-color:var(--rv);box-shadow:0 0 0 1px var(--rv) inset}
.card[data-decision="reject"]{border-color:var(--no);box-shadow:0 0 0 1px var(--no) inset}
.media{background:#0e121a;display:flex;align-items:center;justify-content:center;min-height:110px}
.media img,.media video{display:block;width:100%;max-height:300px;object-fit:contain}
.media audio{width:100%;padding:6px}
.body{padding:13px;display:flex;flex-direction:column;gap:8px;flex:1}
h3{margin:0;font-size:15px}
.meta{margin:0;color:var(--dim);font-size:12.5px}
details summary{cursor:pointer;color:var(--accent);font-size:12.5px}
.proof{font-size:12.5px;color:#b9c4d4;margin:6px 0 0}
.extra{margin:0;font-size:13px}
.extra a{color:var(--accent);text-decoration:none}
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
</style></head>
<body>
<header>
  <h1>Z-Dot Approval Gallery</h1>
  <p class="sub">Every asset up for review. Decide each one, add a note, then export.</p>
  <nav>%%NAV%%</nav>
  <div class="bar">
    <span class="count" id="counts">no decisions yet</span>
    <button class="act" id="export">Export decisions (JSON)</button>
    <button class="act" id="copy">Copy summary</button>
    <button class="act" id="clearc">Clear all</button>
  </div>
</header>
<main>%%SECTIONS%%</main>
<footer>
  Built %%STAMP%%. Decisions are stored in this browser (localStorage) and are not sent
  anywhere. Export and hand the JSON to the CTO to push into the checklist portal.
  Verification text is what we actually ran, not a claim.
</footer>
<script>
const KEY='zdot-gallery-decisions-v1';
const DEC=['approve','revise','reject'];
let state={};
try{ state=JSON.parse(localStorage.getItem(KEY)||'{}'); }catch(_){ state={}; }

function save(){ localStorage.setItem(KEY, JSON.stringify(state)); render(); }
function render(){
  let n={approve:0,revise:0,reject:0};
  document.querySelectorAll('.card').forEach(card=>{
    const id=card.dataset.id, d=(state[id]||{}).d;
    if(d){ card.dataset.decision=d; n[d]++; } else { delete card.dataset.decision; }
    card.querySelectorAll('.btn').forEach(b=>{
      b.classList.toggle('on', !!d && 'd'+'='+b.dataset.d===('d='+d));
    });
    const ta=card.querySelector('.note');
    if(ta && ta.value !== ((state[id]||{}).note||'')) ta.value=(state[id]||{}).note||'';
    const st=card.querySelector('.stamp');
    const t=(state[id]||{}).t;
    st.textContent = d ? (d.toUpperCase()+' · '+(t||'')) : '';
  });
  const tot=n.approve+n.revise+n.reject;
  document.getElementById('counts').innerHTML = tot
    ? `<b>${n.approve}</b> approved · <b>${n.revise}</b> revise · <b>${n.reject}</b> rejected · <b>${tot}</b>/${document.querySelectorAll('.card').length} decided`
    : 'no decisions yet';
}

document.querySelectorAll('.card').forEach(card=>{
  const id=card.dataset.id;
  card.querySelectorAll('.btn').forEach(b=>{
    b.onclick=()=>{
      const d=b.dataset.d;
      const cur=(state[id]||{});
      if(cur.d===d){ delete state[id]; }   // click again to undo
      else { state[id]=Object.assign({},cur,{d:d, t:new Date().toISOString().slice(0,16).replace('T',' ')}); }
      save();
    };
  });
  const ta=card.querySelector('.note');
  ta.onchange=()=>{
    const cur=state[id]||{};
    if(ta.value.trim()==='' && !cur.d){ delete state[id]; } else { state[id]=Object.assign({},cur,{note:ta.value.trim()}); }
    save();
  };
});

document.getElementById('export').onclick=()=>{
  const out={generated:new Date().toISOString(), decisions:Object.entries(state).map(
    ([id,v])=>({id:id, decision:v.d||null, note:v.note||'', at:v.t||null}))};
  const b=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(b);
  a.download='zdot-gallery-decisions.json';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
};

document.getElementById('copy').onclick=async()=>{
  const lines=Object.entries(state).map(([id,v])=>
    `${id}: ${(v.d||'undecided').toUpperCase()}${v.note?(' — '+v.note):''}`);
  const txt=lines.length?lines.join('\\n'):'no decisions yet';
  try{ await navigator.clipboard.writeText(txt); alert('Copied:\\n\\n'+txt); }
  catch(_){ alert(txt); }
};

document.getElementById('clearc').onclick=()=>{
  if(confirm('Clear all decisions in this browser?')){ state={}; save(); }
};

render();
</script>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="/tmp/gallery")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    doc = build()
    with open(os.path.join(a.outdir, "index.html"), "w") as f:
        f.write(doc)
    print(f"wrote {a.outdir}/index.html ({len(doc)} B, {len(ITEMS)} items)")


if __name__ == "__main__":
    main()
