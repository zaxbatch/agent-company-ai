#!/usr/bin/env python3
"""Build a Scratch 3 scene where the Spread Da Word characters move and interact.

Each character is a sprite with three script stacks:
  1. entrance + dialogue, chained by broadcasts (Vin speaks, then cues Q, ...)
  2. a forever idle bob so they are always moving
  3. a click reaction so they interact with the viewer

    scripts/scratch_sdw_scene.py --out content/experiments/scratch/sdw-scene.sb3
"""
from __future__ import annotations
import argparse, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scratch_lib import (Blocks, Project, num, text, bcast, sub, md5_file)

STAGE_W, STAGE_H = 480, 360

# name, source art, dialogue, click reaction, pixel height on stage
CAST = [
    ("Vin Negar",   "vin.png",     "Two shelves. One story.",        "The realest.",     130),
    ("Q",           "q.png",       "TURN IT UP!",                    "Hype man never stops.", 120),
    ("Manny",       "manny.png",   "Family business. Always was.",   "Da Man has spoken.", 120),
    ("Miracle",     "miracle.png", "Came up cold. Stayed seasoned.", "That's the recipe.", 120),
    ("Tom",         "tom.png",     "Ain't no shelf big enough.",    "32 ounces of truth.", 125),
    ("Tom Jr.",     "jr.png",      "Fresh out the fryer!",           "Optimist for life.", 115),
]


def crop_alpha(png):
    im = Image.open(png).convert("RGBA")
    bbox = im.getbbox()
    return im.crop(bbox) if bbox else im


def fit(im, target_h):
    s = target_h / im.height
    return im.resize((max(1, int(im.width * s)), target_h), Image.LANCZOS)


def backdrop(path, title, subtitle):
    img = Image.new("RGB", (STAGE_W, STAGE_H), (10, 12, 22))
    d = ImageDraw.Draw(img)
    for i in range(STAGE_H):
        t = i / STAGE_H
        d.line([(0, i), (STAGE_W, i)],
               fill=(int(10 + 26 * t), int(12 + 20 * t), int(22 + 46 * t)))
    for x in range(0, STAGE_W, 24):
        d.line([(x, 0), (x, STAGE_H)], fill=(20, 26, 44))
    for y in range(0, STAGE_H, 24):
        d.line([(0, y), (STAGE_W, y)], fill=(20, 26, 44))
    d.rectangle([0, STAGE_H - 34, STAGE_W, STAGE_H], fill=(6, 8, 14))
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    tw = d.textlength(title, font=f1)
    d.text(((STAGE_W - tw) / 2, 22), title, font=f1, fill=(243, 156, 18))
    tw2 = d.textlength(subtitle, font=f2)
    d.text(((STAGE_W - tw2) / 2, 56), subtitle, font=f2, fill=(150, 190, 235))
    d.text((10, STAGE_H - 26), "click a character", font=f2, fill=(140, 150, 170))
    img.save(path)
    return path


def build(refdir, out, music=None, flat=False):
    proj = Project()
    tmp = "/tmp/scratch_build"
    os.makedirs(tmp, exist_ok=True)

    bg = backdrop(os.path.join(tmp, "backdrop.png"), "SPREAD DA WORD",
                  "a Z-Dot original series")
    proj.stage(bg)

    # sound on the stage
    sound_asset = None
    if music and os.path.exists(music):
        sound_asset = proj.add_sound(proj.targets[0], music, name="beat")
        sound_asset = (sound_asset["name"], sound_asset["assetId"])
    proj.targets[0]["blocks"] = Blocks().b

    mids = {}
    for key in ["start"] + [f"cue{i}" for i in range(1, len(CAST) + 1)] + ["family"]:
        mids[key] = proj.broadcast_id(key)

    # stage: flag -> play music -> broadcast start
    sb = Blocks()
    stage_specs = [("event_whenflagclicked", {}, {})]
    if sound_asset:
        stage_specs.append(("sound_play", {"SOUND_MENU": [1, [11, sound_asset[0], sound_asset[1]]]}, {}))
    stage_specs.append(("event_broadcast", {"BROADCAST_INPUT": bcast("start", mids["start"])}, {}))
    sb.chain(stage_specs)
    proj.targets[0]["blocks"] = sb.b

    # lay the cast out along the stage floor
    arts = []
    for name, fn, line, react, h in CAST:
        p = os.path.join(refdir, fn)
        if flat:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from flat_style import flatify
            fp = os.path.join(tmp, fn.replace(".png", "-flat.png"))
            flatify(p, out=fp, lift_levels=True, shadow=True)
            im = fit(crop_alpha(fp), h)
        else:
            im = fit(crop_alpha(p), h)
        out_png = os.path.join(tmp, fn.replace(".png", "-sprite.png"))
        im.save(out_png)
        arts.append([name, out_png, im, line, react])

    # two rows of three, so each character can be roughly twice as large.
    # front row sits lower and in front; back row higher and behind.
    gap = 10
    per_row = 3
    rows = [arts[:per_row], arts[per_row:per_row * 2]]
    row_y = [40, -85]                    # scratch y for back / front row
    slot_w = (STAGE_W - 20 - gap * (per_row - 1)) / per_row

    layout = []                          # (art, x, y, size%)
    for r, row in enumerate(rows):
        widths = []
        for a in row:
            size_pct = min(100.0, slot_w / a[2].width * 100.0)
            widths.append(a[2].width * size_pct / 100.0)
        total = sum(widths) + gap * (len(row) - 1)
        cursor = -total / 2.0
        for a, w in zip(row, widths):
            layout.append((a, cursor + w / 2.0, row_y[r], min(100.0, slot_w / a[2].width * 100.0)))
            cursor += w + gap

    layer = 1
    for i, (a, cx, y, size_pct) in enumerate(layout):
        name, png, im, line, react = a

        bl = Blocks()
        cue_in = mids["start"] if i == 0 else mids[f"cue{i}"]
        cue_out = mids["family"] if i == len(arts) - 1 else mids[f"cue{i+1}"]
        enter_x, enter_y = cx, y
        shrink = size_pct

        # stack on the receive
        chain = [
            ("motion_gotoxy", {"X": num(cx), "Y": num(y - 150)}, {}),      # start below
            ("motion_glidesecstoxy", {"SECS": num(0.6), "X": num(enter_x), "Y": num(enter_y)}, {}),
            ("looks_sayforsecs", {"MESSAGE": text(line), "SECS": num(2.2)}, {}),
            ("event_broadcast", {"BROADCAST_INPUT": bcast(
                "family" if i == len(arts) - 1 else f"cue{i+1}",
                cue_out)}, {}),
        ]
        first = bl.chain(chain, parent=None)
        # prepend the hat: the old first block is no longer a script head
        bl.b[first]["topLevel"] = False
        bl.b[first]["parent"] = None
        hat = bl.add("event_whenbroadcastreceived",
                     {}, {"BROADCAST_OPTION": [("start" if i == 0 else f"cue{i}"), cue_in]},
                     top=True)
        bl.b[hat]["next"] = first
        bl.b[first]["parent"] = hat

        # idle bob: forever, so they keep moving
        up_hat = bl.add("event_whenflagclicked", {}, {}, top=True)
        bob = bl.add("control_forever", {"SUBSTACK": [2, None]}, {}, top=False, parent=up_hat)
        bl.b[up_hat]["next"] = bob
        c1 = bl.add("motion_changeyby", {"DY": num(3)}, {}, parent=bob)
        c2 = bl.add("control_wait", {"DURATION": num(0.35)}, {}, parent=c1)
        c3 = bl.add("motion_changeyby", {"DY": num(-3)}, {}, parent=c2)
        c4 = bl.add("control_wait", {"DURATION": num(0.35)}, {}, parent=c3)
        bl.b[c1]["next"] = c2; bl.b[c2]["next"] = c3; bl.b[c3]["next"] = c4
        bl.b[c4]["next"] = c1
        bl.b[bob]["inputs"]["SUBSTACK"] = [2, c1]

        # click reaction
        click_hat = bl.add("event_whenthisspriteclicked", {}, {}, top=True)
        s1 = bl.add("looks_setsize", {"SIZE": num(round(shrink * 1.15, 1))}, {}, parent=click_hat)
        s2 = bl.add("looks_sayforsecs", {"MESSAGE": text(react), "SECS": num(1.6)}, {}, parent=s1)
        s3 = bl.add("looks_setsize", {"SIZE": num(round(shrink, 1))}, {}, parent=s2)
        bl.b[click_hat]["next"] = s1; bl.b[s1]["next"] = s2; bl.b[s2]["next"] = s3

        proj.sprite(name, png, x=enter_x, y=enter_y, size=shrink, layer=layer, blocks=bl.b)
        layer += 1

    size = proj.save(out)
    return size, proj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refdir", default="/tmp/sdwref")
    ap.add_argument("--out", default="content/experiments/scratch/sdw-scene.sb3")
    ap.add_argument("--music", default="content/experiments/lmms/beat-16bar.wav")
    ap.add_argument("--flat", action="store_true", help="flat paper-cutout style + drop shadow")
    a = ap.parse_args()
    size, proj = build(a.refdir, a.out, a.music, flat=a.flat)
    print(f"wrote {a.out} ({size} B) — {len(proj.targets)} targets")
    for t in proj.targets:
        print(f"   {'STAGE' if t['isStage'] else 'sprite':<7} {t['name']:<12} "
              f"blocks={len(t['blocks'])} costumes={len(t['costumes'])} sounds={len(t['sounds'])}")


if __name__ == "__main__":
    main()
