#!/usr/bin/env python3
"""Pull real instrument presets out of LMMS .xpf files for embedding in projects.

LMMS saves sessions with instrument state inline, not a preset path, so to use a
bundled preset in a generated project we copy its <instrument> block across.

    from lmms_presets import instrument_from_preset
    xml = instrument_from_preset("/usr/share/lmms/presets/Organic/pad_rich.xpf")
"""
from __future__ import annotations
import os, re

ROOT = "/usr/share/lmms/presets"


# children of <instrumenttrack> that are NOT instruments
NON_INSTRUMENT = {"eldata", "chordcreator", "arpeggiator", "midiport", "fxchain"}


def instrument_from_preset(path):
    """Return an <instrument> block. Handles both preset shapes:
    newer ones wrap the engine in <instrument name="x">, older ones (e.g.
    Organic) put the bare engine element straight inside <instrumenttrack>."""
    with open(path) as f:
        s = f.read()

    m = re.search(r'(<instrument\s+name="[^"]+">.*?</instrument>)', s, re.S)
    if m:
        return m.group(1)

    # bare-engine preset: look only INSIDE <instrumenttrack> for the engine
    it = re.search(r'<instrumenttrack\b.*?>(.*?)</instrumenttrack>', s, re.S)
    if not it:
        raise SystemExit(f"no <instrumenttrack> in {path}")
    for mm in re.finditer(r'<(\w+)(\s[^>]*?)?/?>', it.group(1)):
        tag = mm.group(1)
        if tag in NON_INSTRUMENT or tag in ("head", "instrumenttrack", "instrumenttracksettings"):
            continue
        return (f'<instrument name="{tag}">\n'
                f'                  {mm.group(0)}\n'
                f'                </instrument>')
    raise SystemExit(f"no instrument found in {path}")


def find(bank, name_fragment):
    """Locate a preset by bank + filename fragment."""
    d = os.path.join(ROOT, bank)
    if not os.path.isdir(d):
        raise SystemExit(f"no such bank: {bank} (have {sorted(os.listdir(ROOT))})")
    hits = [f for f in sorted(os.listdir(d))
            if name_fragment.lower() in f.lower() and f.endswith(".xpf")]
    if not hits:
        raise SystemExit(f"no preset matching {name_fragment!r} in {bank}")
    return os.path.join(d, hits[0])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        p = find(sys.argv[1], sys.argv[2])
        print(p)
        print(instrument_from_preset(p))
    else:
        for b in sorted(os.listdir(ROOT)):
            n = len([f for f in os.listdir(os.path.join(ROOT, b)) if f.endswith(".xpf")])
            print(f"{b:<18} {n:>3} presets")
