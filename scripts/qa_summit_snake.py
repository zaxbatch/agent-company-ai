#!/usr/bin/env python3
"""CTO independent QA harness for a self-contained HTML5 mobile game.

Checks, at real mobile viewports:
  1. no horizontal scroll / no vertical scroll
  2. canvas has real pixel dimensions (dpr-aware)
  3. START button >= 44x44 css px and a tap leaves the start state
  4. simulated taps on the canvas actually drive the game (altitude advances)
  5. no console errors / page errors
  6. the game survives a SANDBOXED srcdoc iframe (how SnowSnakes renders it)

Usage: venv/bin/python scripts/qa_summit_snake.py <path-to.html> [--url BASE]
"""
from __future__ import annotations
import argparse, json, pathlib, re, sys

from playwright.sync_api import sync_playwright

VIEWPORTS = [
    ("390x844", 390, 844),
    ("360x800", 360, 800),
    ("414x896", 414, 896),
    ("768x1024", 768, 1024),
    ("844x390-landscape", 844, 390),
]

TAP_JS = """
([x, y]) => {
  const c = document.querySelector('canvas');
  const r = c.getBoundingClientRect();
  const cx = r.left + r.width * x, cy = r.top + r.height * y;
  for (const t of ['pointerdown','pointerup']) {
    c.dispatchEvent(new PointerEvent(t, {bubbles:true, cancelable:true, clientX:cx, clientY:cy,
                                          pointerId:1, pointerType:'touch', isPrimary:true, buttons:1}));
  }
}
"""

CHARGE_JS = """
([x, y, holdMs]) => {
  const c = document.querySelector('canvas');
  const r = c.getBoundingClientRect();
  const cx = r.left + r.width * x, cy = r.top + r.height * y;
  c.dispatchEvent(new PointerEvent('pointerdown', {bubbles:true, cancelable:true, clientX:cx,
      clientY:cy, pointerId:1, pointerType:'touch', isPrimary:true, buttons:1}));
  return new Promise(res => setTimeout(() => {
    c.dispatchEvent(new PointerEvent('pointerup', {bubbles:true, cancelable:true, clientX:cx,
        clientY:cy, pointerId:1, pointerType:'touch', isPrimary:true, buttons:1}));
    res(true);
  }, holdMs));
}
"""

STATE_JS = """
() => {
  const d = window.__SUMMIT || window.__GAME || window.__DEBUG || null;
  const c = document.querySelector('canvas');
  return {
    debug: d ? JSON.parse(JSON.stringify(d)) : null,
    canvas: c ? {w: c.width, h: c.height, cw: c.clientWidth, ch: c.clientHeight} : null,
    scrollW: document.documentElement.scrollWidth,
    scrollH: document.documentElement.scrollHeight,
    innerW: window.innerWidth,
    innerH: window.innerHeight,
    bodyOverflow: getComputedStyle(document.body).overflow,
  };
}
"""


def run_file_mode(page, path, label, results):
    page.goto(pathlib.Path(path).as_uri())
    page.wait_for_timeout(600)

    st = page.evaluate(STATE_JS)
    ok = lambda name, cond, extra="": results.append(
        {"check": f"{label}:{name}", "pass": bool(cond), "extra": extra})

    ok("no-h-scroll", st["scrollW"] <= st["innerW"] + 1, f"{st['scrollW']}<={st['innerW']}")
    ok("no-v-scroll", st["scrollH"] <= st["innerH"] + 2, f"{st['scrollH']}<={st['innerH']}")
    ok("canvas-sized", bool(st["canvas"]) and st["canvas"]["w"] > 0 and st["canvas"]["h"] > 0,
       json.dumps(st["canvas"]))
    ok("body-overflow-hidden", st["bodyOverflow"] in ("hidden", "clip"), st["bodyOverflow"])

    # tap the start control (button if present, else a canvas tap)
    btn = page.query_selector("button")
    if btn:
        box = btn.bounding_box() or {}
        ok("button->=44px", box.get("width", 0) >= 44 and box.get("height", 0) >= 44,
           f"{box.get('width')}x{box.get('height')}")
        btn.tap() if hasattr(btn, "tap") else btn.click()
    else:
        page.evaluate(TAP_JS, [0.5, 0.5])
    page.wait_for_timeout(400)

    st2 = page.evaluate(STATE_JS)
    d2 = st2["debug"] or {}
    ok("left-start-state", (d2.get("state") != "start") or (st2["debug"] is None and not btn),
       f"state={d2.get('state')}")

    # simulate alternating wall jumps (tap, and one long hold), driven by real timing
    for i, (x, y, hold) in enumerate([(0.5, 0.6, 30), (0.5, 0.6, 250), (0.5, 0.5, 40),
                                      (0.5, 0.5, 300), (0.5, 0.6, 30), (0.5, 0.5, 260)]):
        page.evaluate(CHARGE_JS, [x, y, hold])
        page.wait_for_timeout(320)

    page.wait_for_timeout(400)
    st3 = page.evaluate(STATE_JS)
    d3 = st3["debug"] or {}
    alt = d3.get("altitude", d3.get("height", d3.get("alt", None)))
    ok("game-advanced", (alt is not None and alt > 0) or d3.get("state") == "play",
       f"altitude={alt} state={d3.get('state')} debug={json.dumps(d3)[:180]}")
    return st3


def run_srcdoc_mode(page, html, label, results):
    """SnowSnakes renders posted code inside a sandboxed iframe -> prove it works there."""
    import html as _html
    host = ("<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;"
            "height:100%}iframe{width:390px;height:844px;border:0}</style></head><body>"
            f"<iframe id='f' sandbox='allow-scripts' srcdoc=\"{_html.escape(html, quote=True)}\">"
            "</iframe></body></html>")
    page.set_content(host)
    page.wait_for_timeout(1200)
    fr = page.frames[1] if len(page.frames) > 1 else page.frame_locator("#f").first

    ok = lambda name, cond, extra="": results.append(
        {"check": f"{label}:{name}", "pass": bool(cond), "extra": extra})

    try:
        fr.evaluate(STATE_JS)
        ok("iframe-frame-reachable", True, "frame handle ok")
    except Exception as e:  # noqa
        ok("iframe-frame-reachable", False, str(e)[:200])
        return None

    st = fr.evaluate(STATE_JS)
    ok("iframe-canvas-rendered", bool(st["canvas"]) and st["canvas"]["w"] > 0,
       json.dumps(st["canvas"]))

    # tap start then drive the game inside the sandboxed frame
    caught = []
    fr.evaluate("() => { window.__err=[]; addEventListener('error', e=>window.__err.push(String(e.message))); }")
    try:
        b = fr.query_selector("button")
        (b.tap() if hasattr(b, "tap") else b.click()) if b else fr.evaluate(TAP_JS, [0.5, 0.5])
    except Exception as e:
        caught.append(str(e)[:150])
    fr.wait_for_timeout(500)
    for x, y, hold in [(0.5, 0.6, 30), (0.5, 0.5, 260), (0.5, 0.6, 40), (0.5, 0.5, 280)]:
        try:
            fr.evaluate(CHARGE_JS, [x, y, hold])
        except Exception as e:
            caught.append(str(e)[:150])
        fr.wait_for_timeout(320)

    st2 = fr.evaluate(STATE_JS)
    d2 = st2["debug"] or {}
    alt = d2.get("altitude", d2.get("height", d2.get("alt", None)))
    ok("iframe-in-sandbox-tap-works", (alt is not None and alt > 0) or d2.get("state") == "play",
       f"altitude={alt} state={d2.get('state')} errors={caught[:2]}")
    try:
        errs = fr.evaluate("() => window.__err || []")
        ok("iframe-no-window-errors", len(errs) == 0, str(errs[:3]))
    except Exception:
        pass
    return st2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--shots", default="content/snowsnakes/games/_qa")
    a = ap.parse_args()

    src = pathlib.Path(a.path)
    html = src.read_text()
    results, shots = [], pathlib.Path(a.shots)
    shots.mkdir(parents=True, exist_ok=True)
    stem = src.stem

    errors = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for label, w, h in VIEWPORTS:
            ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2,
                                has_touch=True, is_mobile=(w < 600))
            pg = ctx.new_page()
            pg.on("console", lambda m: errors.append((label, m.type, m.text))
                  if m.type == "error" else None)
            pg.on("pageerror", lambda e: errors.append((label, "pageerror", str(e))))
            try:
                run_file_mode(pg, src, label, results)
                pg.screenshot(path=str(shots / f"{stem}-{label}.png"))
            except Exception as e:
                results.append({"check": f"{label}:EXCEPTION", "pass": False, "extra": str(e)[:300]})
            ctx.close()

        # sandbox/srcdoc proof at the primary mobile viewport
        ctx = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                            has_touch=True, is_mobile=True)
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(("srcdoc", "pageerror", str(e))))
        try:
            run_srcdoc_mode(pg, html, "srcdoc-390x844", results)
            pg.screenshot(path=str(shots / f"{stem}-srcdoc.png"))
        except Exception as e:
            results.append({"check": "srcdoc-390x844:EXCEPTION", "pass": False, "extra": str(e)[:300]})
        ctx.close()
        b.close()

    real_errs = [e for e in errors if "favicon" not in e[2]]
    passed = sum(1 for r in results if r["pass"])
    print(json.dumps({"file": str(src), "bytes": src.stat().st_size,
                      "checks_passed": passed, "checks_total": len(results),
                      "console_errors": real_errs[:6], "results": results}, indent=2))
    fails = [r for r in results if not r["pass"]]
    print(f"\n=== {'ALL PASS' if not fails else 'FAILURES'}: {passed}/{len(results)} checks, "
          f"{len(real_errs)} console/page errors ===")
    return 1 if fails or real_errs else 0


if __name__ == "__main__":
    sys.exit(main())
