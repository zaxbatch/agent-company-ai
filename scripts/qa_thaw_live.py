#!/usr/bin/env python3
"""qa_thaw_live.py — prove the PUBLISHED THAW plays on the real SnowSnakes host.

MODE A: GET /api/games/<id>/launch — the exact HTML the platform serves.
        NB the host wraps the whole document inside <div id="game-container">,
        nesting a second doctype/html/head/body. Verified, not assumed.
MODE B: sandboxed srcdoc iframe (sandbox="allow-scripts"), which is how the
        site renders posted code.

Plays by TAPPING THE CANVAS with real pointer events, so it exercises the actual
input path a thumb would.

Usage: python3 scripts/qa_thaw_live.py [game_id]
"""
from __future__ import annotations

import html as _html
import json
import sys
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

GID = sys.argv[1] if len(sys.argv) > 1 else "125"
LAUNCH = f"https://snowsnakes.zerric.xyz/api/games/{GID}/launch"
OUT = Path("evidence/thaw-qa")
MOBILE = {"width": 390, "height": 844}


def play(frame) -> dict:
    """Start THAW, tap tiles through real clicks, and report the state."""
    frame.wait_for_selector("#ovBtn", timeout=25000)
    frame.click("#ovBtn")
    frame.wait_for_timeout(350)

    box = frame.evaluate("""() => {const c=document.getElementById('board').getBoundingClientRect();
        return {x:c.left, y:c.top, w:c.width, h:c.height};}""")
    side = frame.evaluate("()=>parseFloat(document.getElementById('board').style.width)")
    n = frame.evaluate("()=>{const g=document.getElementById('level');return 4;}")
    cell = side / n
    before = frame.evaluate("()=>document.getElementById('taps').textContent")

    # tap a handful of interior tiles (a real thumb, roughly)
    taps = 0
    for (gx, gy) in [(1, 1), (2, 1), (1, 2), (2, 2), (1, 1)]:
        cx = box["x"] + cell * (gx + 0.5)
        cy = box["y"] + cell * (gy + 0.5)
        frame.page.mouse.click(cx, cy)
        frame.wait_for_timeout(70)
        taps += 1

    after = frame.evaluate("()=>document.getElementById('taps').textContent")
    colours = frame.evaluate("""() => {
      const c=document.getElementById('board');
      const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
      const s=new Set();
      for(let i=0;i<d.length;i+=4*89) s.add(d[i]+','+d[i+1]+','+d[i+2]);
      return s.size;
    }""")
    state = frame.evaluate("""() => {
      const de=document.documentElement;
      const c=document.getElementById('board').getBoundingClientRect();
      return {taps:document.getElementById('taps').textContent,
              par:document.getElementById('par').textContent,
              level:document.getElementById('level').textContent,
              over: document.getElementById('ov').classList.contains('on'),
              overlayText: document.getElementById('ovCard').innerText.slice(0,60),
              canvas:{w:Math.round(c.width), h:Math.round(c.height)},
              scrollW:de.scrollWidth, clientW:de.clientWidth};
    }""")
    state["taps_before"] = before
    state["taps_after"] = after
    state["taps_tried"] = taps
    state["colours"] = colours
    return state


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    with urllib.request.urlopen(LAUNCH, timeout=40) as r:
        live_html = r.read().decode()
    print(f"launch HTML : {len(live_html):,} bytes from {LAUNCH}")
    for probe in ["THAW", "parFromMoves", "mulberry32", "game-container"]:
        print(f"   {probe!r:14} present: {probe in live_html}")
    if "parFromMoves" not in live_html:
        problems.append("launch HTML does not contain my THAW code")

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])

        # MODE A: launch URL directly
        ctx = b.new_context(viewport=MOBILE, device_scale_factor=2,
                            is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(LAUNCH, wait_until="load", timeout=60000)
        pg.wait_for_timeout(700)
        pg.screenshot(path=str(OUT / "live-A-start.png"))
        try:
            stA = play(pg.main_frame)
            print("\nMODE A (launch URL):")
            print(f"   taps {stA['taps_before']} -> {stA['taps_after']} "
                  f"(spent {stA['taps_tried']}) | par {stA['par']} | level {stA['level']}")
            print(f"   canvas {stA['canvas']} | colours {stA['colours']}")
            print(f"   scrollW {stA['scrollW']} vs clientW {stA['clientW']}")
            if stA["taps_before"] == stA["taps_after"]:
                problems.append("MODE A: taps did not decrement — not interactive on the host")
            if stA["colours"] < 5:
                problems.append(f"MODE A: canvas blank ({stA['colours']})")
            if stA["canvas"]["w"] <= 0:
                problems.append("MODE A: board has zero width")
            if stA["scrollW"] > stA["clientW"] + 1:
                problems.append("MODE A: horizontal scroll on the host")
        except Exception as e:  # noqa: BLE001
            problems.append(f"MODE A failed: {str(e)[:180]}")
        pg.screenshot(path=str(OUT / "live-A-played.png"))
        ctx.close()

        # MODE B: sandboxed srcdoc iframe
        ctx2 = b.new_context(viewport=MOBILE, device_scale_factor=2,
                             is_mobile=True, has_touch=True)
        pg2 = ctx2.new_page()
        errs2 = []
        pg2.on("pageerror", lambda e: errs2.append(str(e)))
        host = ("<!DOCTYPE html><html><head><meta charset='utf-8'>"
                "<style>html,body{margin:0;height:100%;overflow:hidden}"
                "iframe{width:390px;height:844px;border:0}</style></head><body>"
                f"<iframe id='f' sandbox='allow-scripts' srcdoc=\"{_html.escape(live_html, quote=True)}\">"
                "</iframe></body></html>")
        Path("/tmp/thaw_srcdoc_host.html").write_text(host)
        pg2.goto(Path("/tmp/thaw_srcdoc_host.html").as_uri(), wait_until="load")
        pg2.wait_for_timeout(900)
        try:
            stB = play(pg2.frames[-1])
            print("\nMODE B (sandboxed srcdoc iframe):")
            print(f"   taps {stB['taps_before']} -> {stB['taps_after']} | "
                  f"par {stB['par']} | level {stB['level']}")
            print(f"   canvas {stB['canvas']} | colours {stB['colours']}")
            if stB["taps_before"] == stB["taps_after"]:
                problems.append("MODE B: taps did not decrement inside the sandbox")
            if stB["colours"] < 5:
                problems.append(f"MODE B: canvas blank in sandbox ({stB['colours']})")
        except Exception as e:  # noqa: BLE001
            problems.append(f"MODE B failed: {str(e)[:180]}")
        pg2.screenshot(path=str(OUT / "live-B-srcdoc.png"))
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
        print("THAW VERIFIED LIVE — plays on the real host, both render paths")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
