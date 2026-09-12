#!/usr/bin/env python3
"""Drive the live Snow Beats game headlessly to render a drum loop to WAV.

The game's "Download loop" renders the current 16-step pattern 4x through an
OfflineAudioContext and saves `snow-beats-loop-<bpm>bpm.wav`. This sets the
pattern/BPM in-page and captures the download, so the loop is produced by the
real game rather than reimplemented.

    scripts/snow_beats_loop.py --bpm 128 --out content/experiments/lmms/snow-beats-drums-128.wav
"""
from __future__ import annotations
import argparse, json, os, shutil, sys, urllib.request
from playwright.sync_api import sync_playwright

LOCAL_GAME = "resources/snowsnakes/games-posted/snow-beats-loop-download.html"
TRACKS = ["kick", "snare", "hat", "clap", "ohat", "bass", "lead", "noise"]

# drums only — bass/lead/noise stay empty so synths can be layered in LMMS
DRUM_PATTERN = {
    "kick":  [0, 4, 8, 12, 14],
    "snare": [4, 12],
    "hat":   [0, 2, 4, 6, 8, 10, 12, 14],
    "clap":  [4, 12],
    "ohat":  [6, 14],
    "bass":  [],
    "lead":  [],
    "noise": [],
}


def live_game_url(game_id=97):
    """The launch endpoint returns the live game HTML; prefer it over our copy."""
    try:
        with urllib.request.urlopen(
                f"https://snowsnakes.zerric.xyz/api/games/{game_id}/launch", timeout=25) as r:
            html = r.read().decode()
        if "downloadLoop" in html:
            path = "/tmp/snow_beats_live.html"
            open(path, "w").write(html)
            print(f"  live game HTML: {len(html)} B")
            return "file://" + path
    except Exception as e:
        print(f"  (live launch fetch failed: {e})", file=sys.stderr)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bpm", type=int, default=128)
    ap.add_argument("--out", default="content/experiments/lmms/snow-beats-drums-128.wav")
    a = ap.parse_args()

    url = live_game_url()
    target = url or "file://" + os.path.abspath(LOCAL_GAME)
    print(f"game: {target}")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = "/tmp/snowbeats_dl"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    with sync_playwright() as p:
        br = p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        ctx = br.new_context(accept_downloads=True)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.accept())
        page.goto(target, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_selector("#dlBtn", timeout=20000)

        applied = page.evaluate("""(spec) => {
            bpm = spec.bpm;
            const el = document.getElementById('bpm');
            if (el) { el.value = spec.bpm; el.dispatchEvent(new Event('input')); }
            for (let t = 0; t < TRACKS.length; t++)
                for (let s = 0; s < STEPS; s++) pattern[t][s] = 0;
            spec.rows.forEach(([name, steps]) => {
                const ti = TRACKS.findIndex(t => t.name.toLowerCase() === name);
                if (ti < 0) return;
                steps.forEach(s => { if (s >= 0 && s < STEPS) pattern[ti][s] = 1; });
            });
            refreshGrid();
            let on = 0;
            for (let t = 0; t < TRACKS.length; t++)
                for (let s = 0; s < STEPS; s++) if (pattern[t][s]) on++;
            return {bpm: bpm, stepsOn: on};
        }""", {"bpm": a.bpm, "rows": [[k, v] for k, v in DRUM_PATTERN.items()]})
        print(f"  in-page: bpm={applied['bpm']} steps_on={applied['stepsOn']}")

        with page.expect_download(timeout=60000) as dl:
            page.click("#dlBtn")
        d = dl.value
        saved = os.path.join(tmp, d.suggested_filename)
        d.save_as(saved)
        print(f"  downloaded: {d.suggested_filename} ({os.path.getsize(saved)} B)")
        br.close()

    shutil.copy(saved, a.out)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
