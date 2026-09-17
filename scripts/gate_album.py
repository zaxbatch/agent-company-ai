#!/usr/bin/env python3
"""gate_album.py — run the SnowSnakes standard over every track in an album,
then check the album for homogenisation."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALBUM = ROOT / "content" / "milkups" / "album-full"
man = json.loads((ALBUM / "manifest.json").read_text())

results = []
for t in man["tracks"]:
    wav = ROOT / t["wav"]; cover = ROOT / t["cover"]
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "verify_song.py"), str(wav),
                        "--genre", t["genre"], "--bpm", str(t["bpm"]), "--cover", str(cover)],
                       capture_output=True, text=True)
    ok = r.returncode == 0
    results.append((t["n"], t["title"], t["genre"], ok, r.stdout))
    print(f"{'PASS' if ok else 'FAIL'}  {t['n']}. {t['title']:<22} [{t['genre']}]")
    for line in r.stdout.splitlines():
        if line.strip().startswith("FAIL"):
            print("       " + line.strip())

print(f"\n{sum(1 for x in results if x[3])}/{len(results)} tracks pass the standard")

# ── album-level homogenisation check ──
sys.path.insert(0, str(ROOT / "scripts"))
import songkit as sk
fp = {}
print("\nVARIETY (groove + tempo bucket + brightness bucket)")
for t in man["tracks"]:
    a, sr = sk.load(ROOT / t["wav"])
    bpm, _ = sk.estimate_bpm(a, sr)
    cent = sk.spectral_centroid(a, sr)
    key = (t["genre"], round(bpm / 10) * 10, int(cent // 250))
    fp[t["n"]] = key
    print(f"  {t['n']}. {t['title']:<22} measured {bpm:6.1f}bpm  {cent:6.0f}Hz  key={key}")
clashes = []
for a_ in fp:
    for b_ in fp:
        if a_ < b_ and fp[a_] == fp[b_]:
            clashes.append((a_, b_))
if clashes:
    print(f"\n  FAIL  homogenised pairs: {clashes}")
else:
    print("\n  PASS  all 6 tracks have distinct groove/tempo/brightness profiles")
ok = all(x[3] for x in results) and not clashes
print(f"\nALBUM GATE: {'PASS' if ok else 'FAIL'}")
Path(ALBUM / "gate-report.txt").write_text(
    "\n".join(r[4] for r in results) +
    f"\n\n{sum(1 for x in results if x[3])}/{len(results)} pass\nclashes={clashes}\nALBUM: {'PASS' if ok else 'FAIL'}\n")
raise SystemExit(0 if ok else 1)
