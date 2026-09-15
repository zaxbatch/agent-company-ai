#!/usr/bin/env python3
"""Build the MilkUps TRACKER CUT player page from tracker/manifest.json."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "milkups" / "tracker"
m = json.loads((OUT / "manifest.json").read_text())
T = m["tracks"]

rows = "\n".join(
    f'''    <li class="row" data-i="{i}">
      <button class="play" aria-label="Play {r['title']}"><span class="tri"></span></button>
      <span class="num">{r['no']:02d}</span>
      <span class="ttl">{r['title']}</span>
      <span class="bpm">{r['bpm']}<i>BPM</i></span>
      <span class="len">{int(r['seconds'])//60}:{int(r['seconds'])%60:02d}</span>
      <a class="dl" href="audio/{r['slug']}.mp3" download title="Download MP3">MP3</a>
      <a class="dl xm" href="xm/{r['slug']}.xm" download title="Download the .xm module">.XM</a>
    </li>''' for i, r in enumerate(T))

tracks_js = json.dumps([{"t": r["title"], "f": f"audio/{r['slug']}.mp3"} for r in T])

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MilkUps — Tracker Cut (8 chip tracks)</title>
<meta name="description" content="MilkUps — TRACKER CUT. 8 fresh chiptune tracks, authored as real FastTracker II .XM modules and rendered chip-style. Download the MP3s or the actual modules.">
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#07050a;color:#d7f7e8;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
       min-height:100vh;display:flex;justify-content:center;padding:22px 16px}}
  .wrap{{width:100%;max-width:720px}}
  .top{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:18px;flex-wrap:wrap;gap:6px}}
  .logo{{font-weight:800;letter-spacing:2px;color:#5cffc4;text-shadow:0 0 12px #5cffc455}}
  .logo span{{color:#3d7a68;font-weight:400;letter-spacing:3px;font-size:11px;margin-left:8px}}
  .nav a{{color:#8fe8c8;text-decoration:none;font-size:12px;border-bottom:1px dotted #3d7a68;margin-left:14px}}
  h1{{font-size:15px;letter-spacing:4px;color:#8fe8c8;margin-bottom:4px}}
  .sub{{color:#4f8f79;font-size:12px;margin-bottom:18px;letter-spacing:1px}}
  .scr{{background:linear-gradient(#0a0f0d,#070b09);border:1px solid #1d5c47;border-radius:12px;
        padding:16px;margin-bottom:16px;box-shadow:inset 0 0 60px #000, 0 0 30px #5cffc418}}
  .np{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
  .np .k{{color:#3d7a68;font-size:10px;letter-spacing:2px}}
  .np b{{color:#5cffc4;font-size:13px;letter-spacing:.5px}}
  .bar{{height:6px;background:#12312a;border-radius:4px;overflow:hidden;margin:10px 0}}
  .bar i{{display:block;height:100%;width:0%;background:linear-gradient(90deg,#5cffc4,#00d0ff)}}
  .times{{display:flex;justify-content:space-between;font-size:10px;color:#3d7a68}}
  .ctrl{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}}
  button.p{{background:#5cffc4;color:#04120e;border:0;border-radius:8px;padding:9px 16px;
            font-family:inherit;font-weight:700;font-size:12px;letter-spacing:1px;cursor:pointer}}
  button.s{{background:transparent;color:#8fe8c8;border:1px solid #1d5c47;border-radius:8px;
            padding:9px 14px;font-family:inherit;font-size:12px;cursor:pointer}}
  button:hover{{filter:brightness(1.15)}}
  ul{{list-style:none;border:1px solid #163f33;border-radius:12px;overflow:hidden}}
  li.row{{display:grid;grid-template-columns:38px 30px 1fr 62px 42px 52px 52px;align-items:center;gap:8px;
          padding:9px 12px;border-bottom:1px solid #102b23;font-size:12px;transition:background .15s}}
  li.row:last-child{{border-bottom:0}}
  li.row:hover{{background:#0d1f19}}
  li.row.on{{background:#0f2a22}}
  li.row.on .ttl{{color:#5cffc4}}
  .play{{width:26px;height:26px;border-radius:6px;border:1px solid #1d5c47;background:#0a1a15;cursor:pointer;
         display:flex;align-items:center;justify-content:center;padding:0}}
  .tri{{width:0;height:0;border-left:7px solid #5cffc4;border-top:5px solid transparent;border-bottom:5px solid transparent;margin-left:2px}}
  .num{{color:#2f6b58;font-size:11px}}
  .ttl{{color:#cdf3e4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .bpm{{color:#4f8f79;font-size:10px;text-align:right}} .bpm i{{font-style:normal;color:#2f6b58;margin-left:2px}}
  .len{{color:#4f8f79;font-size:11px;text-align:right}}
  .dl{{color:#8fe8c8;font-size:10px;text-decoration:none;border:1px solid #1d5c47;border-radius:6px;
       padding:3px 6px;text-align:center;letter-spacing:.5px}}
  .dl:hover{{background:#12312a}} .dl.xm{{color:#69d4ff;border-color:#1b4a5e}}
  .buy{{margin-top:18px;background:#0a0f0d;border:1px solid #1d5c47;border-radius:12px;padding:16px;
        display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
  .buy img{{width:96px;height:96px;border-radius:8px;background:#fff;padding:6px}}
  .buy .bt{{color:#5cffc4;font-size:13px;font-weight:700;letter-spacing:1px}}
  .buy .bs{{color:#4f8f79;font-size:11px;margin-top:4px;line-height:1.6}}
  .buy a.btn{{display:inline-block;margin-top:10px;background:#5cffc4;color:#04120e;text-decoration:none;
              font-weight:700;font-size:12px;padding:9px 16px;border-radius:8px}}
  .foot{{color:#2f6b58;font-size:10px;margin-top:16px;line-height:1.7;letter-spacing:.4px}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="logo">MILKUPS<span>TRACKER CUT</span></div>
    <div class="nav">
      <a href="/">band</a><a href="/album/">tape player</a><a href="/album/v2/">album</a>
    </div>
  </div>

  <h1>TRACKER CUT</h1>
  <div class="sub">8 chip tracks · authored as real FastTracker II .XM · rendered libopenmpt · mastered -14 LUFS</div>

  <div class="scr">
    <div class="np"><span class="k">NOW PLAYING</span><b id="now">—</b></div>
    <div class="bar"><i id="fill"></i></div>
    <div class="times"><span id="cur">0:00</span><span id="tot">0:00</span></div>
    <div class="ctrl">
      <button class="p" id="pp">▶ PLAY</button>
      <button class="s" id="prev">⏮</button>
      <button class="s" id="next">⏭</button>
      <button class="s" id="shuf">SHUFFLE</button>
    </div>
  </div>

  <ul>
{rows}
  </ul>

  <div class="buy">
    <img src="/assets/qr-zdotllc-5.png" alt="Cash App QR — send $5 to $zdotllc">
    <div>
      <div class="bt">$5 — the whole thing, all cuts</div>
      <div class="bs">Cash App <b>$zdotllc</b> · every track streams free right here,<br>
      no login, no paywall. The $5 gets you all three cuts + the .xm modules.</div>
      <a class="btn" href="https://cash.app/$zdotllc/5">Send $5 → $zdotllc</a>
    </div>
  </div>

  <div class="foot">
    Every module here is pure code — synthesized samples, no external audio.<br>
    Download the .XM and open it in MilkyTracker, FastTracker II, or OpenMPT.<br>
    MilkUps · milkups@zerric.xyz
  </div>
</div>

<script>
var TRACKS = {tracks_js};
var a = new Audio(), i = 0, shuf = false;
var now = document.getElementById('now'), fill = document.getElementById('fill'),
    cur = document.getElementById('cur'), tot = document.getElementById('tot'),
    pp = document.getElementById('pp');
function fmt(s){{ s = Math.max(0, s|0); return (s/60|0) + ':' + String(s%60).padStart(2,'0'); }}
function mark(){{ document.querySelectorAll('li.row').forEach(function(r){{
  r.classList.toggle('on', +r.dataset.i === i); }}); }}
function load(n, play){{
  i = (n + TRACKS.length) % TRACKS.length;
  a.src = TRACKS[i].f; now.textContent = TRACKS[i].t; mark();
  if (play) a.play(); pp.textContent = play ? '⏸ PAUSE' : '▶ PLAY';
}}
function next(){{ if (shuf) load(Math.floor(Math.random()*TRACKS.length), true);
  else load(i+1, true); }}
a.addEventListener('timeupdate', function(){{
  fill.style.width = (a.duration ? (a.currentTime/a.duration*100) : 0) + '%';
  cur.textContent = fmt(a.currentTime); tot.textContent = fmt(a.duration || 0);
}});
a.addEventListener('ended', next);
pp.onclick = function(){{
  if (!a.src) {{ load(0, true); return; }}
  if (a.paused) {{ a.play(); pp.textContent = '⏸ PAUSE'; }}
  else {{ a.pause(); pp.textContent = '▶ PLAY'; }}
}};
document.getElementById('next').onclick = next;
document.getElementById('prev').onclick = function(){{
  if (a.currentTime > 3) {{ a.currentTime = 0; return; }} load(i-1, true); }};
document.getElementById('shuf').onclick = function(e){{
  shuf = !shuf; e.target.textContent = shuf ? 'SHUFFLE ✓' : 'SHUFFLE'; }};
document.querySelectorAll('li.row').forEach(function(r){{
  var n = +r.dataset.i;
  r.querySelector('.play').onclick = function(){{ load(n, true); }};
  r.querySelector('.ttl').style.cursor = 'pointer';
  r.querySelector('.ttl').onclick = function(){{ load(n, true); }};
}});
mark();
</script>
</body>
</html>
'''
(OUT / "index.html").write_text(html)
print(f"page written: {(OUT/'index.html').relative_to(ROOT)} ({len(html)} bytes, {len(T)} tracks)")
