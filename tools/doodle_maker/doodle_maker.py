#!/usr/bin/env python3
"""doodle_maker.py - template-driven doodle runner with a job log.

ONE-LINE INVOCATION
  venv/bin/python tools/doodle_maker/doodle_maker.py \
      --template content/milkups/art/doodles/_templates/doodle-prompt-v1.md \
      --seed 128 --out content/milkups/art/doodles/programmatic --tag programmatic

BEHAVIOUR
  * reads a markdown template (YAML front matter) -> deterministic render
  * writes  <out>/<template_id>-seed<seed>.png
  * appends ONE JSONL job-log line to tools/doodle_maker/joblog.jsonl containing
    UTC timestamp, seed, template id, template sha256, output path, output sha256,
    byte count, renderer, tag.
  * exits NON-ZERO on any failure.

PROVENANCE (read this before tagging anything "AI")
  renderer=programmatic means: deterministic in-house Python/PIL composition.
  It is NOT a vendor "doodle maker" product and it is NOT hand-drawn.
  Do not tag its output "ai" or "traditional". See
  docs/DOODLE-EVIDENCE-REPLY--20260912.md and the style guide for the 3-class rule.

Owner: NinjaNerd (CTO) - Z-Dot LLC.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, random, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
JOBLOG = Path(__file__).resolve().parent / "joblog.jsonl"
RENDERER_VERSION = "doodle_maker.py/1.0.0"

REQUIRED_KEYS = ("template_id", "canvas", "paper", "ink", "body", "accent", "snow", "caption")


def hexcol(v: str):
    v = v.strip().strip('"').strip("'").lstrip("#")
    if len(v) != 6:
        raise ValueError(f"bad colour: {v!r}")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def parse_template(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("template missing front matter (---)")
    _, fm, body = text.split("---", 2)
    data, body = {}, body.strip()
    for line in fm.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"bad front-matter line: {line!r}")
        k, v = line.split(":", 1)
        data[k.strip()] = v.strip()
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"template missing keys: {missing}")
    data["_prompt_body"] = body
    data["_path"] = str(path)
    data["_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    w, h = data["canvas"].lower().split("x")
    data["_size"] = (int(w), int(h))
    return data


def _font(sz: int):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(p, sz)
        except OSError:
            continue
    return ImageFont.load_default()


def render(t: dict, seed: int, out_path: Path) -> Path:
    from PIL import Image, ImageDraw
    W, H = t["_size"]
    PAPER, INK, BODY, ACCENT, SNOW = (hexcol(t[k]) for k in
                                      ("paper", "ink", "body", "accent", "snow"))
    rnd = random.Random(seed)

    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    def jline(pts, jitter=1.6, width=5, fill=INK):
        wob = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter))
               for x, y in pts]
        d.line(wob, fill=fill, width=width, joint="curve")

    def snowflake(cx, cy, r, col=SNOW, w=2):
        for k in range(3):
            a = math.radians(k * 60)
            x, y = math.cos(a) * r, math.sin(a) * r
            d.line([(cx - x, cy - y), (cx + x, cy + y)], fill=col, width=w)
        for k in range(3):
            a = math.radians(k * 60 + 30)
            for s in (0.55,):
                x, y = math.cos(a) * r * s, math.sin(a) * r * s
                d.line([(cx, cy), (cx + x, cy + y)], fill=col, width=w)
                d.line([(cx, cy), (cx - x, cy - y)], fill=col, width=w)

    def note(x, y, s=1.0, col=INK):
        d.ellipse([x - 11 * s, y - 8 * s, x + 11 * s, y + 8 * s], fill=col)
        d.line([(x + 9 * s, y), (x + 9 * s, y - 54 * s)], fill=col, width=max(1, int(4 * s)))
        d.line([(x + 9 * s, y - 54 * s), (x + 30 * s, y - 46 * s)], fill=col, width=max(1, int(4 * s)))

    # paper dot grid
    for y in range(40, H - 40, 34):
        for x in range(40, W - 40, 34):
            d.point((x, y), fill=(226, 228, 224))

    cx, cy = W * 0.5, H * 0.733
    t0, t1 = math.radians(180), math.radians(270)
    r0, r1 = 52.0, 168.0
    N = 260
    pts = []
    for i in range(N + 1):
        tt = i / N
        th = t0 + (t1 - t0) * tt
        r = r0 + (r1 - r0) * tt
        pts.append((cx + math.cos(th) * r * 1.12, cy + math.sin(th) * r * 0.92))

    jline([(x + 5, y + 6) for x, y in pts], jitter=0.06, width=44, fill=(238, 238, 234))
    jline(pts, jitter=0.06, width=42, fill=BODY)
    jline(pts, jitter=0.06, width=3, fill=INK)
    for i in range(14, N - 6, 22):
        snowflake(pts[i][0], pts[i][1], 11, col=(150, 200, 235), w=2)

    hx, hy = pts[-1][0] + 2, pts[-1][1] - 34
    d.ellipse([hx - 58, hy - 46, hx + 58, hy + 46], fill=BODY, outline=INK, width=4)
    for sx in (-24, 24):
        d.ellipse([hx + sx - 13, hy - 8, hx + sx + 13, hy + 18], fill=(255, 255, 255),
                  outline=INK, width=3)
        d.ellipse([hx + sx - 5, hy + 2, hx + sx + 6, hy + 13], fill=INK)
        d.ellipse([hx + sx - 2, hy + 1, hx + sx + 2, hy + 5], fill=(255, 255, 255))
    d.arc([hx - 26, hy + 8, hx + 26, hy + 40], start=15, end=165, fill=INK, width=3)
    d.line([(hx, hy + 44), (hx, hy + 74)], fill=ACCENT, width=4)
    d.line([(hx, hy + 74), (hx - 14, hy + 92)], fill=ACCENT, width=4)
    d.line([(hx, hy + 74), (hx + 14, hy + 92)], fill=ACCENT, width=4)

    d.arc([hx - 66, hy - 84, hx + 66, hy + 30], start=185, end=355, fill=INK, width=9)
    for sx in (-64, 64):
        d.rounded_rectangle([hx + sx - 17, hy - 30, hx + sx + 17, hy + 34], radius=11,
                            fill=(44, 48, 58), outline=INK, width=3)
        d.rounded_rectangle([hx + sx - 10, hy - 16, hx + sx + 10, hy + 22], radius=7, fill=ACCENT)
    jline([(hx - 64, hy + 34), (hx - 96, hy + 96), (hx - 40, hy + 150)], width=4, fill=INK)

    note(W * 0.783, H * 0.413, 1.15, ACCENT)
    note(W * 0.857, H * 0.478, 1.0, INK)
    note(W * 0.16, H * 0.449, 0.95, INK)

    d.ellipse([86, 726, 154, 776], fill=(196, 42, 42))
    d.ellipse([96, 716, 128, 740], fill=(196, 42, 42))
    d.ellipse([126, 712, 152, 734], fill=(196, 42, 42))
    d.text((86, 784), t.get("stamp", "SPICY"), font=_font(17), fill=(196, 42, 42))

    d.text((44, 52), t.get("brand", "SNOW BEATS"), font=_font(52), fill=INK)
    d.text((46, 116), t.get("tag", ""), font=_font(26), fill=SNOW)
    d.line([(44, 156), (300, 156)], fill=SNOW, width=4)

    f = _font(34)
    cap = t["caption"]
    tw = d.textlength(cap, font=f)
    d.text(((W - tw) / 2, 806), cap, font=f, fill=INK)
    d.text((W - 150, 858), t.get("footer", "Z-DOT"), font=_font(19), fill=(150, 158, 170))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="Template-driven doodle runner (writes a job log).")
    ap.add_argument("--template", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", default="programmatic",
                    choices=["programmatic", "ai", "traditional"])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    tpl_path = Path(a.template)
    if not tpl_path.is_absolute():
        tpl_path = ROOT / tpl_path
    t = parse_template(tpl_path)

    out_dir = Path(a.out)
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_file = out_dir / f"{t['template_id']}-seed{a.seed}.png"

    if a.dry_run:
        print(f"DRY-RUN ok template={t['template_id']} seed={a.seed} out={out_file}")
        return 0

    render(t, a.seed, out_file)
    digest = hashlib.sha256(out_file.read_bytes()).hexdigest()
    rec = {
        "ts_utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "renderer": RENDERER_VERSION,
        "renderer_kind": "programmatic",
        "tag": a.tag,
        "template_id": t["template_id"],
        "template_path": str(tpl_path.relative_to(ROOT)) if str(tpl_path).startswith(str(ROOT)) else str(tpl_path),
        "template_sha256": t["_sha256"],
        "seed": a.seed,
        "canvas": t["canvas"],
        "output_path": str(out_file.relative_to(ROOT)) if str(out_file).startswith(str(ROOT)) else str(out_file),
        "output_sha256": digest,
        "output_bytes": out_file.stat().st_size,
    }
    JOBLOG.parent.mkdir(parents=True, exist_ok=True)
    with open(JOBLOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"OK {out_file} {rec['output_bytes']}B sha256={digest[:16]} log={JOBLOG}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # non-zero on any failure, always
        print(f"FAIL {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
