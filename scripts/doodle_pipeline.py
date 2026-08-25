#!/usr/bin/env python3
"""Doodle pipeline — generates 10 doodles/day into the approval folder + progress page.

Usage:
  python3 scripts/doodle_pipeline.py            # generate today's 10 doodles
  python3 scripts/doodle_pipeline.py --dry-run  # preview names only

Flow: build 10 unique SVG doodles (Spread Da Word universe + Snitch rats) →
resources/snowsnakes/doodles-comics-under-review/ → regenerate progress proof.json
so tasks.zdotllc.com/progress shows the gallery. NOT posted to SnowSnakes (approval first).
"""
import argparse, os, random, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "resources" / "snowsnakes" / "doodles-comics-under-review"
OUT.mkdir(parents=True, exist_ok=True)

# ── Universe pieces ──
CHARACTERS = [
    {"name":"Vin Negar","emoji":"🍶","color":"#3d5a3d","label":"ACV","quote":"You ain't ready for me, bro."},
    {"name":"Que","emoji":"🥫","color":"#6a2f1f","label":"BBQ","quote":"Pass the sauce, pass the vibe."},
    {"name":"Red","emoji":"🍅","color":"#c62828","label":"KETCH","quote":"I go with everything."},
    {"name":"Yellow","emoji":"🌼","color":"#f9a825","label":"MUST","quote":"I was here first."},
    {"name":"Aji","emoji":"🌶️","color":"#d32f2f","label":"AJI","quote":"With MORE fire."},
    {"name":"Mayo","emoji":"🤍","color":"#f4f4f4","label":"MAYO","quote":"Let's keep it smooth."},
    {"name":"Whip","emoji":"🍯","color":"#f8e6c8","label":"WHIP","quote":"I'm not Mayo. I'm me."},
    {"name":"Zest","emoji":"🍋","color":"#fff59d","label":"ZEST","quote":"A little goes a long way."},
    {"name":"Crisp","emoji":"🥗","color":"#cfefcf","label":"CRISP","quote":"Hey guys! What's up?"},
    {"name":"Snow Snake","emoji":"🐍","color":"#e8f4ff","label":"SNOW","quote":"Always watching. Never explained."},
]
SCENES = [
    ("3AM snack run", "#1a1a2e", "moon"),
    ("fridge standoff", "#dfe8ee", "fridge"),
    ("cookout", "#1a3a1a", "grill"),
    ("dumpster dive", "#2d2d44", "dumpster"),
    ("sewer crossing", "#0e2a1a", "sewer"),
    ("parking lot", "#24243a", "lot"),
    ("kitchen counter", "#8a6a4a", "counter"),
    ("back alley", "#2a1a2a", "alley"),
    ("snow field", "#0b1a2a", "snow"),
    ("the lair", "#3a1a0a", "lair"),
]
CAPTIONS = [
    "The shelves raised us.",
    "Stay silent. Watch. Win.",
    "Even the fridge fears the hood.",
    "Trust is the real currency.",
    "Some snitch. Some survive.",
    "The cab-nets vs the suburbs.",
    "Never explained. Always watching.",
    "Pass the vibe.",
    "The cheese is a lie.",
    "One shelf. Two worlds.",
]

def doodle_svg(seed):
    rnd = random.Random(seed)
    ch = rnd.choice(CHARACTERS)
    scene = rnd.choice(SCENES)
    caption = rnd.choice(CAPTIONS)
    bg, _, motif = scene
    # compose a simple, valid SVG
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
  <rect width="800" height="600" fill="{bg}"/>
  <!-- motif hint -->
  <text x="60" y="90" font-size="28" fill="#ffffff22" font-family="monospace">{motif}</text>
  <!-- character -->
  <g transform="translate(320,180)">
    <rect x="10" y="60" width="100" height="140" rx="14" fill="{ch['color']}"/>
    <rect x="32" y="10" width="56" height="55" rx="8" fill="{ch['color']}"/>
    <rect x="44" y="-16" width="32" height="30" rx="5" fill="{ch['color']}"/>
    <text x="60" y="130" font-size="18" fill="#fff" text-anchor="middle" font-family="monospace">{ch['label']}</text>
    <circle cx="44" cy="34" r="7" fill="#fff"/>
    <circle cx="78" cy="34" r="7" fill="#fff"/>
    <circle cx="46" cy="35" r="3.5" fill="#111"/>
    <circle cx="76" cy="35" r="3.5" fill="#111"/>
    <path d="M48 54 Q62 64 76 54" stroke="#111" stroke-width="3" fill="none"/>
    <text x="60" y="24" font-size="34" text-anchor="middle">{ch['emoji']}</text>
  </g>
  <!-- speech -->
  <rect x="180" y="110" width="260" height="46" rx="18" fill="#fff"/>
  <text x="310" y="140" font-size="17" fill="#111" text-anchor="middle" font-family="monospace">{ch['quote']}</text>
  <!-- caption -->
  <text x="400" y="560" font-size="26" fill="#7fd1ff" text-anchor="middle" font-family="monospace" font-weight="bold">{caption}</text>
  <text x="400" y="585" font-size="13" fill="#ffffff44" text-anchor="middle" font-family="monospace">spread da word · doodle {seed}</text>
</svg>'''
    return svg, ch["name"], scene[0], caption

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--count", type=int, default=10)
    args = ap.parse_args()

    today = date.today().isoformat()
    created = []
    for i in range(args.count):
        seed = int(f"{today.replace('-','')}{i:02d}")
        svg, ch, scene, cap = doodle_svg(seed)
        fname = f"doodle-{today}-{i+1:02d}-{ch.lower().replace(' ','-')}.svg"
        if args.dry_run:
            print(f"[DRY] {fname} — {ch} · {scene} · \"{cap}\"")
            continue
        (OUT / fname).write_text(svg)
        created.append(fname)

    if args.dry_run:
        print(f"\nWould create {args.count} doodles in {OUT}")
        return

    # append to README manifest
    readme = OUT / "README.md"
    with readme.open("a") as f:
        f.write(f"\n## {today} — daily batch\n")
        for fname in created:
            f.write(f"- {fname}\n")

    # regenerate progress proof.json with doodle gallery
    try:
        subprocess = __import__("subprocess")
        subprocess.run([sys.executable, str(ROOT/"scripts"/"build_proof_site.py")], check=False)
    except Exception as e:
        print("note: proof regen failed:", e)

    print(f"✅ {len(created)} doodles → {OUT}")
    for f in created: print("  ", f)

if __name__ == "__main__":
    main()
