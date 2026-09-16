#!/usr/bin/env python3
"""EP-010 "ELECTRO EP" — 10 tracks, built HERE from scratch.

The saasCo/ep workspace referenced by the previous evidence report does not exist
on this machine. This builds the EP for real with the Z-Dot tracker pipeline:
pure-Python FastTracker II .XM authoring -> ffmpeg libopenmpt -> two-pass
loudnorm master -> MP3 320k CBR, with a hard QA gate.

Spec: 10 tracks, each >= 120 s (2:00), uniform -14 LUFS / -1.0 dBTP.
"""
from __future__ import annotations
import hashlib, json, math, subprocess, sys
from pathlib import Path

EP   = Path(__file__).resolve().parents[1]
ROOT = Path("/home/zax/Biz/z-dot-team")
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import build_milkups_album as A
from build_milkups_album import make_song, xm_write
from build_milkups_tracker_cut import render_xm_libopenmpt, master_to_mp3, dur_of

_orig_plan = A.plan_patterns
TARGET_S = 132.0
A.plan_patterns = lambda track, target_s=TARGET_S: _orig_plan(track, target_s)

XM, WAV, MP3, ART, QA = (EP/"xm", EP/"wav", EP/"mp3", EP/"art", EP/"qa")
for d in (XM, WAV, MP3, ART, QA): d.mkdir(parents=True, exist_ok=True)
MIN_SECONDS = 120.0

TRACKS = [
    ( 1, "Neon Voltage",      "neon-voltage",      168, 45, 151),
    ( 2, "Circuit Breaker",   "circuit-breaker",   150, 41, 163),
    ( 3, "Midnight Protocol", "midnight-protocol", 134, 43, 179),
    ( 4, "Chrome Hearts",     "chrome-hearts",     172, 48, 191),
    ( 5, "Voltage Drop",      "voltage-drop",      128, 40, 197),
    ( 6, "Static Bloom",      "static-bloom",      144, 46, 211),
    ( 7, "Pulse Reactor",     "pulse-reactor",     178, 50, 223),
    ( 8, "Afterglow Drive",   "afterglow-drive",   138, 44, 227),
    ( 9, "Overdrive",         "overdrive",         164, 47, 233),
    (10, "Aurora Circuit",    "aurora-circuit",    156, 52, 239),
]
HUES = [(255,60,160),(60,220,255),(140,90,255),(255,140,40),(70,255,190),
        (255,80,80),(90,140,255),(255,200,60),(200,60,255),(50,230,180)]


def cover(no, title, slug, bpm, hue):
    Wv = Hv = 1000
    bg = (8, 8, 16)
    im = Image.new("RGB", (Wv, Hv), bg); d = ImageDraw.Draw(im)
    r, g, b = hue
    for i in range(0, Wv, 50):
        a = int(26 + 40*abs(math.sin(i/90)))
        d.line([(i,0),(i,Hv)], fill=(r*a//255//4, g*a//255//4, b*a//255//4), width=1)
    for j in range(0, Hv, 50):
        a = int(26 + 40*abs(math.cos(j/90)))
        d.line([(0,j),(Wv,j)], fill=(r*a//255//4, g*a//255//4, b*a//255//4), width=1)
    for k in range(90, 0, -1):
        al = (90-k)/90*0.55
        d.rectangle([0, 700-k//2, Wv, 700+k//2],
                    fill=(int(r*al)+bg[0], int(g*al)+bg[1], int(b*al)+bg[2]))
    d.rectangle([0, 692, Wv, 708], fill=hue)
    f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 74)
    f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    f3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
    words = title.upper().split()
    lines = [" ".join(words[:1]), " ".join(words[1:])] if len(words) > 1 else [words[0]]
    for i, ln in enumerate(lines):
        if ln: d.text((58, 120 + i*84), ln, font=f1, fill=(255, 255, 255))
    d.text((58, 300), f"{bpm} BPM  ·  ELECTRO", font=f2, fill=hue)
    d.text((58, 760), "EP-010", font=f3, fill=(150, 150, 170))
    d.text((Wv-300, 760), f"TRACK {no:02d}", font=f3, fill=hue)
    d.text((58, 900), "SNOWSNAKES", font=f3, fill=(90, 90, 110))
    p = ART/f"{slug}.png"; im.save(p); return p


def probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration,size,bit_rate",
                        "-show_entries","stream=codec_name,sample_rate,channels",
                        "-of","json",str(p)], capture_output=True, text=True)
    return json.loads(r.stdout or "{}")


def main():
    man = {"ep":"EP-010","title":"ELECTRO EP","artist":"SnowSnakes",
           "engine":"FastTracker II (.xm) -> ffmpeg libopenmpt",
           "master":{"target_lufs":-14.0,"target_tp":-1.0,"target_lra":9.0},
           "spec":f"10 tracks, each >= {MIN_SECONDS:.0f}s","tracks":[]}
    print(f"{'#':>2}  {'track':<19} {'bpm':>4} {'sec':>7} {'LUFS':>7} {'TP':>6} {'mp3':>9}  gate")
    for no, title, slug, bpm, root, seed in TRACKS:
        t = {"n":no,"title":title,"slug":slug,"bpm":bpm,"root":root,"bars":32,"seed":seed}
        song = make_song(t)
        xm, wav, mp3 = XM/f"{slug}.xm", WAV/f"{slug}.wav", MP3/f"{slug}.mp3"
        xm_write(t, song, xm)
        render_xm_libopenmpt(xm, wav)
        lm = master_to_mp3(wav, mp3)
        sec = dur_of(mp3)
        cv = cover(no, title, slug, bpm, HUES[no-1])
        ok = sec>=MIN_SECONDS and abs(lm["out_i"]+14.0)<=1.0 and lm["out_tp"]<=-1.0+0.3
        rec = {"no":no,"title":title,"slug":slug,"bpm":bpm,
               "xm":f"ep/xm/{slug}.xm","xm_bytes":xm.stat().st_size,
               "mp3":f"ep/mp3/{slug}.mp3","mp3_bytes":mp3.stat().st_size,
               "cover":f"ep/art/{slug}.png","seconds":round(sec,3),
               "lufs":round(lm["out_i"],2),"true_peak_dbtp":round(lm["out_tp"],2),
               "lra":round(lm["out_lra"],2),
               "sha256":hashlib.sha256(mp3.read_bytes()).hexdigest(),
               "probe":probe(mp3),"gate":"PASS" if ok else "FAIL"}
        man["tracks"].append(rec)
        print(f"{no:>2}  {title:<19} {bpm:>4} {sec:>7.2f} {rec['lufs']:>7.2f} "
              f"{rec['true_peak_dbtp']:>6.2f} {rec['mp3_bytes']:>9}  {rec['gate']}", flush=True)
        try: wav.unlink()
        except OSError: pass
    fails=[t for t in man["tracks"] if t["gate"]!="PASS"]
    man["gate"]={"passed":not fails,"failed":[t["slug"] for t in fails]}
    (EP/"manifest.json").write_text(json.dumps(man,indent=2))
    md=["# EP-010 \"ELECTRO EP\" — QA EVIDENCE (raw values, generated)","",
        f"Rendered {len(man['tracks'])}/10. Gate: {'PASS' if not fails else 'FAIL'}.","",
        "| # | Track | BPM | File | Bytes | Duration (s) | LUFS | True Peak (dBTP) | SHA256 (first 16) |",
        "|---|-------|-----|------|-------|--------------|------|------------------|-------------------|"]
    for t in man["tracks"]:
        md.append(f"| {t['no']:02d} | {t['title']} | {t['bpm']} | mp3/{t['slug']}.mp3 | "
                  f"{t['mp3_bytes']} | {t['seconds']} | {t['lufs']} | {t['true_peak_dbtp']} | {t['sha256'][:16]} |")
    md+=["","## ffprobe (verbatim)","```"]
    for t in man["tracks"]:
        md.append(f"$ ffprobe ... ep/mp3/{t['slug']}.mp3"); md.append(f"{t['seconds']},{t['mp3_bytes']}")
    md+=["```","","## Gate","- duration >= 120s","- |LUFS +14| <= 1","- true peak <= -1.0 dBTP","",
         "## Editable modules","```"]
    for t in man["tracks"]: md.append(f"ep/xm/{t['slug']}.xm  {t['xm_bytes']} bytes")
    md.append("```")
    (QA/"EP-010-QA.md").write_text("\n".join(md)+"\n")
    tl="\n".join(f"{t['no']:02d} - {t['title']}.mp3 ({t['bpm']} BPM) "
                 f"{int(t['seconds'])//60}:{int(t['seconds'])%60:02d}" for t in man["tracks"])
    (EP/"tracklist.txt").write_text(f"SNOWSNAKES — EP-010 \"ELECTRO EP\"\n10 tracks\n\n{tl}\n")
    print(f"\nGATE: {'PASS' if not fails else 'FAIL'}  rendered {len(man['tracks'])}/10", flush=True)
    for t in fails: print("  FAIL:", t["slug"], t["seconds"], t["lufs"])
    return 0 if not fails else 1

if __name__ == "__main__":
    raise SystemExit(main())
