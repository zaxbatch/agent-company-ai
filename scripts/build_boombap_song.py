#!/usr/bin/env python3
"""build_boombap_song.py — 'Dust on the Shelf', a boom-bap track.

Built to prove the SnowSnakes standard is a BAR and not a template: this clears
every requirement in content/snowsnakes/songs/STANDARD.md while sounding nothing
like "Shelves After Dark".

Boom-bap is defined by the BACKBEAT, not a pulse:
  * kick on 1 and 3, never four-on-the-floor
  * heavy snare on 2 and 4  (the whole genre hangs off this)
  * swung (shuffled) hi-hats, not straight eighths
  * dusty minor-7th chords, vinyl noise floor
  * laid-back walking bass
versus disco's relentless 4/4 kick and offbeat string stabs.

Everything synthesized in-process. No samples. Deterministic.
"""
from __future__ import annotations
import argparse, json, math, subprocess, sys, urllib.request, urllib.error, uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import songkit as sk
from songkit import SR, hz, place, saw, tri, sine, sq, adsr, exp_decay, noise

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "snowsnakes" / "songs"
BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
CLOUD, PRESET = "r6natkse", "snowsnakes_unsigned"

BPM = 92
SPB = 60.0 / BPM
BAR = 4 * SPB
BARS = 26                     # ~68 s
TITLE = "Dust on the Shelf"
SWING = 0.62                  # triplet-ish shuffle on the 8ths (straight = 0.50)

# Dm9 - Bb maj7 - Gmin7 - A7  (jazzy minor, entirely unlike the disco changes)
PROG = [50, 46, 43, 45]


def swung(t_bar, eighth):
    """Position of the eighth-note, shuffled. eighth 0..7."""
    if eighth % 2 == 0:
        return t_bar + (eighth // 2) * SPB
    return t_bar + (eighth // 2) * SPB + SPB * SWING * 2


# ── voices: dusty, warm, intentionally NOT the disco palette ─────────────────
def dusty_kick():
    """808-ish boom with a soft attack -- no click, unlike the disco kick."""
    n = int(0.42 * SR)
    t = np.arange(n) / SR
    f = 96 * np.exp(-19 * t) + 42
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    return (np.tanh(body * 1.25) * exp_decay(n, 5.2) * 0.98).astype(np.float32)


def fat_snare(rng):
    """Loud, roomy backbeat snare -- the anchor of the genre."""
    n = int(0.34 * SR)
    nz = noise(rng, 0.34)[:n] * exp_decay(n, 13)
    tone = np.sin(2 * np.pi * 178 * np.arange(n) / SR) * exp_decay(n, 20)
    room = np.concatenate([np.zeros(int(0.018 * SR), dtype=np.float32),
                           (nz * 0.30)[:n - int(0.018 * SR)]])
    return ((nz * 0.78 + tone * 0.42 + room) * 0.62).astype(np.float32)


def dusty_hat(rng, open_=False):
    dur = 0.16 if open_ else 0.035
    n = int(dur * SR)
    nz = noise(rng, dur)[:n]
    nz = np.diff(np.concatenate([[0], nz]))
    return (nz * exp_decay(n, 10 if open_ else 78) * (0.10 if open_ else 0.085)).astype(np.float32)


def rhodes(midis, dur, gain=0.115):
    """Electric-piano-ish chord: sine + soft odd harmonics, long decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        f = hz(m)
        v = (sine(2 * np.pi * f * t) + 0.28 * sine(2 * np.pi * f * 2.01 * t)
             + 0.12 * sine(2 * np.pi * f * 3.02 * t) + 0.06 * tri(2 * np.pi * f * 0.5 * t))
        out += (v * adsr(n, 0.008, 0.30, 0.34, 0.60) / len(midis)).astype(np.float32)
    return (out * gain).astype(np.float32)


def upright_bass(midi, dur, gain=0.30):
    """Soft-attack upright: fundamental-heavy, quick natural decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    v = 0.85 * sine(2 * np.pi * f * t) + 0.22 * tri(2 * np.pi * f * t) + 0.10 * saw(2 * np.pi * f * t)
    return (np.tanh(v * adsr(n, 0.012, 0.14, 0.40, 0.10) * 1.1) * gain).astype(np.float32)


def vinyl(rng, dur):
    """Surface noise + the occasional crackle. The 'dusty' in the title."""
    n = int(dur * SR)
    hiss = rng.normal(0, 0.0022, n).astype(np.float32)
    idx = rng.choice(n, size=int(dur * 7), replace=False)
    hiss[idx] += rng.uniform(-0.05, 0.05, size=len(idx)).astype(np.float32)
    return hiss


def arrange():
    total = BARS * BAR + 1.5
    buf = np.zeros(int(total * SR), dtype=np.float32)
    rng = np.random.default_rng(1992)
    place(buf, 0, vinyl(rng, min(total, BARS * BAR)), 1.0)

    for bar in range(BARS):
        t0 = bar * BAR
        root = PROG[bar % 4]
        intro = bar < 2
        full = 4 <= bar < 22

        # ── backbeat: kick 1 & 3, SNARE 2 & 4 (the genre's spine) ──
        place(buf, t0, dusty_kick(), 1.0)                      # beat 1
        place(buf, t0 + 2 * SPB, dusty_kick(), 0.94)            # beat 3
        if bar >= 2:                                           # ghost kick, syncopated
            place(buf, t0 + 2.75 * SPB, dusty_kick(), 0.42)
        if bar >= 1:
            place(buf, t0 + 1 * SPB, fat_snare(rng), 1.0)       # beat 2  <- backbeat
            place(buf, t0 + 3 * SPB, fat_snare(rng), 1.0)       # beat 4  <- backbeat
            if bar % 4 == 3:
                place(buf, t0 + 3.5 * SPB, fat_snare(rng), 0.35)  # pickup

        # ── shuffled hats (not straight -- this is the genre) ──
        for e in range(8):
            t = swung(t0, e)
            if e % 2 == 0 or rng.random() < 0.55:
                place(buf, t, dusty_hat(rng, open_=(e == 7)), 0.9 if e % 2 == 0 else 0.5)

        # ── walking upright bass, laid back ──
        if not intro or bar == 1:
            for beat, off, oct_ in ((0, 0.0, 0), (1, 0.0, 7), (2, 0.0, 0), (3, 0.0, 5)):
                m = root - 24 + oct_
                place(buf, t0 + beat * SPB + off, upright_bass(m, SPB * 0.78), 1.0)
            if bar % 2 == 1:
                place(buf, swung(t0, 7), upright_bass(root - 24 + 10, SPB * 0.4), 0.8)

        # ── dusty Rhodes chords ──
        if bar >= 2:
            tones = [root - 12, root - 8, root - 5, root - 3]     # min7 / maj7 colours
            place(buf, t0, rhodes(tones, BAR * 0.92), 1.0)
            if bar % 4 in (1, 3):
                place(buf, t0 + 2.5 * SPB, rhodes(tones, SPB * 1.1), 0.55)

        # ── sparse horn-ish stabs, only in the full section ──
        if full and bar % 4 == 2:
            for i, m in enumerate([root + 4, root + 7, root + 11]):
                place(buf, t0 + (1.5 + i * 0.25) * SPB, sk.brass(m, SPB * 0.30, 0.085), 1.0)

    # ── master + a touch more dust ──
    out = sk.master(buf, peak=0.88, drive=1.10, fade_in=0.4, fade_out=2.2)
    return out


def make_cover(path):
    W = H = 1000
    im = Image.new("RGB", (W, H), (34, 26, 20))
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for _ in range(2600):                                   # dusty speckle
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        v = int(rng.integers(26, 60))
        d.point((x, y), fill=(v + 16, v + 8, v))
    for _ in range(90):                                     # scratches
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        d.line([(x, y), (x + int(rng.integers(-40, 40)), y + int(rng.integers(-8, 8)))],
               fill=(88, 74, 58), width=1)
    cx, cy, r = W // 2, 430, 268                            # vinyl record
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(22, 18, 16), outline=(120, 104, 84), width=5)
    for i in range(7):
        rr = int(r * (0.36 + i * 0.09))
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=(52, 44, 38), width=3)
    d.ellipse([cx - 46, cy - 46, cx + 46, cy + 46], fill=(196, 154, 74), outline=(30, 24, 20), width=5)
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(22, 18, 16))
    f1, f2 = _font(96, True), _font(38, False)
    t1 = "DUST ON"; t2 = "THE SHELF"
    for txt, yy, col, fnt in ((t1, 742, (238, 224, 200), f1), (t2, 838, (196, 154, 74), f1)):
        w = d.textlength(txt, font=fnt)
        d.text(((W - w) / 2, yy), txt, font=fnt, fill=col, stroke_width=7, stroke_fill=(16, 12, 10))
    sub = "MILKUPS  ·  BOOM BAP  92 BPM"
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, 946), sub, font=f2, fill=(150, 132, 108))
    path.parent.mkdir(parents=True, exist_ok=True); im.save(path); return path


def _font(sz, bold):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()


def upload(path, rtype):
    b = "----zdotbb" + uuid.uuid4().hex
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nsnowsnakes\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {'audio/mpeg' if rtype=='video' else 'image/png'}\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.loads(r.read().decode())


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token: h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode() if data else None,
                                 method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--as", dest="author", default="leo_park")
    a = ap.parse_args()

    wav = sk.write_wav(arrange(), OUT / "dust-on-the-shelf.wav")
    secs = sk.duration(wav)
    mp3 = OUT / "dust-on-the-shelf.mp3"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
                    "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)], check=True)
    cover = make_cover(OUT / "dust-on-the-shelf-cover.png")
    print(f"built: {secs:.2f}s  wav {wav.stat().st_size//1024}KB  mp3 {mp3.stat().st_size//1024}KB")

    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_song.py"), str(wav),
                        "--genre", "boombap", "--bpm", str(BPM), "--cover", str(cover),
                        "--catalog", str(OUT)], capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("GATE FAILED -- not posting")
        return 1
    if not a.post:
        return 0
    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    tok = api("/auth/login", {"username": a.author, "password": users[a.author]["password"]},
              method="POST")[1]
    tok = tok.get("token") if isinstance(tok, dict) else None
    au = upload(mp3, "video").get("secure_url")
    cu = upload(cover, "image").get("secure_url")
    st, res = api("/songs", {"title": TITLE, "audio_url": au, "cover_url": cu}, token=tok, method="POST")
    print(f"{'ok ' if st==201 else '!! '}POST /songs as {a.author} -> HTTP {st} id={res.get('id') if isinstance(res,dict) else res}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
