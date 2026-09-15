#!/usr/bin/env python3
"""Build 2 SnowSnakes tracker songs (.xm -> libopenmpt -> mastered MP3) + covers."""
from __future__ import annotations
import hashlib, json, math, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from build_milkups_album import make_song, xm_write
from build_milkups_tracker_cut import render_xm_libopenmpt, master_to_mp3, dur_of

OUT = ROOT / "content" / "snowsnakes" / "songs"
XM, WAV, MP3, ART = OUT/"xm", OUT/"wav", OUT/"audio", OUT/"art"
for d in (XM, WAV, MP3, ART): d.mkdir(parents=True, exist_ok=True)

TRACKS = [
    {"n":1, "title":"Frozen Cab-Nets", "slug":"frozen-cab-nets", "bpm":150, "root":45, "bars":28, "seed":301},
    {"n":2, "title":"Snowflake Static","slug":"snowflake-static","bpm":172, "root":48, "bars":30, "seed":317},
]
PAL = {"Frozen Cab-Nets":((12,24,40),(120,200,255),(255,209,102)),
       "Snowflake Static":((18,12,34),(150,120,255),(120,240,220))}

def cover(title, slug, sub):
    W,H=1000,1000
    bg,ac,ac2 = PAL[title]
    im=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(im)
    # snow grid
    import random; r=random.Random(title)
    for _ in range(240):
        x,y=r.random()*W, r.random()*H; s=r.choice([2,3,4,6])
        d.ellipse([x,y,x+s,y+s], fill=ac2)
    # geometric band
    d.rectangle([0,640,W,760], fill=ac)
    f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",86)
    f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",44)
    f3=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",34)
    for i,ln in enumerate(title.upper().split()):
        d.text((60, 150+i*100), ln, font=f1, fill=(255,255,255))
    d.text((60, 672), sub, font=f2, fill=bg)
    d.text((60, 900), "SNOWSNAKES", font=f3, fill=ac2)
    p=ART/f"{slug}.png"; im.save(p); return p

def main():
    man={"artist":"SnowSnakes","engine":"FastTracker II (.xm) -> libopenmpt","tracks":[]}
    for t in TRACKS:
        song=make_song(t)
        xm=XM/f"{t['slug']}.xm"; wav=WAV/f"{t['slug']}.wav"; mp3=MP3/f"{t['slug']}.mp3"
        xm_write(t,song,xm); render_xm_libopenmpt(xm,wav); lm=master_to_mp3(wav,mp3)
        sec=dur_of(mp3)
        cv=cover(t["title"], t["slug"], f"{t['bpm']} BPM  ·  TRACKER CUT")
        rec={"title":t["title"],"slug":t["slug"],"bpm":t["bpm"],"seconds":round(sec,2),
             "lufs":round(lm["out_i"],2),"tp":round(lm["out_tp"],2),
             "mp3":str(mp3.relative_to(ROOT)),"mp3_bytes":mp3.stat().st_size,
             "cover":str(cv.relative_to(ROOT)),"sha256":hashlib.sha256(mp3.read_bytes()).hexdigest()}
        man["tracks"].append(rec)
        print(f"  {t['title']:<20} {sec:6.2f}s  {rec['lufs']:6.2f} LUFS  {rec['tp']:6.2f} dBTP  cover={cv.name}")
    (OUT/"manifest.json").write_text(json.dumps(man,indent=2))
    print("GATE:", "PASS" if all(x["seconds"]>=60 for x in man["tracks"]) else "FAIL")
if __name__=="__main__": raise SystemExit(main())
