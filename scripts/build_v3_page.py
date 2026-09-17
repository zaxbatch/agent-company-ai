#!/usr/bin/env python3
"""Player page for album-v3, showing each track's own identity."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "milkups" / "album-v3"
m = json.loads((OUT/"manifest.json").read_text())
T = m["tracks"]
V = m.get("variety", {})

rows = "\n".join(
f'''    <li class="row" data-i="{i}">
      <button class="play" aria-label="Play {r['title']}"><span class="tri"></span></button>
      <span class="num">{r['no']:02d}</span>
      <span class="ttl">{r['title']}</span>
      <span class="kit">{r['lead'].replace('_',' ')}</span>
      <span class="bpm">{r['bpm']}<i>BPM</i></span>
      <span class="len">{int(r['seconds'])//60}:{int(r['seconds'])%60:02d}</span>
      <a class="dl" href="mp3/{r['slug']}.mp3" download>MP3</a>
      <a class="dl xm" href="xm/{r['slug']}.xm" download>.XM</a>
    </li>''' for i, r in enumerate(T))

tracks_js = json.dumps([{"t": r["title"], "f": f"mp3/{r['slug']}.mp3"} for r in T])
spread = V.get("centroid_spread", 0)

html = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MilkUps — The Shelves Raised Us (2026 rebuild)</title>
<meta name="description" content="MilkUps — The Shelves Raised Us. Eight tracks, each with its own lead voice, bass, drum kit and harmony. Built in FastTracker II at 16-bit.">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#08070c;color:#e9e4f5;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
min-height:100vh;display:flex;justify-content:center;padding:22px 15px}}
.wrap{{width:100%;max-width:780px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;flex-wrap:wrap;gap:8px}}
.logo{{font-weight:800;letter-spacing:2px;color:#f0a6ff;text-shadow:0 0 14px #f0a6ff44}}
.logo span{{color:#6f5f8a;font-weight:400;font-size:11px;letter-spacing:3px;margin-left:9px}}
.nav a{{color:#c39bd8;text-decoration:none;font-size:12px;margin-left:13px;border-bottom:1px dotted #6f5f8a}}
h1{{font-size:16px;letter-spacing:4px;color:#c39bd8;margin-bottom:5px}}
.sub{{color:#7d6a99;font-size:12px;line-height:1.7;margin-bottom:18px}}
.sub b{{color:#f0a6ff}}
.scr{{background:linear-gradient(#100c18,#0a0710);border:1px solid #3d2a55;border-radius:13px;
padding:16px;margin-bottom:16px;box-shadow:inset 0 0 60px #000}}
.np{{color:#7d6a99;font-size:10px;letter-spacing:2px;margin-bottom:7px}}
.np b{{color:#f0a6ff;font-size:13px;letter-spacing:0}}
.bar{{height:6px;background:#20162e;border-radius:4px;overflow:hidden;margin:10px 0}}
.bar i{{display:block;height:100%;width:0%;background:linear-gradient(90deg,#f0a6ff,#7fd1ff)}}
.times{{display:flex;justify-content:space-between;font-size:10px;color:#5d4d75}}
.ctrl{{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}}
button.p{{background:#f0a6ff;color:#1a0a20;border:0;border-radius:8px;padding:10px 18px;
font-family:inherit;font-weight:700;font-size:12px;cursor:pointer}}
button.s{{background:transparent;color:#c39bd8;border:1px solid #3d2a55;border-radius:8px;
padding:10px 14px;font-family:inherit;font-size:12px;cursor:pointer}}
ul{{list-style:none;border:1px solid #2c1f3d;border-radius:13px;overflow:hidden}}
li.row{{display:grid;grid-template-columns:34px 26px 1fr 118px 54px 40px 44px 44px;
align-items:center;gap:7px;padding:10px 12px;border-bottom:1px solid #1c1428;font-size:12px}}
li.row:last-child{{border-bottom:0}}
li.row:hover{{background:#130e1d}} li.row.on{{background:#1b1230}} li.row.on .ttl{{color:#f0a6ff}}
.play{{width:24px;height:24px;border-radius:6px;border:1px solid #3d2a55;background:#130e1d;cursor:pointer;
display:flex;align-items:center;justify-content:center;padding:0}}
.tri{{width:0;height:0;border-left:7px solid #f0a6ff;border-top:5px solid transparent;border-bottom:5px solid transparent;margin-left:2px}}
.num{{color:#5d4d75;font-size:11px}}
.ttl{{color:#e9e4f5;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.kit{{color:#8f7ab0;font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.bpm{{color:#5d4d75;font-size:10px;text-align:right}} .bpm i{{font-style:normal;color:#40344f}}
.len{{color:#5d4d75;font-size:11px;text-align:right}}
.dl{{color:#c39bd8;font-size:10px;text-decoration:none;border:1px solid #3d2a55;border-radius:6px;padding:3px 5px;text-align:center}}
.dl:hover{{background:#241832}} .dl.xm{{color:#7fd1ff;border-color:#22445c}}
.buy{{margin-top:18px;background:#0d0a14;border:1px solid #2c1f3d;border-radius:13px;padding:16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
.buy img{{width:92px;height:92px;border-radius:8px;background:#fff;padding:6px}}
.buy .bt{{color:#f0a6ff;font-size:13px;font-weight:700}}
.buy .bs{{color:#7d6a99;font-size:11px;margin-top:4px;line-height:1.6}}
.buy a.btn{{display:inline-block;margin-top:9px;background:#f0a6ff;color:#1a0a20;text-decoration:none;
font-weight:700;font-size:12px;padding:10px 17px;border-radius:8px}}
.foot{{color:#4a3d5e;font-size:10px;margin-top:16px;line-height:1.8}}
</style></head><body><div class="wrap">
<div class="top"><div class="logo">MILKUPS<span>2026 REBUILD</span></div>
<div class="nav"><a href="/">band</a><a href="/album/">tape</a><a href="/album/v2/">album</a><a href="/tracker/">tracker</a></div></div>
<h1>THE SHELVES RAISED US</h1>
<div class="sub">Eight tracks. <b>Each one has its own lead voice, bass, drum kit, harmony and register</b> &mdash;
no shared instrument, no transposed loop. Authored in FastTracker II at <b>16-bit</b>, so quiet
sections actually survive. Mastered to &minus;14 LUFS.<br>
Spectral spread across the album: <b>{spread:.0f} Hz</b> (the previous cut: 162 Hz).</div>
<div class="scr">
  <div class="np">NOW PLAYING <b id="now">&mdash;</b></div>
  <div class="bar"><i id="fill"></i></div>
  <div class="times"><span id="cur">0:00</span><span id="tot">0:00</span></div>
  <div class="ctrl"><button class="p" id="pp">&#9654; PLAY</button>
  <button class="s" id="prev">&#9198;</button><button class="s" id="next">&#9197;</button>
  <button class="s" id="shuf">SHUFFLE</button></div>
</div>
<ul>{rows}</ul>
<div class="buy"><img src="/assets/qr-zdotllc-5.png" alt="Cash App QR — $zdotllc">
<div><div class="bt">$5 &mdash; all cuts, everything</div>
<div class="bs">Cash App <b>$zdotllc</b>. Every track streams free right here, no login.<br>
The $5 gets you all cuts plus the editable .XM modules.</div>
<a class="btn" href="https://cash.app/$zdotllc/5">Send $5 &rarr; $zdotllc</a></div></div>
<div class="foot">Every .XM module is downloadable &mdash; open it in MilkyTracker, FastTracker II or OpenMPT.
Each track's instrument list is its own. MilkUps &middot; milkups@zerric.xyz</div>
</div>
<script>
var TRACKS={tracks_js};
var a=new Audio(),i=0,shuf=false;
var now=document.getElementById('now'),fill=document.getElementById('fill'),
cur=document.getElementById('cur'),tot=document.getElementById('tot'),pp=document.getElementById('pp');
function fmt(s){{s=Math.max(0,s|0);return (s/60|0)+':'+String(s%60).padStart(2,'0')}}
function mark(){{document.querySelectorAll('li.row').forEach(function(r){{r.classList.toggle('on',+r.dataset.i===i)}})}}
function load(n,play){{i=(n+TRACKS.length)%TRACKS.length;a.src=TRACKS[i].f;now.textContent=TRACKS[i].t;mark();
if(play)a.play();pp.textContent=play?'&#10074;&#10074; PAUSE':'&#9654; PLAY'}}
function next(){{shuf?load(Math.floor(Math.random()*TRACKS.length),true):load(i+1,true)}}
a.addEventListener('timeupdate',function(){{fill.style.width=(a.duration?(a.currentTime/a.duration*100):0)+'%';
cur.textContent=fmt(a.currentTime);tot.textContent=fmt(a.duration||0)}});
a.addEventListener('ended',next);
pp.onclick=function(){{if(!a.src){{load(0,true);return}}if(a.paused){{a.play();pp.textContent='&#10074;&#10074; PAUSE'}}
else{{a.pause();pp.textContent='&#9654; PLAY'}}}};
document.getElementById('next').onclick=next;
document.getElementById('prev').onclick=function(){{if(a.currentTime>3){{a.currentTime=0;return}}load(i-1,true)}};
document.getElementById('shuf').onclick=function(e){{shuf=!shuf;e.target.textContent=shuf?'SHUFFLE &#10003;':'SHUFFLE'}};
document.querySelectorAll('li.row').forEach(function(r){{var n=+r.dataset.i;
r.querySelector('.play').onclick=function(){{load(n,true)}};
r.querySelector('.ttl').style.cursor='pointer';
r.querySelector('.ttl').onclick=function(){{load(n,true)}}}});
mark();
</script></body></html>
'''
(OUT/"index.html").write_text(html)
print(f"page: {(OUT/'index.html').relative_to(ROOT)} ({len(html)} bytes, {len(T)} tracks, spread {spread:.0f} Hz)")
