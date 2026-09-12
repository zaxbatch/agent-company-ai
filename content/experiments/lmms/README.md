# Local LMMS beat tool (experiment, internal)

Scope: **local internal tooling.** Not a product, not a tracked initiative
(Zerric, 2026-09-12). Nothing here is deployed to public web properties.

## Why it works
LMMS 1.2.x project files (`.mmp`) are plain XML, and `lmms render` runs
headless — no X server needed:

    QT_QPA_PLATFORM=offscreen lmms render project.mmp -o out.wav -f wav

So a beat is reproducible from a spec instead of hand-drawn in a GUI.

## Files
| File | Role |
|---|---|
| `scripts/lmms_spec.py` | Spec model + validation (chords, layers, sections) |
| `scripts/lmms_beat.py` | Spec -> `.mmp` -> master WAV (+ stems, + MP3) |
| `scripts/lmms_qa.py` | QA gate: audible, clipping, tempo, arrangement, spectrum |

## Use
    python3 scripts/lmms_beat.py --spec content/experiments/lmms/beat-16bar.spec.json \
        --stems --mp3
    venv/bin/python scripts/lmms_qa.py content/experiments/lmms/beat-16bar.wav \
        --spec content/experiments/lmms/beat-16bar.spec.json

## Spec shape
    {
      "title": "beat-16bar", "bpm": 128,
      "progression": ["Am", "F", "C", "G"],
      "sections": [
        {"name": "intro", "bars": 2, "layers": ["kick", "bass"]},
        {"name": "drop",  "bars": 4, "layers": ["kick","snare","hat","bass","stab"]},
        {"name": "drop2", "bars": 6, "fill": true,
         "layers": ["kick","snare","clap","hat","openhat","bass","stab"]}
      ]
    }

Layers: `kick snare clap hat openhat crash bass stab`.
Chords: `Am A F Fm C G Dm Em D E Bb`.
`"fill": true` puts a 16th snare roll + bass walk-up on the section's last bar.

## Known constraints (do not rediscover these)
1. **Master fader must stay <= 0.5** in generated projects. At 0.71 the sum of
   8 tracks clipped (1 sample at 0.0 dBFS). `MASTER_FADER` in `lmms_beat.py`.
2. **Samples resolve relative to `/usr/share/lmms/samples`** — e.g.
   `src="drums/kick_hard01.ogg"`. Bundled kit: 1004 samples, drums in `drums/`.
3. **Track container nesting matters.** Instrument tracks + patterns must sit
   inside `bbtrack > bbtrackcontainer`, with a sibling `bbtco` in the song
   track, or the pattern never plays.
4. **Section contrast is the thing to watch.** Adding only transient hits
   (claps, ghost snares) barely moves RMS. Contrast comes from *removing whole
   layers* — e.g. the `break` section drops the kick. QA fails below 15% range.
5. `-i sincbest` is pointless here (samples and output are both 44.1k) and
   slow. Default interpolation is fine.

## Verified baseline (2026-09-12)
16 bars @ 128 BPM, 31.87 s: peak -1.36 dBFS, 0 clipped, RMS -17.20 dBFS,
tempo error 0.31%, section range 1.32x (quietest `break`, loudest `drop2`).
