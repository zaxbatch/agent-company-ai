#!/usr/bin/env python3
"""qa_dice_drop_live.py — prove the PUBLISHED game plays on the real SnowSnakes host.

Two modes, because the host does something unusual:

  MODE A ("launch"): GET /api/games/<id>/launch is the exact HTML the platform
     serves. NOTE: the host wraps our whole document inside
     `<div id="game-container">` — i.e. a second <!DOCTYPE>/<html>/<head>/<body>
     nested inside the outer body. Browsers drop the nested structural tags but
     keep our <style> and <script>, so this must be proven, not assumed.

  MODE B ("srcdoc"): SnowSnakes renders posted code inside a sandboxed iframe
     (sandbox="allow-scripts"). Reproduce that exact sandbox and play inside it.

Writes screenshots + JSON evidence.

Usage: python3 scripts/qa_dice_drop_live.py [game_id]
"""
from __future__ import annotations

import html as _html
import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

GID = sys.argv[1] if len(sys.argv) > 1 else "124"
LAUNCH = f"https://snowsnakes.zerric.xyz/api/games/{GID}/launch"
OUT = Path("evidence/dice-drop-qa")
MOBILE = {"width": 390, "height": 844}


def play_in_frame(frame) -> dict:
    """Drive the real game: tap start, move/rotate/drop, read state + canvas."""
    frame.wait_for_selector("#ovBtn", timeout=25000)
    frame.click("#ovBtn")
    frame.wait_for_timeout(400)
    for _ in range(8):
        frame.click("#bL"); frame.click("#bR")
        frame.click("#bHD")
        frame.wait_for_timeout(80)
    frame.wait_for_timeout(300)
    return frame.evaluate("""() => {
      const c = document.getElementById('board');
      const d = c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      const s = new Set();
      for (let i=0;i<d.length;i+=4*97) s.add(d[i]+','+d[i+1]+','+d[i+2]);
      const de = document.documentElement;
      const cb = c.getBoundingClientRect();
      return {
        score: document.getElementById('score').textContent,
        rows: document.getElementById('rows').textContent,
        best: document.getElementById('best').textContent,
        canvas: {w: Math.round(cb.width), h: Math.round(cb.height)},
        colours: s.size,
        scrollW: de.scrollWidth, clientW: de.clientWidth,
        bodyH: document.body.getBoundingClientRect().height,
        innerH: window.innerHeight,
      };
    }""")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    # ── fetch exactly what the platform serves ─────────────────────────────
    with urllib.request.urlopen(LAUNCH, timeout=40) as r:
        live_html = r.read().decode()
    print(f"launch HTML : {len(live_html):,} bytes from {LAUNCH}")
    for probe in ["DICE DROP", "LUCKY 28", "BLACKJACK", "QUAD_MULT", "game-container"]:
        print(f"   {probe!r:16} present: {probe in live_html}")
    if "DICE DROP" not in live_html:
        problems.append("launch HTML does not contain our game")

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])

        # ── MODE A: load the launch URL directly ──────────────────────────
        ctx = b.new_context(viewport=MOBILE, device_scale_factor=2,
                            is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(LAUNCH, wait_until="load", timeout=60000)
        pg.wait_for_timeout(800)
        pg.screenshot(path=str(OUT / "live-A-start.png"))
        try:
            stA = play_in_frame(pg.main_frame)
            print("\nMODE A (launch URL):")
            print("   state   :", {k: stA[k] for k in ("score", "rows", "best")})
            print("   canvas  :", stA["canvas"], "colours:", stA["colours"])
            print("   scrollW :", stA["scrollW"], "clientW:", stA["clientW"],
                  "| bodyH:", stA["bodyH"], "innerH:", stA["innerH"])
            if int(str(stA["score"]).replace(",", "") or 0) <= 0:
                problems.append("MODE A: score stayed 0 — not interactive on the live host")
            if stA["colours"] < 5:
                problems.append(f"MODE A: canvas blank ({stA['colours']} colours)")
            if stA["canvas"]["w"] <= 0:
                problems.append("MODE A: board has zero width on the live host")
            if stA["scrollW"] > stA["clientW"] + 1:
                problems.append("MODE A: horizontal scroll on the live host")
        except Exception as e:  # noqa: BLE001
            problems.append(f"MODE A failed: {str(e)[:200]}")
        pg.screenshot(path=str(OUT / "live-A-played.png"))
        ctx.close()

        # ── MODE B: sandboxed srcdoc iframe, exactly how the site renders it ──
        ctx2 = b.new_context(viewport=MOBILE, device_scale_factor=2,
                             is_mobile=True, has_touch=True)
        pg2 = ctx2.new_page()
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        inner = live_html[live_html.find("<div id=\"game-container\">"):]
        framesrc = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                    "<style>html,body{margin:0;padding:0;height:100%;overflow:hidden}"
                    "iframe{width:390px;height:844px;border:0}</style></head><body>"
                    f"<iframe id='f' sandbox='allow-scripts' srcdoc=\"{_html.escape(live_html, quote=True)}\">"
                    "</iframe></body></html>")
        Path("/tmp/srcdoc_host.html").write_text(framesrc)
        pg2.goto(Path("/tmp/srcdoc_host.html").as_uri(), wait_until="load")
        pg2.wait_for_timeout(900)
        try:
            fr = pg2.frame_locator("#f")
            frm = pg2.frames[-1]
            stB = play_in_frame(frm)
            print("\nMODE B (sandboxed srcdoc iframe):")
            print("   state   :", {k: stB[k] for k in ("score", "rows", "best")})
            print("   canvas  :", stB["canvas"], "colours:", stB["colours"])
            if int(str(stB["score"]).replace(",", "") or 0) <= 0:
                problems.append("MODE B: score stayed 0 inside the sandboxed iframe")
            if stB["colours"] < 5:
                problems.append(f"MODE B: canvas blank in sandbox ({stB['colours']} colours)")
        except Exception as e:  # noqa: BLE001
            problems.append(f"MODE B failed: {str(e)[:200]}")
        pg2.screenshot(path=str(OUT / "live-B-srcdoc-played.png"))
        ctx2.close()
        b.close()

    if errs:
        print("\nMODE A JS errors:", errs[:3])
    if errs2:
        print("MODE B JS errors:", errs2[:3])

    rep = {"game_id": GID, "launch_bytes": len(live_html),
           "mode_a": stA if "stA" in dir() else None,
           "mode_b": stB if "stB" in dir() else None,
           "js_errors_a": errs, "js_errors_b": errs2, "problems": problems}
    (OUT / "live-report.json").write_text(json.dumps(rep, indent=2))

    print()
    if problems:
        print("PROBLEMS:")
        for x in problems:
            print(" -", x)
    else:
        print("LIVE GAME VERIFIED — plays on the real host, both render paths")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
