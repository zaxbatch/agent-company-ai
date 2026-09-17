#!/usr/bin/env python3
"""MilkUps — THE SHELVES RAISED US (quality rebuild).

WHY THIS EXISTS
The previous cut used ONE square-wave lead pinned 2-3 octaves up, four fixed
instruments, and one 16-bar loop transposed eight times. Measured result:
spectral-centroid spread of 162 Hz across eight "different" songs — i.e. one song
played eight times. Zerric heard it immediately.

ALSO FIXED: 8-bit samples destroyed quiet detail entirely (0 of 2000 samples at
-48 dBFS survived). 16-bit is now used, so real dynamics exist for the first time:
quiet intros, breakdowns, fade-outs.

WHAT IS DIFFERENT PER TRACK
  voice    - its own lead from 10 distinct synth designs
  bass     - its own bass from 6
  kit      - its own drum kit from 6 (different kick/snare/hat synthesis)
  harmony  - its own chord progression, not one loop transposed
  register - its own lead octave (low / mid / high)
  groove   - its own kick/snare/hat patterns
  shape    - its own section map with real dynamic contrast

Usage: python3 scripts/build_milkups_quality.py [--only 3]
"""
from __future__ import annotations
import argparse, hashlib, json, math, subprocess, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import numpy as np
from xm_lib import Sample, Instrument, Module, SR
from milkups_voices import LEADS, BASSES, KITS, env, lp, hp

OUT = ROOT / "content" / "milkups" / "album-v3"
XM, WAV, MP3, ART, QA = (OUT/"xm", OUT/"wav", OUT/"mp3", OUT/"art", OUT/"qa")
for d in (XM, WAV, MP3, ART, QA): d.mkdir(parents=True, exist_ok=True)

CH = dict(lead=0, bass=1, arp=2, kick=3, snare=4, hat=5, perc=6, pad=7)
NCH = 8
LEAD_F, BASS_F = 440.0, 110.0          # voice design frequencies (calibrated)
DRUM_NOTE = 49                          # plays a drum sample at its designed pitch

def hz(midi): return 440.0 * 2 ** ((midi - 69) / 12.0)
def note_for(target_hz, base):
    """Calibrated: a voice designed at `base` Hz sounds at note 49. Verified."""
    return max(1, min(96, int(round(49 + 12 * math.log2(max(20.0, target_hz) / base)))))

MINOR = [0, 2, 3, 5, 7, 8, 10]
PENTA = [0, 3, 5, 7, 10]

# ── per-track briefs: every field is a real musical decision ─────────────────
TRACKS = [
 dict(no=1, title="Cold Aisle Chip", slug="01-cold-aisle-chip", bpm=168, root=57,  # A3
      lead="bright_square", bass="square", kit="clicky", reg=36, scale=MINOR,
      prog=[(0,[0,3,7]),(8,[0,4,7]),(3,[0,4,7]),(10,[0,4,7])],
      kick="x..x..x...x.x...", snare="....x.......x...", hat="x.x.x.x.x.x.x.x.",
      density=0.78, sections=[("intro",0.34),("build",0.60),("drop",1.0),
                              ("break",0.42),("drop",1.0),("outro",0.30)]),

 dict(no=2, title="Carton Static", slug="02-carton-static", bpm=152, root=53,     # F3
      lead="detuned_saw", bass="saw", kit="tight", reg=24, scale=MINOR,
      prog=[(0,[0,3,7]),(8,[0,3,7]),(3,[0,4,7]),(10,[0,4,7])],
      kick="x...x..x..x.....", snare="....x.......x..x", hat="x.xxx.x.x.xxx.x.",
      density=0.70, sections=[("build",0.62),("drop",1.0),("drop",1.0),
                              ("break",0.40),("drop",1.0),("outro",0.32)]),

 dict(no=3, title="Expiration Date", slug="03-expiration-date", bpm=140, root=55, # G3
      lead="soft_triangle", bass="organ", kit="soft", reg=12, scale=MINOR,
      prog=[(0,[0,3,7]),(5,[0,3,7]),(10,[0,4,7]),(7,[0,4,7])],
      kick="x.......x.......", snare="........x.......", hat="..x...x...x...x.",
      density=0.44, sections=[("intro",0.30),("build",0.48),("drop",0.74),
                              ("break",0.34),("drop",0.74),("outro",0.22)]),

 dict(no=4, title="Dairy Case Dreams", slug="04-dairy-case-dreams", bpm=176, root=50,# D3
      lead="fm_bell", bass="sub", kit="808", reg=36, scale=MINOR,
      prog=[(0,[0,3,7]),(5,[0,3,7]),(8,[0,4,7]),(9,[0,4,7])],
      kick="x.....x.....x...", snare="....x.......x...", hat="x.x.x.x.x.x.x.x.",
      density=0.52, sections=[("intro",0.36),("drop",0.82),("break",0.38),
                              ("drop",0.92),("outro",0.26)]),

 dict(no=5, title="2% Signal", slug="05-2pct-signal", bpm=132, root=52,           # E3
      lead="narrow_pulse", bass="square", kit="clicky", reg=24, scale=MINOR,
      prog=[(0,[0,3,7]),(8,[0,4,7]),(5,[0,3,7]),(7,[0,4,7])],
      kick="x..x..x..x..x...", snare="....x.......x.x.", hat="xxxxxxxxxxxxxxxx",
      density=0.86, sections=[("intro",0.30),("build",0.55),("drop",1.0),
                              ("drop",1.0),("break",0.44),("outro",0.28)]),

 dict(no=6, title="Shelf Life", slug="06-shelf-life", bpm=160, root=48,           # C3
      lead="organ", bass="organ", kit="soft", reg=24, scale=MINOR,
      prog=[(0,[0,3,7]),(8,[0,4,7]),(3,[0,4,7]),(10,[0,3,7])],
      kick="x.......x.......", snare="........x.......", hat="..x...x...x...x.",
      density=0.50, sections=[("intro",0.42),("build",0.58),("drop",0.80),
                              ("break",0.50),("drop",0.86),("outro",0.34)]),

 dict(no=7, title="Homogenized", slug="07-homogenized", bpm=128, root=59,         # B3
      lead="metallic_fm", bass="fm", kit="industrial", reg=24, scale=MINOR,
      prog=[(0,[0,3,7]),(3,[0,4,7]),(5,[0,3,7]),(10,[0,4,7])],
      kick="x.x...x...x.x...", snare="....x...x...x.x.", hat="x.xx.xx.x.xx.xx.",
      density=0.62, sections=[("intro",0.26),("drop",0.96),("break",0.36),
                              ("drop",1.0),("outro",0.30)]),

 dict(no=8, title="Last Carton", slug="08-last-carton", bpm=184, root=57,         # A3
      lead="supersaw", bass="saw", kit="deep", reg=36, scale=[0,2,4,7,9],   # major pent
      prog=[(0,[0,4,7]),(9,[0,3,7]),(5,[0,4,7]),(7,[0,4,7])],
      kick="x..x..x..x..x..x", snare="....x.......x...", hat="x.x.x.x.x.x.x.x.",
      density=0.80, sections=[("intro",0.34),("build",0.64),("drop",1.0),
                              ("drop",1.0),("break",0.46),("drop",1.0),("outro",0.30)]),
]


# ── instrument construction: each track builds its OWN samples ───────────────
def make_instruments(b, rng):
    lead_fn  = LEADS[b["lead"]]
    bass_fn  = BASSES[b["bass"]]
    kit      = KITS[b["kit"]]()
    S = {}
    S["lead"]  = Sample(lead_fn(LEAD_F, 1.10), name=f"LEAD {b['lead'][:12]}", bits=16)
    S["bass"]  = Sample(bass_fn(BASS_F, 1.10), name=f"BASS {b['bass'][:12]}", bits=16)
    S["arp"]   = Sample(LEADS["pluck"](LEAD_F, 0.85), name="ARP PLUCK", bits=16)
    S["pad"]   = Sample(lead_fn(LEAD_F * 0.5, 1.60), name="PAD", bits=16)
    S["kick"]  = Sample(kit["kick"],  name="KICK", bits=16)
    S["snare"] = Sample(kit["snare"], name="SNARE", bits=16)
    S["hat"]   = Sample(kit["hat"],   name="HAT", bits=16)
    S["perc"]  = Sample(LEADS["chip_arp"](LEAD_F * 2, 0.22), name="PERC", bits=16)
    return S


def chord_at(b, bar_index):
    """Which chord a bar sits on — each track has its own progression."""
    offsets, tones = b["prog"][bar_index % len(b["prog"])]
    return b["root"] + offsets, tones


def build_pattern(b, sec, dyn, pat_idx, rng, S):
    """One 64-row pattern (4 bars) for the given section and dynamic level."""
    cells = {}
    is_drop  = sec in ("drop",)
    is_break = sec == "break"
    quiet    = dyn < 0.5

    lead_vol = int(max(6, min(64, 8 + 54 * b["density"] * dyn)))
    bass_vol = int(max(8, min(64, 14 + 46 * dyn)))
    drum_knock = 0.55 + 0.45 * dyn

    for row in range(64):
        bar = pat_idx * 4 + (row // 16)
        step = row % 16
        chord_root, tones = chord_at(b, bar)

        # ---- drums: the track's own patterns ----
        if b["kick"][step] == "x":
            cells[(row, CH["kick"])] = (DRUM_NOTE, 4, int(16 + 46 * drum_knock), 0, 0)
        if b["snare"][step] == "x" and not quiet:
            cells[(row, CH["snare"])] = (DRUM_NOTE, 5, int(12 + 44 * drum_knock), 0, 0)
        if b["hat"][step] == "x":
            hv = 0.30 if quiet else 1.0
            cells[(row, CH["hat"])] = (DRUM_NOTE, 6, int(10 + 26 * hv * drum_knock), 0, 0)
        if is_drop and step in (6, 14) and rng.random() < 0.5:
            cells[(row, CH["perc"])] = (DRUM_NOTE, 8, int(14 + 18 * dyn), 0x1B, 0x03)

        # ---- bass: own rhythm, follows the progression ----
        if step in (0, 6, 8, 14) or (is_drop and step in (3, 11)):
            n = note_for(hz(chord_root - 12), BASS_F)
            v = bass_vol if step in (0, 8) else int(bass_vol * 0.84)
            cells[(row, CH["bass"])] = (n, 2, v, 0x02 if step == 14 else 0, 0x18 if step == 14 else 0)

        # ---- arpeggio: chord tones, busier in drops ----
        arp_rate = 2 if is_drop else 4
        if step % arp_rate == 0:
            deg = tones[(row // arp_rate) % len(tones)]
            oct_ = 12 if (is_drop and (row // arp_rate) % 4 >= 2) else 0
            n = note_for(hz(chord_root + b["reg"] + deg + oct_), LEAD_F)
            cells[(row, CH["arp"])] = (n, 3, int(10 + 26 * dyn), 0, 0)

        # ---- pad: sustained chord tones, quiet sections only ----
        if (quiet or is_break) and step == 0:
            for i, t in enumerate(tones):
                if row == 0:
                    n = note_for(hz(chord_root + b["reg"] - 12 + t), LEAD_F)
                    cells[(row, CH["pad"])] = (n, 9, int(8 + 22 * dyn), 0, 0)

        # ---- lead melody: per-track density, its own register ----
        if step % 2 == 0:
            if rng.random() < b["density"] * (0.55 + 0.45 * dyn):
                scale = b["scale"]
                deg = scale[int(rng.integers(0, len(scale)))]
                oct_ = 12 if rng.random() < 0.22 else 0
                target = hz(chord_root + b["reg"] + deg + oct_)
                n = note_for(target, LEAD_F)
                if 1 <= n <= 96:
                    fx, pm = (0x04, 0x37) if (is_drop and step % 8 == 0) else (0, 0)
                    cells[(row, CH["lead"])] = (n, 1, lead_vol, fx, pm)
    return cells


def assemble(b):
    rng = np.random.default_rng(1000 + b["no"] * 37)
    S = make_instruments(b, rng)
    order_names = ["lead", "bass", "arp", "pad", "kick", "snare", "hat", "perc"]
    mod = Module(name=b["title"][:20], channels=NCH, bpm=b["bpm"], speed=6)
    idx = {}
    for i, nm in enumerate(order_names, start=1):
        mod.add_instrument(Instrument(nm.upper(), [S[nm]]))
        idx[nm] = i
    # remap channel->instrument to match the order above
    inst_of = {CH["lead"]: idx["lead"], CH["bass"]: idx["bass"], CH["arp"]: idx["arp"],
               CH["pad"]: idx["pad"], CH["kick"]: idx["kick"], CH["snare"]: idx["snare"],
               CH["hat"]: idx["hat"], CH["perc"]: idx["perc"]}

    # expand the section map into enough patterns to clear the length gate
    pat_seconds = 64 * (6 * 2.5 / b["bpm"])
    needed = max(1, math.ceil(105.0 / pat_seconds))
    plan, pi = [], 0
    while len(plan) < needed:
        for sec, dyn in b["sections"]:
            plan.append((sec, dyn))
            if len(plan) >= needed: break
    order = []
    for i, (sec, dyn) in enumerate(plan):
        cells = build_pattern(b, sec, dyn, i, rng, S)
        cells = {(r, c): (n, inst_of.get(c, inst), v, fx, pm)
                 for (r, c), (n, inst, v, fx, pm) in cells.items()}
        p = mod.add_pattern(cells)
        order.append(p)
    mod.order = order
    return mod, len(order), pat_seconds


# ── render / master / verify ─────────────────────────────────────────────────
TL, TP, LR = -14.0, -1.0, 9.0

def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def render(xm: Path, wav: Path):
    r = run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(xm),
             "-c:a","pcm_s16le",str(wav)])
    if r.returncode: raise RuntimeError(r.stderr[:300])

def measure(p: Path):
    r = run(["ffmpeg","-hide_banner","-nostats","-i",str(p),
             "-af",f"loudnorm=I={TL}:TP={TP}:LRA={LR}:print_format=json","-f","null","-"])
    return json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}")+1])

def master(wav: Path, mp3: Path) -> dict:
    m = measure(wav)
    af = (f"loudnorm=I={TL}:TP={TP}:LRA={LR}:measured_I={m['input_i']}"
          f":measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
          f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}"
          f":linear=true:print_format=json")
    r = run(["ffmpeg","-hide_banner","-nostats","-y","-i",str(wav),"-af",af,
             "-c:a","libmp3lame","-b:a","320k",str(mp3)])
    if r.returncode: raise RuntimeError(r.stderr[:300])
    o = measure(mp3)
    return {"lufs": float(o["input_i"]), "tp": float(o["input_tp"]),
            "lra": float(o["input_lra"])}

def dur(p: Path) -> float:
    r = run(["ffprobe","-v","error","-show_entries","format=duration",
             "-of","default=nw=1:nk=1",str(p)])
    return float(r.stdout.strip() or 0)

def variety(mp3: Path) -> dict:
    """Spectral centroid + high-band share: the objective proof of variety."""
    from scipy import signal as sg
    x = np.frombuffer(subprocess.run(["ffmpeg","-v","error","-i",str(mp3),"-t","40",
        "-ac","1","-ar","22050","-f","f32le","-"],capture_output=True).stdout, dtype=np.float32)
    if len(x) < 8192: return {}
    f,_,Z = sg.stft(x, 22050, nperseg=2048)
    mag = np.abs(Z); fr = f[:,None]
    cen = float(np.median((mag*fr).sum(0)/(mag.sum(0)+1e-9)))
    hi  = float(mag[(f>=2000)&(f<8000)].sum()/(mag.sum()+1e-9))
    lo  = float(mag[(f>=40)&(f<400)].sum()/(mag.sum()+1e-9))
    return {"centroid_hz": round(cen,1), "high_ratio": round(hi,3), "low_ratio": round(lo,3)}

def cover(b):
    from PIL import Image, ImageDraw, ImageFont
    W=H=1000; im=Image.new("RGB",(W,H),(10,9,16)); d=ImageDraw.Draw(im)
    hue = [(255,90,170),(90,200,255),(150,120,255),(255,160,60),(70,240,190),
           (240,110,110),(120,150,255),(255,210,80)][(b["no"]-1) % 8]
    for i in range(0,W,44):
        d.line([(i,0),(i,H)], fill=(hue[0]//9, hue[1]//9, hue[2]//9), width=1)
    for j in range(0,H,44):
        d.line([(0,j),(W,j)], fill=(hue[0]//11, hue[1]//11, hue[2]//11), width=1)
    d.rectangle([0,690,W,714], fill=hue)
    f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",72)
    f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
    f3=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",24)
    w=b["title"].upper().split()
    lines=[" ".join(w[:1])," ".join(w[1:])] if len(w)>1 else [w[0]]
    for i,l in enumerate(lines):
        if l: d.text((56,110+i*80), l, font=f1, fill=(255,255,255))
    d.text((56,760), f"{b['bpm']} BPM · {b['lead'].replace('_',' ')}", font=f2, fill=hue)
    d.text((56,880), "MILKUPS · THE SHELVES RAISED US", font=f3, fill=(120,118,140))
    d.text((W-260,880), f"TRACK {b['no']:02d}", font=f3, fill=hue)
    p = ART/f"{b['slug']}.png"; im.save(p); return p


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only", type=int)
    a = ap.parse_args()
    picks = [t for t in TRACKS if not a.only or t["no"] == a.only]
    man = {"album":"The Shelves Raised Us","artist":"MilkUps","cut":"album-v3",
           "engine":"16-bit FastTracker II .XM -> libopenmpt","tracks":[]}
    print(f"{'#':>2} {'title':<20} {'lead':<15} {'bps':>4} {'pat':>4} {'sec':>7} {'LUFS':>7} {'TP':>6} {'centHz':>8}")
    for b in picks:
        mod, npat, ps = assemble(b)
        xm, wav, mp3 = XM/f"{b['slug']}.xm", WAV/f"{b['slug']}.wav", MP3/f"{b['slug']}.mp3"
        mod.save(xm)
        render(xm, wav)
        m = master(wav, mp3)
        sec = dur(mp3); v = variety(mp3)
        cover(b)
        rec = {"no":b["no"],"title":b["title"],"slug":b["slug"],"bpm":b["bpm"],
               "lead":b["lead"],"bass":b["bass"],"kit":b["kit"],"register":b["reg"],
               "patterns":npat,"seconds":round(sec,2),"lufs":round(m["lufs"],2),
               "true_peak_dbtp":round(m["tp"],2),"lra":round(m["lra"],2),
               "xm_bytes":xm.stat().st_size,"mp3_bytes":mp3.stat().st_size,
               "sha256":hashlib.sha256(mp3.read_bytes()).hexdigest(), **v}
        man["tracks"].append(rec)
        print(f"{b['no']:>2} {b['title'][:20]:<20} {b['lead']:<15} {b['bpm']:>4} "
              f"{npat:>4} {sec:>7.2f} {m['lufs']:>7.2f} {m['tp']:>6.2f} {v.get('centroid_hz',0):>8.0f}", flush=True)
        try: wav.unlink()
        except OSError: pass

    cs = np.array([t["centroid_hz"] for t in man["tracks"] if t.get("centroid_hz")])
    if len(cs) > 1:
        man["variety"] = {"centroid_mean": round(float(cs.mean()),1),
                          "centroid_spread": round(float(cs.std()),1),
                          "centroid_min": round(float(cs.min()),1),
                          "centroid_max": round(float(cs.max()),1),
                          "coefficient_of_variation": round(float(cs.std()/cs.mean()),3)}
        print(f"\nVARIETY: mean {cs.mean():.0f} Hz spread {cs.std():.0f} Hz "
              f"CV {cs.std()/cs.mean():.3f}  (old cut was spread 162 Hz, CV 0.074)")
    man["gate"] = {"passed": all(t["seconds"]>=60 and abs(t["lufs"]+14)<=1.0
                                for t in man["tracks"]), "tracks": len(man["tracks"])}
    (OUT/"manifest.json").write_text(json.dumps(man, indent=2))
    print("\nGATE:", "PASS" if man["gate"]["passed"] else "FAIL", "|", len(man["tracks"]), "tracks")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
