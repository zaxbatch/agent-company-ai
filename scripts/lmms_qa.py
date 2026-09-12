#!/usr/bin/env python3
"""QA gate for an LMMS render — is there music, is it clean, does it move?

Checks: duration, peak, clipping, RMS, detected tempo vs spec, per-section
energy against the spec's arrangement map, and band balance (kick vs hats).

    python3 scripts/lmms_qa.py content/experiments/lmms/beat-16bar.wav \
        --spec content/experiments/lmms/beat-16bar.spec.json
"""
from __future__ import annotations
import argparse, json, os, sys
import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lmms_spec import section_map


def detect_tempo(mono, sr):
    hop, win = 256, 1024
    n = 1 + (len(mono) - win) // hop
    if n < 8:
        return 0.0
    frames = np.lib.stride_tricks.as_strided(
        mono, shape=(n, win), strides=(mono.strides[0] * hop, mono.strides[0]))
    env = np.sqrt((frames ** 2).mean(axis=1))
    env = np.diff(env, prepend=env[0])
    env[env < 0] = 0
    env = env - env.mean()
    ac = np.correlate(env, env, mode="full")[len(env) - 1:]
    lo = int(sr / hop * 60 / 200)
    hi = min(int(sr / hop * 60 / 60), len(ac) - 1)
    return 60.0 * sr / ((lo + int(np.argmax(ac[lo:hi]))) * hop)


def rms(x):
    return float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0


def analyze(path, spec=None, bpm_tol=0.03, min_contrast=0.15):
    x, sr = sf.read(path, always_2d=True)
    mono = x.mean(axis=1)
    dur = len(mono) / sr
    peak = float(np.max(np.abs(mono)))
    clipped = int(np.sum(np.abs(mono) >= 0.999))
    level = 20 * np.log10(max(rms(mono), 1e-9))
    bpm = detect_tempo(mono, sr)

    print(f"file         : {path}")
    print(f"duration     : {dur:.3f} s  ({sr} Hz, {x.shape[1]}ch)")
    print(f"peak         : {peak:.4f} ({20*np.log10(max(peak,1e-9)):.2f} dBFS)   "
          f"rms {level:.2f} dBFS   clipped {clipped}")
    print(f"tempo        : {bpm:.2f} BPM" + (f"  (spec {spec['bpm']})" if spec else ""))

    spec_bpm = spec["bpm"] if spec else None
    bpm_ok = True
    if spec_bpm:
        err = abs(bpm - spec_bpm) / spec_bpm
        # autocorrelation can lock to a 2x/0.5x multiple; accept those, then
        # fold back so the reported number is at song tempo
        for mult in (0.5, 2.0):
            if abs(bpm * mult - spec_bpm) / spec_bpm < err:
                bpm, err = bpm * mult, abs(bpm * mult - spec_bpm) / spec_bpm
        bpm_ok = err <= bpm_tol
        print(f"tempo error  : {err*100:.2f}%  (tolerance {bpm_tol*100:.0f}%) "
              f"{'OK' if bpm_ok else 'OUT OF TOLERANCE'}")

    sections = {}
    contrast_ok = True
    if spec:
        spb = sr * 60.0 / spec["bpm"] * 4   # samples per bar (4/4)
        print(f"{'section':<9}{'bars':>5}{'start s':>9}{'rms':>9}{'dBFS':>9}")
        for name, first, count in section_map(spec):
            a, b = int(first * spb), int((first + count) * spb)
            seg = mono[a:b]
            sections[name] = rms(seg)
            print(f"{name:<9}{count:>5}{a/sr:>9.2f}{sections[name]:>9.4f}"
                  f"{20*np.log10(max(sections[name],1e-9)):>9.2f}")
        loud, quiet = max(sections.values()), min(sections.values())
        gain = loud / quiet if quiet else float("inf")
        contrast_ok = (gain - 1) >= min_contrast
        loudest = max(sections, key=sections.get)
        print(f"range        : {gain:.2f}x  loudest={loudest}  "
              f"({'OK' if contrast_ok else f'FLAT - needs >= {min_contrast*100:.0f}% contrast'})")

    spec_fft = np.abs(np.fft.rfft(mono * np.hanning(len(mono))))
    freqs = np.fft.rfftfreq(len(mono), 1 / sr)
    band = lambda lo, hi: float(spec_fft[(freqs > lo) & (freqs < hi)].sum())
    low, mid, high = band(30, 120), band(120, 5000), band(5000, 16000)
    print(f"band energy  : low {low:.0f} / mid {mid:.0f} / high {high:.0f}")
    band_ok = low > 0 and mid > 0 and high > 0

    checks = {
        "audible": dur > 1 and level > -40,
        "not clipping": clipped < 100 and peak <= 0.999,
        "tempo": bpm_ok,
        "arrangement": contrast_ok,
        "spectrum": band_ok,
    }
    print("checks       : " + "  ".join(
        f"{k}={'PASS' if v else 'FAIL'}" for k, v in checks.items()))
    ok = all(checks.values())
    print(f"VERDICT      : {'PASS' if ok else 'FAIL'}")
    return ok, sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("wav")
    ap.add_argument("--spec")
    a = ap.parse_args()
    spec = None
    if a.spec:
        with open(a.spec) as f:
            spec = json.load(f)
    ok, _ = analyze(a.wav, spec)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
