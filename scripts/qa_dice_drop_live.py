#!/usr/bin/env python3
"""qa_dice_drop_live.py — load the PUBLISHED game from the live SnowSnakes URL
in a phone viewport and prove it plays there (not just locally).

Usage: python3 scripts/qa_dice_drop_live.py [game_id]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

GID = sys.argv[1] if len(sys.argv) > 1 else "124"
URL = f"https://snowsnakes.zerric.xyz/games/{GID}"
OUT = Path("evidence/dice-drop-qa")
MOBILE = {"width": 390, "height": 844}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        ctx = b.new_context(viewport=MOBILE, device_scale_factor=2, is_mobile=True,
                            has_touch=True)
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        page.goto(URL, wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(OUT / "live-01-loaded.png"))

        # find the game iframe / canvas — the game is served inside the app shell
        info = page.evaluate("""() => {
          const frames = [...document.querySelectorAll('iframe')].map(f => f.src);
          const canv = document.querySelectorAll('canvas').length;
          return {title: document.title, frames, canvases: canv,
                  bodyLen: document.body.innerText.length};
        }""")
        print("shell     :", info["title"])
        print("iframes   :", info["frames"] or "none")
        print("canvases  :", info["canvases"])

        # if the game is in an iframe, drive it there; otherwise drive the page
        target = page
        if info["frames"]:
            fr = page.frame(url=lambda u: "games" in u or "cdn" in u or "cloudinary" in u)
            if fr is None and page.frames:
                fr = page.frames[-1]
            if fr:
                target = fr

        try:
            target.wait_for_selector("#ovBtn", timeout=20000)
            target.click("#ovBtn")
            target.wait_for_timeout(400)
            for _ in range(6):
                target.click("#bL"); target.click("#bR"); target.click("#bHD")
                target.wait_for_timeout(90)
            target.wait_for_timeout(300)
            state = target.evaluate("""() => ({
              score: document.getElementById('score').textContent,
              rows: document.getElementById('rows').textContent,
              best: document.getElementById('best').textContent})""")
            blank = target.evaluate("""() => {
              const c = document.getElementById('board');
              const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
              const s = new Set();
              for (let i=0;i<d.length;i+=4*97) s.add(d[i]+','+d[i+1]+','+d[i+2]);
              return s.size;
            }""")
            print("live state:", state)
            print("canvas    :", blank, "distinct sampled colours")
            if int(str(state["score"]).replace(",", "") or 0) <= 0:
                problems.append("live: score stayed 0 — game not interactive on the live URL")
            if blank < 5:
                problems.append(f"live: canvas blank ({blank} colours)")
        except Exception as e:  # noqa: BLE001
            problems.append(f"live: could not drive the game ({str(e)[:150]})")

        page.screenshot(path=str(OUT / "live-02-played.png"))
        ctx.close(); b.close()

    rep = {"url": URL, "shell": info, "js_errors": errors, "problems": problems}
    (OUT / "live-report.json").write_text(json.dumps(rep, indent=2))
    if errors:
        print("JS errors :", errors[:3])
    if problems:
        print("\nPROBLEMS:")
        for x in problems:
            print(" -", x)
    else:
        print("\nLIVE GAME PLAYS OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
