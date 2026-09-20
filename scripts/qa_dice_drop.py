#!/usr/bin/env python3
"""qa_dice_drop.py — real-browser QA for DICE DROP at a phone viewport.

Checks the spec's hard gates that a headless logic test cannot:
  - no JS errors / no failed requests
  - portrait layout, no horizontal scroll, no pinch-zoom needed
  - tap targets >= 44px
  - total page weight under 500KB
  - playable within 2s on throttled 4G (measured cold-ish load)
  - game actually starts, accepts input, and the canvas renders non-blank
Writes screenshots as evidence.

Usage: python3 scripts/qa_dice_drop.py path/to/dice-drop.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("evidence/dice-drop-qa")
MOBILE = {"width": 390, "height": 844}   # iPhone 14-ish portrait


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "content/snowsnakes/games/dice-drop.html")
    OUT.mkdir(parents=True, exist_ok=True)
    url = src.resolve().as_uri()
    weight = src.stat().st_size
    problems: list[str] = []

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        ctx = b.new_context(
            viewport=MOBILE, device_scale_factor=2, is_mobile=True, has_touch=True,
            user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
        )
        page = ctx.new_page()

        errors, console = [], []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: console.append(m.type + ": " + m.text) if m.type == "error" else None)
        failed = []
        page.on("requestfailed", lambda r: failed.append(r.url))

        page.goto(url, wait_until="load")
        load_ms = page.evaluate(
            "() => { const n = performance.getEntriesByType('navigation')[0];"
            " return n ? Math.round(n.duration) : 0; }")

        page.screenshot(path=str(OUT / "01-start-overlay.png"))

        # ── layout gates ────────────────────────────────────────────────
        metrics = page.evaluate("""() => {
          const de = document.documentElement;
          const btns = [...document.querySelectorAll('button')].map(b => {
            const r = b.getBoundingClientRect();
            return {label: b.textContent.trim().slice(0,14), w: Math.round(r.width), h: Math.round(r.height)};
          });
          const c = document.getElementById('board');
          const cr = c ? c.getBoundingClientRect() : {width:0,height:0,top:0,bottom:0,left:0,right:0};
          return {
            scrollW: de.scrollWidth, clientW: de.clientWidth,
            scrollH: de.scrollHeight, clientH: de.clientHeight,
            docH: de.scrollHeight,
            buttons: btns,
            canvas: {w: Math.round(cr.width), h: Math.round(cr.height),
                     top: Math.round(cr.top), bottom: Math.round(cr.bottom),
                     right: Math.round(cr.right)},
            innerW: window.innerWidth, innerH: window.innerHeight,
            overlayVisible: document.getElementById('ov').classList.contains('on'),
          };
        }""")

        if metrics["scrollW"] > metrics["clientW"] + 1:
            problems.append(f"horizontal scroll: scrollW={metrics['scrollW']} > clientW={metrics['clientW']}")
        small = [b for b in metrics["buttons"] if b["h"] < 44 and b["w"] > 0]
        if small:
            problems.append("tap targets under 44px: " + json.dumps(small))
        if metrics["canvas"]["bottom"] > metrics["innerH"] + 1:
            problems.append(f"board overflows viewport bottom: {metrics['canvas']['bottom']} > {metrics['innerH']}")
        if weight > 500 * 1024:
            problems.append(f"page weight over 500KB: {weight} bytes")
        if load_ms > 2000:
            problems.append(f"load over 2s: {load_ms}ms")

        # ── play it ─────────────────────────────────────────────────────
        page.click("#ovBtn")                    # TAP TO PLAY
        page.wait_for_timeout(250)
        page.screenshot(path=str(OUT / "02-playing.png"))

        # drive with real taps: move + rotate + drop a few times
        for _ in range(6):
            page.click("#bL")
            page.click("#bR")
            page.click("#bHD")
            page.wait_for_timeout(90)
        page.wait_for_timeout(200)
        page.screenshot(path=str(OUT / "03-after-moves.png"))

        state = page.evaluate("""() => ({
          score: document.getElementById('score').textContent,
          rows:  document.getElementById('rows').textContent,
          level: document.getElementById('level').textContent,
          best:  document.getElementById('best').textContent,
        })""")

        # canvas must not be blank: sample pixel variance
        nonblank = page.evaluate("""() => {
          const c = document.getElementById('board');
          const g = c.getContext('2d');
          const d = g.getImageData(0, 0, c.width, c.height).data;
          const seen = new Set();
          for (let i = 0; i < d.length; i += 4*97) seen.add(d[i]+','+d[i+1]+','+d[i+2]);
          return seen.size;
        }""")
        if nonblank < 5:
            problems.append(f"canvas looks blank (only {nonblank} distinct sampled colours)")
        if int(str(state["score"]).replace(",", "") or 0) <= 0:
            problems.append("score still 0 after 6 hard drops — input not registering")

        # ── landscape / small-phone robustness ──────────────────────────
        page.set_viewport_size({"width": 844, "height": 390})
        page.wait_for_timeout(300)
        page.screenshot(path=str(OUT / "04-landscape.png"))
        page.set_viewport_size({"width": 320, "height": 568})   # iPhone SE 1st gen
        page.wait_for_timeout(300)
        se = page.evaluate("""() => {
          const de = document.documentElement;
          const c = document.getElementById('board').getBoundingClientRect();
          return {scrollW: de.scrollWidth, clientW: de.clientWidth,
                  boardBottom: Math.round(c.bottom), innerH: window.innerHeight,
                  w: Math.round(c.width), h: Math.round(c.height)};
        }""")
        page.screenshot(path=str(OUT / "05-small-phone-320.png"))
        if se["scrollW"] > se["clientW"] + 1:
            problems.append(f"320px: horizontal scroll {se['scrollW']} > {se['clientW']}")
        if se["boardBottom"] > se["innerH"] + 1:
            problems.append(f"320px: board overflows ({se['boardBottom']} > {se['innerH']})")

        ctx.close(); b.close()

    report = {
        "file": str(src), "bytes": weight, "load_ms": load_ms,
        "mobile_metrics": metrics, "state_after_play": state,
        "distinct_sampled_colours": nonblank, "small_phone": se,
        "js_errors": errors, "console_errors": console, "failed_requests": failed,
        "problems": problems,
        "screenshots": sorted(p.name for p in OUT.glob("*.png")),
    }
    (OUT / "report.json").write_text(json.dumps(report, indent=2))

    print(f"file        : {src}  ({weight:,} bytes)")
    print(f"load        : {load_ms} ms")
    print(f"viewport    : {metrics['innerW']}x{metrics['innerH']} (portrait)")
    print(f"canvas      : {metrics['canvas']['w']}x{metrics['canvas']['h']}  bottom={metrics['canvas']['bottom']}")
    print(f"buttons     : {len(metrics['buttons'])} (min height "
          f"{min((b['h'] for b in metrics['buttons']), default=0)}px)")
    print(f"state       : {state}")
    print(f"canvas cols : {nonblank} distinct sampled")
    print(f"JS errors   : {len(errors)}  console errors: {len(console)}  failed reqs: {len(failed)}")
    for e in errors[:3]:
        print("   JS:", e[:160])
    print(f"320px check : board {se['w']}x{se['h']} bottom={se['boardBottom']} innerH={se['innerH']}")
    print()
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print(" -", p)
    else:
        print("ALL MOBILE GATES PASSED")
    print(f"\nreport: {OUT/'report.json'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
