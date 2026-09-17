#!/usr/bin/env python3
"""build_disco_song.py — make a real DISCO track from scratch and post it to SnowSnakes.

Disco is not "fast synthwave". The genre is defined by specific parts, so this
builds all of them explicitly:

  * four-on-the-floor kick, every beat, no exceptions  (the disco pulse)
  * open hi-hat on the offbeat eighths                 (the shuffle)
  * string stabs on the offbeats of 2 and 4            (the classic disco hook)
  * funky octave bassline, syncopated                  (the engine)
  * clav/rhythm guitar 16th skanks                     (the texture)
  * brass-ish lead hook, and a rising disco string run (the release)

Everything is synthesized in-process (oscillators + noise), so there are no
external samples. Rendered deterministically from fixed seeds.

Usage:
  python3 scripts/build_disco_song.py                 # build wav + cover only
  python3 scripts/build_disco_song.py --post          # build, upload, post
  python3 scripts/build_disco_song.py --post --as sam_rivera
"""
from __future__ import annotations
import argparse, json, math, random, struct, sys, urllib.request, urllib.error, uuid
import base64
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "snowsnakes" / "songs"
BASE = "https://snowsnakes.zerric.xyz/api"
USERS = ROOT / ".snowsnakes_real_users.json"
CLOUD, PRESET = "r6natkse", "snowsnakes_unsigned"
SR = 44100

BPM = 118
SPB = 60.0 / BPM            # seconds per beat
BAR = 4 * SPB
BARS = 34                   # ~69 s
TITLE = "Shelves After Dark"

# A minor disco progression: Am - F - C - G   (i - VI - III - VII)
PROG = [57, 53, 60, 55]


def hz(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


# ── synthesis primitives (all math, no samples) ───────────────────────────────
def saw(ph):
    return 2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0


def sq(ph):
    return np.sign(np.sin(ph))


def tri(ph):
    return 2.0 * np.abs(2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0) - 1.0


def adsr(n, a, d, s, r):
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    si = max(n - ai - di - ri, 0)
    return np.concatenate([
        np.linspace(0, 1, ai, endpoint=False),
        np.linspace(1, s, di, endpoint=False),
        np.full(si, s),
        np.linspace(s, 0, ri),
    ])[:n]


def place(buf, t, sig, gain=1.0):
    i = int(t * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    if n > 0:
        buf[i:i + n] += sig[:n] * gain
    return buf


# ── the kit ───────────────────────────────────────────────────────────────────
def kick():
    n = int(0.30 * SR)
    t = np.arange(n) / SR
    f = 138 * np.exp(-30 * t) + 48
    body = np.sin(2 * np.pi * np.cumsum(f) / SR)
    click = np.exp(-260 * t) * 0.5
    return (np.tanh((body + click) * 1.5) * np.exp(-7.5 * t) * 0.95).astype(np.float32)


def hat(open_=False, rng=None):
    dur = 0.28 if open_ else 0.045
    n = int(dur * SR)
    rng = rng or np.random.default_rng(3)
    nz = rng.uniform(-1, 1, n)
    nz = np.diff(np.concatenate([[0], nz]))       # brighten
    dec = np.exp(-(9 if open_ else 65) * np.arange(n) / SR)
    return (nz * dec * (0.20 if open_ else 0.16)).astype(np.float32)


def clap(rng):
    n = int(0.20 * SR)
    out = np.zeros(n, dtype=np.float32)
    for k, off in enumerate((0.0, 0.011, 0.021)):  # the 3-burst disco clap
        s = int(off * SR)
        m = n - s
        nz = rng.uniform(-1, 1, m)
        out[s:s + m] += (nz * np.exp(-34 * np.arange(m) / SR) * (1.0 - k * 0.22)).astype(np.float32)
    return (out * 0.42).astype(np.float32)


def tamb(rng, dur=0.09):
    n = int(dur * SR)
    nz = rng.uniform(-1, 1, n)
    return (nz * np.exp(-38 * np.arange(n) / SR) * 0.13).astype(np.float32)


def string_stab(midis, dur=0.34, bright=1.0):
    """Sawtooth string section; the disco offbeat hook."""
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        f = hz(m)
        t = np.arange(n) / SR
        for det in (0.996, 1.0, 1.005, 1.011):
            out += saw(2 * np.pi * f * det * t).astype(np.float32) / 4
    e = adsr(n, 0.012, 0.08, 0.55, 0.18)
    return (out * e * 0.16 * bright).astype(np.float32)


def brass(midi, dur=0.55):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    v = (0.6 * saw(2 * np.pi * f * t) + 0.35 * sq(2 * np.pi * f * 1.002 * t)
         + 0.15 * tri(2 * np.pi * f * 0.5 * t))
    e = adsr(n, 0.01, 0.06, 0.7, 0.16)
    return (v * e * 0.15).astype(np.float32)


def bass_note(midi, dur, rng):
    """Syncopated octave funk bass -- saw + sub, quick decay."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(midi)
    v = 0.75 * saw(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 0.5 * t)
    e = adsr(n, 0.004, 0.10, 0.45, 0.07)
    return (np.tanh(v * e * 1.25) * 0.34).astype(np.float32)


def skank(midis, dur=0.10):
    """Rhythm-guitar 16th upstroke: short, thin, on the 'and'."""
    n = int(dur * SR)
    out = np.zeros(n, dtype=np.float32)
    for m in midis:
        t = np.arange(n) / SR
        out += (saw(2 * np.pi * hz(m) * t) * 0.5
                + sq(2 * np.pi * hz(m) * 1.004 * t) * 0.2).astype(np.float32)
    return (out * np.exp(-40 * np.arange(n) / SR) * 0.10).astype(np.float32)


# ── arrangement ──────────────────────────────────────────────────────────────
def arrange():
    total = BARS * BAR + 1.2
    buf = np.zeros(int(total * SR), dtype=np.float32)
    rng = np.random.default_rng(1979)

    def chord_of(bar):
        return PROG[bar % 4]

    for bar in range(BARS):
        t0 = bar * BAR
        root = chord_of(bar)
        # sections: 0-3 intro (drums+bass), 4-11 add strings, 12-27 full, 28-33 outro
        intro = bar < 4
        strings_in = bar >= 4
        full = 12 <= bar < 28

        # ── drums ──
        for beat in range(4):
            place(buf, t0 + beat * SPB, kick(), 1.0 if beat in (0, 2) else 0.86)
        if bar >= 2:                                   # clap on 2 and 4
            for beat in (1, 3):
                place(buf, t0 + beat * SPB, clap(rng), 0.85)
        for eighth in range(8):                        # hats: closed on beat, open offbeat
            t = t0 + eighth * SPB / 2
            if eighth % 2 == 0:
                place(buf, t, hat(False, rng), 0.8)
            else:
                place(buf, t, hat(True, rng), 0.62)
        for six in range(4):                           # tambourine 16ths
            place(buf, t0 + six * SPB / 4, tamb(rng), 0.7)

        # ── bass: octave funk, syncopated ──
        for step in range(8):
            t = t0 + step * SPB / 2
            if step in (0, 3, 4, 6):
                m = root - 24 + (12 if step in (3, 6) else 0)   # octave pops
                dur = SPB * (0.42 if step != 6 else 0.30)
                place(buf, t, bass_note(m, dur, rng), 1.0)
            elif step == 7 and bar % 2 == 1:
                place(buf, t, bass_note(root - 19, SPB * 0.3, rng), 0.8)  # turnaround

        # ── skanks on the "and" of each beat ──
        if bar >= 2:
            tones = [root - 12, root - 5, root - 1]
            for beat in range(4):
                place(buf, t0 + beat * SPB + SPB / 2, skank(tones), 0.9)

        # ── the disco string hook: offbeats of 2 and 4 ──
        if strings_in:
            stab = string_stab([root + 12, root + 15, root + 19, root + 24], 0.30)
            place(buf, t0 + SPB * 0.5, stab, 0.95)
            place(buf, t0 + SPB * 1.5, stab, 0.75)
            place(buf, t0 + SPB * 2.5, stab, 0.95)
            place(buf, t0 + SPB * 3.5, stab, 0.85)
            # long sustained string pad on the downbeat of each bar
            pad = string_stab([root, root + 7, root + 12, root + 19], SPB * 1.6, 0.55)
            place(buf, t0, pad, 0.5)

        # ── brass lead hook in the full section ──
        if full:
            hook = [(0, root + 24), (1.5, root + 27), (2, root + 31), (3, root + 24), (3.5, root + 22)]
            for off, m in hook:
                place(buf, t0 + off * SPB, brass(m, SPB * 0.42), 0.9)
            if bar % 8 == 7:                     # rising disco string run (the release)
                for i, m in enumerate([root + 12, root + 15, root + 19, root + 24, root + 27, root + 31]):
                    place(buf, t0 + (2 + i * 0.33) * SPB, string_stab([m], 0.22, 0.9), 1.0)

        # ── intro: keep it sparse, no strings yet ──
        if intro:
            buf[int(t0 * SR):int((t0 + BAR) * SR)] *= 1.0

    # ── master: mix, gentle compression, fade in/out ──
    peak = float(np.max(np.abs(buf))) or 1.0
    buf = buf / peak * 0.92
    buf = np.tanh(buf * 1.15).astype(np.float32)
    n_in, n_out = int(0.15 * SR), int(1.8 * SR)
    buf[:n_in] *= np.linspace(0, 1, n_in)
    buf[-n_out:] *= np.linspace(1, 0, n_out)
    return buf


def write_wav(buf, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(buf * 32767, -32768, 32767).astype("<i2")
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


# ── cover art (disco ball, made with the same flat style as the doodles) ─────
def make_cover(path):
    W = H = 1000
    im = Image.new("RGB", (W, H), (18, 8, 34))
    d = ImageDraw.Draw(im)
    for y in range(H):                                   # nightclub gradient
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(18 + 40 * t), int(8 + 6 * t), int(34 + 62 * t)))
    for i in range(22):                                  # light beams
        a = math.radians(-160 + i * 15)
        d.line([(W / 2, -60), (W / 2 + math.cos(a) * 1700, -60 + math.sin(a) * 1700)],
               fill=(255, 90, 190) if i % 2 else (90, 230, 255), width=7)
    cx, cy, r = W // 2, 300, 190                          # disco ball
    rng = random.Random(7)
    for gy in range(-r, r + 1, 26):                       # faceted tiles
        for gx in range(-r, r + 1, 26):
            if gx * gx + gy * gy <= r * r:
                s = 13
                light = math.hypot(gx, gy) / r
                v = int(235 - 120 * light + rng.randint(-26, 26))
                col = (min(255, v + 30), min(255, v + 10), min(255, v + 45))
                d.rectangle([cx + gx - s, cy + gy - s, cx + gx + s, cy + gy + s], fill=col)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255), width=9)
    d.rectangle([cx - 6, 96, cx + 6, cy - r], fill=(200, 200, 215))   # hanger
    f = font(92, True); f2 = font(44, False)
    t1, t2 = "SHELVES", "AFTER DARK"
    w1 = d.textlength(t1, font=f); w2 = d.textlength(t2, font=f)
    d.text(((W - w1) / 2, 560), t1, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(10, 6, 20))
    d.text(((W - w2) / 2, 660), t2, font=f, fill=(255, 94, 168), stroke_width=8, stroke_fill=(10, 6, 20))
    sub = "MILKUPS  ·  DISCO  118 BPM"
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, 790), sub, font=f2, fill=(94, 232, 255))
    d.rectangle([0, 900, W, 912], fill=(255, 94, 168))
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)
    return path


def font(sz, bold):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
         else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    try:
        return ImageFont.truetype(p, sz)
    except OSError:
        return ImageFont.load_default()


# ── upload + post ────────────────────────────────────────────────────────────
def upload(path, rtype):
    b = "----zdotdisco" + uuid.uuid4().hex
    body = b"".join([
        f"--{b}\r\nContent-Disposition: form-data; name=\"upload_preset\"\r\n\r\n{PRESET}\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"folder\"\r\n\r\nsnowsnakes\r\n".encode(),
        f"--{b}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\n"
        f"Content-Type: {'audio/mpeg' if rtype=='video' else 'image/png'}\r\n\r\n".encode(),
        path.read_bytes(), f"\r\n--{b}--\r\n".encode()])
    req = urllib.request.Request(f"https://api.cloudinary.com/v1_1/{CLOUD}/{rtype}/upload",
                                 data=body, method="POST",
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("   upload failed:", str(e)[:200]); return {}


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {"_err": e.read().decode()[:200]}
    except Exception as e:
        return None, {"_err": str(e)[:200]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--post", action="store_true")
    ap.add_argument("--as", dest="author", default="sam_rivera")
    ap.add_argument("--title", default=TITLE)
    a = ap.parse_args()

    print(f"[1/4] arranging '{a.title}' at {BPM} BPM, {BARS} bars")
    wav = write_wav(arrange(), OUT / "shelves-after-dark.wav")
    import wave
    with wave.open(str(wav)) as w:
        secs = w.getnframes() / w.getframerate()
    print(f"      {secs:.2f}s  {wav.stat().st_size//1024} KB")

    mp3 = OUT / "shelves-after-dark.mp3"
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav),
                    "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3)], check=True)
    cover = make_cover(OUT / "shelves-after-dark-cover.png")
    print(f"[2/4] mp3 {mp3.stat().st_size//1024} KB | cover {cover.name}")

    # independent audio check
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", str(mp3)],
                           capture_output=True, text=True).stdout.strip()
    vol = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(mp3), "-af", "volumedetect",
                          "-f", "null", "/dev/null"], capture_output=True, text=True).stderr
    peaks = [l.strip() for l in vol.splitlines() if "max_volume" in l or "mean_volume" in l]
    print(f"[3/4] ffprobe duration={probe}s | " + " | ".join(peaks))

    if not a.post:
        print("[4/4] not posted (pass --post)")
        return 0

    users = {u["username"]: u for u in json.loads(USERS.read_text())}
    tok = api("/auth/login", {"username": a.author,
                              "password": users[a.author]["password"]}, method="POST")[1]
    tok = tok.get("token") if isinstance(tok, dict) else None
    if not tok:
        sys.exit(f"FATAL: cannot log in as {a.author}")
    au = upload(mp3, "video").get("secure_url")
    cu = upload(cover, "image").get("secure_url")
    st, res = api("/songs", {"title": a.title, "audio_url": au, "cover_url": cu},
                  token=tok, method="POST")
    ok = st == 201 and isinstance(res, dict) and res.get("id")
    print(f"[4/4] {'ok ' if ok else '!! '}POST /songs as {a.author} -> HTTP {st} id={res.get('id') if isinstance(res,dict) else res}")
    ev = ROOT / ".agent-company-ai" / "disco_song_state.json"
    ev.write_text(json.dumps({"title": a.title, "bpm": BPM, "author": a.author,
                              "seconds": float(probe), "audio_url": au, "cover_url": cu,
                              "http": st, "id": res.get("id") if isinstance(res, dict) else None,
                              "live_peaks": peaks}, indent=1))
    print("evidence:", ev.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
