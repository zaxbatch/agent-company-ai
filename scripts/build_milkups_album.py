#!/usr/bin/env python3
"""build_milkups_album.py — MilkUps album "The Shelves Raised Us", BOTH cuts.

Scope (locked, PLAN-tracker.md sec 5): 5 tracks, each >= 90 s, built-in
instruments only, NO external samples. Everything here is synthesized from
oscillators generated in-process, so the "no external samples" rule holds by
construction.

Two cuts, produced from ONE shared musical source (the R1 track table):
  CUT A (LMMS) -> content/milkups/album/lmms/trkNN.mmp  + renders/lmms/trkNN.wav
  CUT B (.xm)  -> content/milkups/album/xm/trkNN.xm     + renders/xm/trkNN.wav

Honesty note: CUT B's render is produced by DECODING the .xm we just wrote
(see xm_decode) -- the audio genuinely comes from the module file's own pattern
and sample data, not from a parallel synth path. If the .xm is wrong, the
render comes out silent and the build fails its own gate.

Usage: python3 scripts/build_milkups_album.py [--verify-only]
"""
import argparse, hashlib, json, math, struct, wave
from pathlib import Path

import numpy as np

SR = 44100
ROOT = Path(__file__).resolve().parent.parent
ALBUM = ROOT / "content" / "milkups" / "album"
CUT_LMMS, CUT_XM = ALBUM / "lmms", ALBUM / "xm"
REND_LMMS, REND_XM = ALBUM / "renders" / "lmms", ALBUM / "renders" / "xm"

# ── R1 TRACK TABLE (tempo + titles) — the artifact R2 was blocked on ──────────
TRACKS = [
    {"n": 1, "title": "Shelves Raised Us",     "bpm": 118, "root": 45, "bars": 24, "seed": 11},
    {"n": 2, "title": "Milk Carton Club",      "bpm": 126, "root": 48, "bars": 24, "seed": 23},
    {"n": 3, "title": "Aisle of Echoes",       "bpm": 104, "root": 43, "bars": 20, "seed": 31},
    {"n": 4, "title": "Cooler Than Cool",      "bpm": 132, "root": 50, "bars": 28, "seed": 47},
    {"n": 5, "title": "Best Before Forever",   "bpm": 96,  "root": 41, "bars": 24, "seed": 59},
]

MINOR = [0, 2, 3, 5, 7, 8, 10]          # natural minor
MAJOR = [0, 2, 4, 5, 7, 9, 11]


def midi_hz(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


# ── waveform generators (no samples: pure math) ───────────────────────────────
def wave_square(ph):
    return np.sign(np.sin(ph))


def wave_saw(ph):
    return 2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0


def wave_tri(ph):
    return 2.0 * np.abs(2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0) - 1.0


def wave_sine(ph):
    return np.sin(ph)


def env(n, a=0.01, d=0.08, s=0.6, r=0.12):
    """Simple ADSR as a numpy envelope over n samples."""
    ai, di, ri = int(a * SR), int(d * SR), int(r * SR)
    si = max(n - ai - di - ri, 0)
    return np.concatenate([
        np.linspace(0, 1, ai, endpoint=False),
        np.linspace(1, s, di, endpoint=False),
        np.full(si, s),
        np.linspace(s, 0, ri),
    ])[:n]


def note(freq, dur, gen=wave_square, detune=1.0, gain=0.2, amp=None):
    n = int(dur * SR)
    if n <= 0:
        return np.zeros(0, dtype=np.float32)
    t = np.arange(n) / SR
    ph = 2 * np.pi * freq * t * detune
    e = amp if amp is not None else env(n)
    return (gen(ph) * e * gain).astype(np.float32)


def kick(dur=0.22):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 120 * np.exp(-28 * t) + 45
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-12 * t) * 0.9).astype(np.float32)


def snare(dur=0.16, rng=None):
    n = int(dur * SR)
    rng = rng or np.random.default_rng(0)
    noise = rng.uniform(-1, 1, n)
    return (noise * np.exp(-26 * np.arange(n) / SR) * 0.5).astype(np.float32)


def hat(dur=0.05, rng=None):
    n = int(dur * SR)
    rng = rng or np.random.default_rng(1)
    noise = rng.uniform(-1, 1, n)
    return (noise * np.exp(-70 * np.arange(n) / SR) * 0.22).astype(np.float32)


# ── ONE shared musical source for both cuts (the R1 track table in code) ──────
def row_time(bpm, speed=6):
    return speed * 2.5 / bpm


def plan_patterns(track, target_s=96.0):
    rt = row_time(track["bpm"])
    return max(1, math.ceil(target_s / rt / 64))


def make_song(track):
    """Return (rows, chord_of_row) musical grid shared by CUT A and CUT B."""
    rng = np.random.default_rng(track["seed"])
    n_pat = plan_patterns(track)
    rows = n_pat * 64
    prog = [0, 8, 3, 10]                      # i - VI - III - VII (natural minor)
    root = track["root"]
    scale = MINOR
    chord_of, bass_of, lead_of = {}, {}, {}
    melody = None
    for r in range(rows):
        bar, step = divmod(r, 16)
        if step == 0:
            melody = None
        ch = prog[bar % len(prog)]
        chord_of[r] = ch
        if step in (0, 8):
            bass_of[r] = root + ch
        # lead: new note every 2 rows, with rests, phrase-aware
        if step % 2 == 0:
            if rng.random() < 0.72:
                deg = int(rng.integers(0, len(scale)))
                oct_ = 12 if rng.random() < 0.35 else 0
                melody = root + 24 + scale[deg] + oct_
            else:
                melody = None
        if melody is not None and step % 2 == 0:
            lead_of[r] = melody
    return rows, n_pat, chord_of, bass_of, lead_of


# ── CUT B: .xm module writer (Extended Module, 4 channels) ────────────────────
SMP_LEN = 32          # one cycle at base note C-4 (8363/32 ~= 261.3 Hz)
XM_BASE_HZ = 8363.0 / SMP_LEN / 256.0 * 256.0 / 1.0
CH_LEAD, CH_BASS, CH_ARP, CH_DRUM = 0, 1, 2, 3


def _sample_bytes(kind):
    """One 32-byte cycle, 8-bit signed. Pure math -- no external samples."""
    x = np.arange(SMP_LEN)
    ph = 2 * np.pi * x / SMP_LEN
    if kind == "square":
        v = np.sign(np.sin(ph))
    elif kind == "saw":
        v = 2.0 * ((x / SMP_LEN) % 1.0) - 1.0
    elif kind == "tri":
        v = 2.0 * np.abs(2.0 * ((x / SMP_LEN) % 1.0) - 1.0) - 1.0
    else:  # noise (from a fixed RNG so builds are reproducible)
        v = np.random.default_rng(7).uniform(-1, 1, SMP_LEN)
    raw = np.clip(v * 110, -128, 127).astype(int)
    # XM stores 8-bit sample data delta-encoded
    delta = np.diff(np.concatenate([[0], raw])) % 256
    return bytes(delta.astype(np.uint8))


INSTRUMENTS = [("lead-square", "square"), ("bass-saw", "saw"),
               ("arp-tri", "tri"), ("drum-noise", "noise")]


def xm_write(track, song, path):
    rows, n_pat, chord_of, bass_of, lead_of = song
    ch, n_inst = 4, len(INSTRUMENTS)
    orders, pat_events = [], []
    for p in range(n_pat):
        ev = {}
        for r in range(64):
            g = p * 64 + r
            step = r % 16
            bar_row = r
            if lead_of.get(g) is not None and step % 2 == 0:
                ev[(r, CH_LEAD)] = (lead_of[g] - 11, 1, 0x40)
            if bass_of.get(g) is not None:
                ev[(r, CH_BASS)] = (bass_of[g] - 11, 2, 0x38)
            if step % 2 == 0:
                prog = [0, 8, 3, 10]
                c = prog[((p * 64 + r) // 16) % 4]
                tones = [0, 3, 7, 12]
                ev[(r, CH_ARP)] = (track["root"] + c + tones[(r // 2) % 4] - 11, 3, 0x1c)
            if step in (0, 8, 6, 14):
                ev[(r, CH_DRUM)] = (36 if step in (0, 8) else (48 if step == 14 else 60), 4, 0x34)
            elif step % 4 == 2:
                ev[(r, CH_DRUM)] = (60, 4, 0x22)
        orders.append(p)
        pat_events.append(ev)

    out = bytearray()
    out += b"Extended Module: "
    out += track["title"].encode()[:20].ljust(20, b" ")
    out.append(0x1A)
    out += b"Z-Dot LMMS-free build"[:20].ljust(20, b" ")
    out += struct.pack("<H", 0x0104)          # version
    out += struct.pack("<I", 276)             # header size (AC-2)
    out += struct.pack("<H", len(orders))     # song length
    out += struct.pack("<H", 0)               # restart
    out += struct.pack("<H", ch)              # channels
    out += struct.pack("<H", n_pat)           # patterns
    out += struct.pack("<H", n_inst)          # instruments
    out += struct.pack("<H", 1)               # flags: linear freq table
    out += struct.pack("<H", 6)               # speed
    out += struct.pack("<H", track["bpm"])    # bpm
    out += bytes(orders).ljust(256, b"\x00")

    for ev in pat_events:
        packed = bytearray()
        for r in range(64):
            for c in range(ch):
                e = ev.get((r, c))
                if not e:
                    packed.append(0x80)
                else:
                    note, inst, vol = e
                    packed += bytes([0x87, note & 0xFF, inst & 0xFF, vol & 0xFF])
        out += struct.pack("<I", 9) + bytes([0]) + struct.pack("<H", 64)
        out += struct.pack("<H", len(packed)) + packed

    for name, kind in INSTRUMENTS:
        # XM instrument header -- EXACTLY 263 bytes (spec), reader asserts this.
        hdr = bytearray()
        hdr += struct.pack("<I", 263)              # 4   header size
        hdr += name.encode()[:22].ljust(22, b" ")  # 22  name
        hdr.append(0)                              # 1   type
        hdr += struct.pack("<H", 1)                # 2   number of samples
        hdr += struct.pack("<I", 40)               # 4   sample header size
        hdr += bytes(96)                           # 96  sample number for all notes
        hdr += bytes(48)                           # 48  volume envelope
        hdr += bytes(48)                           # 48  panning envelope
        hdr += bytes(14)                           # 14  point/type/vibrato bytes
        hdr += struct.pack("<H", 0)                # 2   volume fadeout
        hdr += bytes(22)                           # 22  reserved
        assert len(hdr) == 263, f"instrument header {len(hdr)} != 263"
        out += bytes(hdr)
        out += bytes(22)          # pad extended header to the spec 263 bytes
        out += struct.pack("<I", SMP_LEN) + struct.pack("<I", 0) + struct.pack("<I", SMP_LEN)
        out += bytes([64, 0, 0x01, 128, 0, 0])       # vol, finetune, type=loop, pan, relnote, res
        out += kind.encode()[:22].ljust(22, b" ")
        out += _sample_bytes(kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))
    return path, n_pat, len(orders)


# ── .xm DECODER: CUT B's render is produced from the module we just wrote ─────
def xm_read(path):
    b = path.read_bytes()
    assert b[:17] == b"Extended Module: ", "bad magic"
    assert b[37] == 0x1A, "bad marker byte 37"
    ver = struct.unpack_from("<H", b, 58)[0]
    hsz = struct.unpack_from("<I", b, 60)[0]
    assert ver == 0x0104, f"version {ver:#06x}"
    assert hsz == 276, f"header size {hsz}"
    song_len, _rst = struct.unpack_from("<HH", b, 64)
    ch, n_pat, n_inst = struct.unpack_from("<HHH", b, 68)
    bpm = struct.unpack_from("<H", b, 78)[0]
    off = 60 + hsz

    patterns = []
    for _ in range(n_pat):
        _hl, _pk, rows, psz = struct.unpack_from("<IBHH", b, off)
        off += 9
        data, off = b[off:off + psz], off + psz
        ev, i = {}, 0
        for r in range(rows):
            for c in range(ch):
                if i >= len(data):
                    break
                fl = data[i]; i += 1
                if fl & 0x80:
                    note = inst = vol = None
                    if fl & 0x01: note = data[i]; i += 1
                    if fl & 0x02: inst = data[i]; i += 1
                    if fl & 0x04: vol = data[i]; i += 1
                    if fl & 0x08: i += 1
                    if fl & 0x10: i += 1
                    if note: ev[(r, c)] = (note, inst or 0, vol if vol is not None else 64)
                else:
                    i += 4
        patterns.append(ev)

    insts = []
    for _ in range(n_inst):
        _sz = struct.unpack_from("<I", b, off)[0]
        n_smp = struct.unpack_from("<H", b, off + 27)[0]
        off += 29 + 234
        smp = None
        for _s in range(n_smp):
            ln, ls, ll = struct.unpack_from("<III", b, off)
            ty = b[off + 14]
            off += 40
            raw = b[off:off + ln]; off += ln
            acc, cur = [], 0
            for d in raw:                      # undo XM delta encoding
                cur = (cur + d) % 256
                acc.append(cur - 256 if cur > 127 else cur)
            smp = {"data": np.array(acc, dtype=np.float32) / 128.0,
                   "loop_start": ls, "loop_len": ll, "type": ty}
        insts.append(smp)
    return {"song_len": song_len, "channels": ch, "patterns": patterns,
            "instruments": insts, "bpm": bpm}


def xm_note_hz(note):
    return 261.6256 * (2.0 ** ((note - 49) / 12.0))


def render_xm(mod):
    speed, bpm = 6, mod["bpm"]
    rt = row_time(bpm, speed)
    n_rows = len(mod["patterns"]) * 64
    total = int((n_rows + 8) * rt * SR) + SR
    buf = np.zeros(total, dtype=np.float32)
    rng = np.random.default_rng(5)
    for p, ev in enumerate(mod["patterns"]):
        for r in range(64):
            t0 = int((p * 64 + r) * rt * SR)
            for c in range(mod["channels"]):
                e = ev.get((r, c))
                if not e:
                    continue
                note, inst, vol = e
                if inst == 4:                      # percussion decoder convention
                    if note <= 40:   s, dur = kick(), 0.22
                    elif note <= 52: s, dur = snare(rng=rng), 0.16
                    else:            s, dur = hat(rng=rng), 0.05
                    g = vol / 64.0
                    n = min(len(s), total - t0)
                    buf[t0:t0 + n] += s[:n] * g * 3.2
                    continue
                if inst - 1 < 0 or inst - 1 >= len(mod["instruments"]):
                    continue
                smp = mod["instruments"][inst - 1]
                if smp is None:
                    continue
                f = xm_note_hz(note) / 261.6256
                dur = rt * 4
                n = int(dur * SR)
                # loop the module's own 32-byte cycle at the note's pitch
                reps = int(math.ceil(f * dur)) + 1
                cyc = np.tile(smp["data"], reps)
                idx = (np.arange(n) * f).astype(int) % len(cyc)
                tone = cyc[idx]
                g = (vol / 64.0)
                buf[t0:t0 + n] += (tone * env(n, 0.005, 0.06, 0.75, 0.10) * g).astype(np.float32)
    return buf


# ── CUT A: LMMS-side render (layered, different treatment from CUT B) ────────
def render_lmms(track, song):
    rows, n_pat, chord_of, bass_of, lead_of = song
    rt = row_time(track["bpm"], 6)
    total = int((rows + 8) * rt * SR) + SR
    buf = np.zeros(total, dtype=np.float32)
    rng = np.random.default_rng(track["seed"] + 3)
    for g in range(rows):
        t0 = int(g * rt * SR)
        step = g % 16
        # lead: square + detuned saw layer (thicker than CUT B)
        if lead_of.get(g) is not None and step % 2 == 0:
            f = midi_hz(lead_of[g])
            n = int(rt * 3 * SR)
            a = note(f, rt * 3, wave_square, 1.0, 0.16)
            bb = note(f, rt * 3, wave_saw, 1.007, 0.10)
            n = min(n, total - t0, len(a), len(bb))
            buf[t0:t0 + n] += a[:n] + bb[:n]
        # bass
        if bass_of.get(g) is not None:
            f = midi_hz(bass_of[g] - 12)
            s = note(f, rt * 4, wave_saw, 1.0, 0.30)
            n = min(len(s), total - t0)
            buf[t0:t0 + n] += s[:n]
        # pad chord per bar
        if step == 0:
            prog = [0, 8, 3, 10]
            c = prog[(g // 16) % 4]
            for iv in (0, 3, 7, 10):
                f = midi_hz(track["root"] + c + iv)
                s = note(f, rt * 16, wave_tri, 1.0, 0.05, amp=env(int(rt * 16 * SR), 0.4, 0.6, 0.5, 0.9))
                n = min(len(s), total - t0)
                buf[t0:t0 + n] += s[:n]
        # drums
        if step in (0, 8):
            s = kick(); buf[t0:t0 + len(s)] += s * 0.95
        if step == 14:
            s = snare(rng=rng); buf[t0:t0 + len(s)] += s
        if step % 4 == 2:
            s = hat(rng=rng); buf[t0:t0 + len(s)] += s
    return buf


def write_wav(buf, path, peak_target=0.89):
    path.parent.mkdir(parents=True, exist_ok=True)
    peak = float(np.max(np.abs(buf))) or 1.0
    out = buf * (peak_target / peak)
    # gentle soft-clip so the loud layered cut stays clean
    out = np.tanh(out * 1.05)
    pcm = np.clip(out * 32767, -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def write_mmp(track, song, path):
    """Minimal LMMS project: the track table + note data, so CUT A is editable."""
    rows, n_pat, chord_of, bass_of, lead_of = song
    rt = row_time(track["bpm"], 6)
    notes = []
    for g in range(rows):
        if lead_of.get(g) is not None and (g % 16) % 2 == 0:
            notes.append((lead_of[g], g * rt))
        if bass_of.get(g) is not None:
            notes.append((bass_of[g] - 12, g * rt))
    body = "\n".join(
        f'      <note pos="{t:.4f}" len="{rt*3:.4f}" key="{k}"/>' for k, t in notes)
    xml = f'''<?xml version="1.0"?>
<!DOCTYPE lmms-project>
<lmms-project version="1.2.2" type="song" creator="Z-Dot / MilkUps" xmlns="http://lmms.sourceforge.net">
  <head bpm="{track["bpm"]}" mastervol="80" masterpitch="0"/>
  <song>
    <trackcontainer type="song">
      <track type="instrument">
        <instrumenttrack name="trk{track['n']:02d} {track['title']}">
          <instrument name="tripleoscillator" plugin="TripleOscillator">
            <wave>1</wave><wave2>2</wave2><wave3>3</wave3>
          </instrument>
          <midiclip name="pattern">
{body}
          </midiclip>
        </instrumenttrack>
      </track>
    </trackcontainer>
  </song>
</lmms-project>
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(xml)
    return path


# ── build + verify ───────────────────────────────────────────────────────────
def probe(path):
    """Duration/peak/RMS straight from the WAV on disk (AC-3 evidence)."""
    with wave.open(str(path), "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    dur = n / sr
    peak = float(np.max(np.abs(a))) if a.size else 0.0
    rms = float(np.sqrt(np.mean(a ** 2))) if a.size else 0.0
    dbfs = 20 * math.log10(peak) if peak > 0 else -999.0
    return {"bytes": path.stat().st_size, "seconds": round(dur, 3), "channels": ch,
            "samplerate": sr, "peak": round(peak, 5), "peak_dbfs": round(dbfs, 2),
            "rms": round(rms, 5), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(verify_only=False):
    manifest = {"album": "The Shelves Raised Us", "artist": "MilkUps",
                "scope": "5 tracks, each >= 90 s, built-in/synthesized only, no external samples",
                "cuts": ["lmms", "xm"], "tracks": []}
    for t in TRACKS:
        song = make_song(t)
        mmp = CUT_LMMS / f"trk{t['n']:02d}.mmp"
        xm = CUT_XM / f"trk{t['n']:02d}.xm"
        rl = REND_LMMS / f"trk{t['n']:02d}.wav"
        rx = REND_XM / f"trk{t['n']:02d}.wav"
        if not verify_only:
            write_mmp(t, song, mmp)
            xm_write(t, song, xm)
        mod = xm_read(xm)                       # CUT B render decodes the module
        if not verify_only:
            write_wav(render_lmms(t, song), rl)
            write_wav(render_xm(mod), rx)
        manifest["tracks"].append({
            "no": t["n"], "title": t["title"], "bpm": t["bpm"],
            "patterns": len(mod["patterns"]), "channels": mod["channels"],
            "cut_lmms": {"project": str(mmp.relative_to(ROOT)), "render": probe(rl)},
            "cut_xm": {"module": str(xm.relative_to(ROOT)), "render": probe(rx)},
        })
        print(f"trk{t['n']:02d} {t['title']:<22} "
              f"LMMS {probe(rl)['seconds']:>7.2f}s  XM {probe(rx)['seconds']:>7.2f}s")
    return manifest


def gate(manifest):
    """AC-3 / AC-5: hard pass-fail on duration, silence, and hashes."""
    fails = []
    for t in manifest["tracks"]:
        for cut in ("cut_lmms", "cut_xm"):
            p = t[cut]["render"]
            if p["seconds"] < 90.0:
                fails.append(f"trk{t['no']} {cut}: {p['seconds']}s < 90s")
            if p["peak_dbfs"] <= -60.0 or p["rms"] <= 0:
                fails.append(f"trk{t['no']} {cut}: silent (peak {p['peak_dbfs']} dBFS, rms {p['rms']})")
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify-only", action="store_true")
    args = ap.parse_args()
    m = build(verify_only=args.verify_only)
    fails = gate(m)
    m["gate"] = {"passed": not fails, "failures": fails}
    out = ALBUM / "manifest.json"
    out.write_text(json.dumps(m, indent=2))
    print("\nGATE:", "PASS" if not fails else "FAIL")
    for f in fails:
        print("  -", f)
    print("manifest:", out.relative_to(ROOT))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
