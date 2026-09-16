#!/usr/bin/env python3
"""verify_xm.py - structural validator for FastTracker II .XM modules.

Independent of the writer: re-parses the binary layout from the spec and proves
the file is fully accounted for (no trailing junk, no overrun), then prints a
machine-readable JSON block. Exit 0 = structurally valid.

    python3 scripts/verify_xm.py path/to/song.xm

Layout proven by this tool:
  header(60 + header_size 276 => 336) | patterns | instruments
  pattern  = 4-byte len + 1 packing + 2 rows + 2 datalen + data
  instr    = 4 len + 22 name + 1 type + 2 nsamp + 4 samplehdr_size
             + 96 sample map + 48 vol env + 48 pan env + 8 env points + 6 vibrato + 2 fadeout + 22 reserved (= 263)
  sample   = 4 len + 4 loopstart + 4 looplen + 1 vol + 1 finetune + 1 type
             + 1 pan + 1 relnote + 1 reserved + 22 name (= 40)
"""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path

MAGIC = b"Extended Module: "


def verify(path: Path) -> dict:
    b = path.read_bytes()
    r: dict = {"file": str(path), "bytes": len(b),
               "sha256": hashlib.sha256(b).hexdigest(), "errors": []}
    if not b.startswith(MAGIC):
        r["errors"].append("bad magic")
        return r
    if b[37] != 0x1A:
        r["errors"].append("missing 0x1A signature byte")
    r["magic"] = MAGIC.decode()
    r["module_name"] = b[17:37].rstrip(b"\x00").decode(errors="replace")
    r["tracker"] = b[38:58].rstrip(b"\x00").decode(errors="replace")
    ver, hsize = struct.unpack("<HI", b[58:64])
    r["version"] = "0x%04x" % ver
    r["header_size"] = hsize
    if hsize != 276:
        r["errors"].append("header_size %d != 276" % hsize)
    (olen, restart, nch, npat, nins, flags, spd, bpm) = struct.unpack("<HHHHHHHH", b[64:80])
    r.update(order_length=olen, restart=restart, channels=nch, patterns=npat,
             instruments=nins, linear_freq=bool(flags & 1), speed=spd, bpm=bpm)
    r["order"] = list(b[80:80 + 256])[:olen]

    off = 60 + hsize
    pat_rows, pat_bytes = [], 0
    for i in range(npat):
        if off + 9 > len(b):
            r["errors"].append("pattern %d header past EOF" % i)
            return r
        plen, ptype, rows, dlen = struct.unpack("<IBHH", b[off:off + 9])
        if plen != 9:
            r["errors"].append("pattern %d header len %d != 9" % (i, plen))
        if ptype != 0:
            r["errors"].append("pattern %d packing type %d != 0 (unpacked expected)" % (i, ptype))
        if dlen != rows * nch * 5:
            r["errors"].append("pattern %d datalen %d != rows*ch*5 %d" % (i, dlen, rows * nch * 5))
        off += 9 + dlen
        pat_rows.append(rows)
        pat_bytes += dlen
    r["pattern_rows"] = pat_rows
    r["pattern_data_bytes"] = pat_bytes
    r["rows_played"] = sum(pat_rows[i] for i in r["order"] if i < len(pat_rows))

    insts = []
    for i in range(nins):
        isize, = struct.unpack("<I", b[off:off + 4])
        iname = b[off + 4:off + 26].rstrip(b"\x00").decode(errors="replace")
        itype, nsamp = struct.unpack("<BH", b[off + 26:off + 29])
        shsize, = struct.unpack("<I", b[off + 29:off + 33])
        if isize != 263:
            r["errors"].append("instrument %d header size %d != 263" % (i + 1, isize))
        smap = b[off + 33:off + 129]
        off += 33 + 96 + 48 + 48 + 16 + 22
        total = 0
        for s in range(nsamp):
            slen, sloop, slplen = struct.unpack("<III", b[off:off + 12])
            total += slen
            off += shsize
        off += total
        if max(smap[:96]) >= max(1, nsamp):
            r["errors"].append(
                "instrument %d sample map references sample >%d "
                "(libopenmpt clamps; spec-tight modules use an all-zero map)" % (i + 1, nsamp - 1))
        insts.append({"n": i + 1, "name": iname, "samples": nsamp, "pcm_bytes": total,
                      "sample_map_max": max(smap[:96])})
    r["instrument_table"] = insts
    r["parsed_bytes"] = off
    r["fully_accounted"] = (off == len(b))
    if off != len(b):
        r["errors"].append("parsed %d bytes, file is %d" % (off, len(b)))
    r["valid"] = not r["errors"]
    return r


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    p = Path(sys.argv[1])
    r = verify(p)
    print(json.dumps(r, indent=2))
    print("\nXM-STRUCT: %s  %s  %d B  ch=%s pat=%s ins=%s bpm=%s order=%s rows=%s" % (
        "PASS" if r["valid"] else "FAIL", p.name, r["bytes"], r.get("channels"),
        r.get("patterns"), r.get("instruments"), r.get("bpm"), r.get("order_length"),
        r.get("rows_played")))
    return 0 if r["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
