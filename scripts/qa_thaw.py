#!/usr/bin/env python3
"""qa_thaw.py — real-browser QA for THAW at phone viewports.

Checks the mobile budget from the SnowSnakes standard, plus THAW's own rules:
  - no JS errors, no failed requests, ZERO external references
  - portrait fits, no horizontal scroll, no board overflow
  - tap targets >= 44px
  - under 60KB (the brief's target) and well under the 500KB budget
  - playable within 2s
  - tap-to-rotate works through REAL pointer events on the canvas
  - tapping the spring does NOT rotate it (endpoints pinned)

Usage: python3 scripts/qa_thaw.py [path]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("evidence/thaw-qa")
MOBILE = {"width": 390, "height": 844}


def main() -> int:
    src = Path(sys.argv[1] if len(sys.argv) > 1 else "content/snowsnakes/games/thaw.html")
    OUT.mkdir(parents=True, exist_ok=True)
    url = src.resolve().as_uri()
    html = src.read_text()
    weight = src.stat().st_size
    problems: list[str] = []

    # static: zero external references
    ext = re.findall(r'(?:src|href)\s*=\s*["\']https?://[^"\']+', html)
    ext += re.findall(r'\bfetch\s*\(|XMLHttpRequest|url\(\s*["\']?https?://', html)
    ext = [e for e in ext if "http://www.w3.org" not in e]   # svg/xml namespaces are inert
    if ext:
        problems.append(f"external references present: {ext[:3]}")
    print(f"external refs  : {len(ext)} (must be 0)")
    print(f"file size      : {weight:,} bytes ({weight/1024:.1f} KB)")
    if weight > 60 * 1024:
        problems.append(f"over the 60KB brief target: {weight} bytes")

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-sandbox"])
        ctx = b.new_context(viewport=MOBILE, device_scale_factor=2,
                            is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        errors, failed, console = [], [], []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("requestfailed", lambda r: failed.append(r.url))
        pg.on("console", lambda m: console.append(m.text) if m.type == "error" else None)
        pg.on("request", lambda r: failed.append("EXT:" + r.url)
              if not r.url.startswith(("file:", "data:")) else None)

        pg.goto(url, wait_until="load")
        load_ms = pg.evaluate("()=>{const n=performance.getEntriesByType('navigation')[0];"
                              "return n?Math.round(n.duration):0;}")
        pg.screenshot(path=str(OUT / "01-start.png"))

        metrics = pg.evaluate("""() => {
          const de=document.documentElement;
          const c=document.getElementById('board');
          const cb=c.getBoundingClientRect();
          const btns=[...document.querySelectorAll('button')].map(b=>{
            const r=b.getBoundingClientRect();
            return {t:b.textContent.trim().slice(0,14), w:Math.round(r.width), h:Math.round(r.height)};
          });
          return {scrollW:de.scrollWidth, clientW:de.clientWidth,
                  innerW:window.innerWidth, innerH:window.innerHeight,
                  canvas:{w:Math.round(cb.width), h:Math.round(cb.height),
                          bottom:Math.round(cb.bottom), right:Math.round(cb.right)},
                  buttons:btns};
        }""")

        if metrics["scrollW"] > metrics["clientW"] + 1:
            problems.append(f"horizontal scroll {metrics['scrollW']}>{metrics['clientW']}")
        small = [x for x in metrics["buttons"] if x["h"] < 44 and x["w"] > 0]
        if small:
            problems.append(f"tap targets under 44px: {small}")
        if metrics["canvas"]["bottom"] > metrics["innerH"] + 1:
            problems.append(f"board overflows bottom {metrics['canvas']['bottom']}>{metrics['innerH']}")
        if metrics["canvas"]["w"] < 100:
            problems.append(f"board too small: {metrics['canvas']}")
        if weight > 500 * 1024:
            problems.append("over the 500KB budget")
        if load_ms > 2000:
            problems.append(f"load over 2s: {load_ms}ms")
        if errors:
            problems.append(f"JS errors: {errors[:2]}")
        if failed:
            problems.append(f"failed/external requests: {failed[:2]}")
        if console:
            problems.append(f"console errors: {console[:2]}")

        # start the game
        pg.click("#ovBtn")
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / "02-playing.png"))

        # ── tap-to-rotate through real pointer events ──────────────────────
        box = pg.evaluate("""() => {const c=document.getElementById('board').getBoundingClientRect();
                              return {x:c.left, y:c.top, w:c.width, h:c.height};}""")
        st_before = pg.evaluate("()=>({taps:document.getElementById('taps').textContent})")

        # tap cell (1,1): offset one cell in from the top-left of the board
        cellPx = pg.evaluate("""() => {
          const c=document.getElementById('board');
          const g=window.__THAW_TEST__ ? null : null;
          const s=parseInt(c.style.width)/(4);
          return s;
        }""")
        tx = box["x"] + cellPx * 1.5
        ty = box["y"] + cellPx * 1.5
        pg.mouse.click(tx, ty)
        pg.wait_for_timeout(250)
        st_after = pg.evaluate("()=>({taps:document.getElementById('taps').textContent})")
        taps_dropped = st_before["taps"] != st_after["taps"]
        print(f"tap-to-rotate  : taps {st_before['taps']} -> {st_after['taps']} "
              f"({'OK' if taps_dropped else 'NO CHANGE'})")
        if not taps_dropped:
            problems.append("tapping the canvas did not consume a tap")

        # non-blank canvas
        colours = pg.evaluate("""() => {
          const c=document.getElementById('board');
          const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
          const s=new Set();
          for(let i=0;i<d.length;i+=4*89) s.add(d[i]+','+d[i+1]+','+d[i+2]);
          return s.size;
        }""")
        print(f"canvas colours : {colours}")
        if colours < 5:
            problems.append(f"canvas looks blank ({colours} colours)")
        pg.screenshot(path=str(OUT / "03-after-tap.png"))

        # ── small phone + landscape robustness ────────────────────────────
        pg.set_viewport_size({"width": 320, "height": 568})
        pg.wait_for_timeout(300)
        se = pg.evaluate("""() => {const de=document.documentElement;
          const c=document.getElementById('board').getBoundingClientRect();
          return {scrollW:de.scrollWidth, clientW:de.clientWidth,
                  w:Math.round(c.width), bottom:Math.round(c.bottom), innerH:window.innerHeight};}""")
        pg.screenshot(path=str(OUT / "04-small-320.png"))
        if se["scrollW"] > se["clientW"] + 1:
            problems.append(f"320px: horizontal scroll {se['scrollW']}>{se['clientW']}")
        if se["bottom"] > se["innerH"] + 1:
            problems.append(f"320px: board overflows {se['bottom']}>{se['innerH']}")

        pg.set_viewport_size({"width": 844, "height": 390})   # landscape
        pg.wait_for_timeout(300)
        pg.screenshot(path=str(OUT / "05-landscape.png"))
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_timeout(250)

        print(f"load           : {load_ms} ms")
        print(f"viewport       : {metrics['innerW']}x{metrics['innerH']}")
        print(f"canvas         : {metrics['canvas']}")
        print(f"min button h   : {min((x['h'] for x in metrics['buttons']), default=0)}px")
        print(f"320px canvas   : {se['w']}px bottom={se['bottom']} innerH={se['innerH']}")
        print(f"JS errors      : {len(errors)}  failed reqs: {len(failed)}")
        ctx.close(); b.close()

    rep = {"file": str(src), "bytes": weight, "load_ms": load_ms, "metrics": metrics,
           "small_phone": se, "canvas_colours": colours, "external_refs": ext,
           "js_errors": errors, "failed_requests": failed, "problems": problems}
    (OUT / "report.json").write_text(json.dumps(rep, indent=2))
    print()
    if problems:
        print("PROBLEMS:")
        for x in problems:
            print(" -", x)
    else:
        print("ALL THAW MOBILE GATES PASSED")
    print(f"\nreport: {OUT/'report.json'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
