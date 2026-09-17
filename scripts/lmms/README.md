# LMMS track generation — status and findings

**Status: NOT WORKING YET.** No LMMS-authored track has passed the album gate.

## What IS proven

- **LMMS renders headless.** `QT_QPA_PLATFORM=offscreen lmms render x.mmp -o out.wav`
  produces real audio on this box (LMMS 1.2.2, no X display, no xvfb needed).
  `lmms rendertracks` also works and renders each track to its own file, which is
  how the bugs below were isolated.
- **`lmms dump` prints `qUncompress: Z_DATA_ERROR` for LMMS's OWN shipped projects.**
  It is benign, not a sign of a corrupt file. Ignore it.

## Project format rules discovered

A hand-written project needs the whole skeleton, not just the music:

1. `<trackcontainer>`, `<fxmixer>`, `<timeline>` alone is not enough — LMMS exits 0
   and writes **no file**. The automation track, `ControllerRackView`, `pianoroll`,
   `automationeditor`, `projectnotes` and `<controllers>` are all required. The
   skeleton is therefore cloned from `/usr/share/lmms/projects/tutorials/`.
2. The automation track is a **sibling** of `<trackcontainer>`, not a child.
   Cutting the file at `<track type="6">` deletes the container's closing tag and
   the project fails to load.
3. A `<pattern>` is a child of the instrument `<track type="0">`, NOT a sibling of
   `<bbtrack>`. Wrong placement renders the correct length in **total silence**,
   with the warning `Track::getTCO(0), but TCO 0 doesn't exist`.
4. `mastervol` matters: six tracks summed at vol 100 clipped to full scale, which
   flattened the dynamics and made the intended dip read as the loudest section.

## Bugs found in this generator (fixed)

- **Beats were passed as bars.** A four-beat drum figure spanned four bars, so the
  kick sounded only on even bars. Offsets are now divided by 4 (beats per bar).
- **`steps="16"` on a 32-bar pattern.** Copied from the 1-bar tutorial pattern.

## Still broken

With the fixes above, timing is STILL wrong:

| Project | Intended | Rendered |
|---------|----------|----------|
| 32-bar track @126 | 61.0 s | 125.7 s |
| kick, every beat | 4 hits/bar | 2 hits/bar (median gap 0.952 s vs 0.476 s) |
| 16-bar pattern | 16 bars | kick on even bars only |

Hand-written `<pattern len=...>` / `<bbtco len=...>` / `<timeline lp1pos=...>`
interact in a way not yet matched. Guessing has cost three failed attempts.

## Plan

Stop hand-writing project XML. Drive LMMS the way it is designed to be driven:

1. Emit a **Type-1 MIDI file** (unambiguous PPQ timing — no XML semantics to guess).
2. Let LMMS import it so **LMMS authors its own project** (`lmms --import x.mid -e`).
3. `lmms render` that project.
4. Gate the result with `albumkit.verify_shape_positions()`.

## Safety property (this is the important part)

The render was caught, not shipped. `albumkit.verify_shape_positions()` fails any
render whose measured per-section energy does not match its declared arrangement:

```
FAIL  DIP: energy as declared    measured 0.78, declared 0.30
FAIL  declared dip IS the quietest   declared dip = DIP, actually quietest = intro
FAIL  declared climax IS the loudest declared climax = CLIMAX, actually loudest = build
```

The earlier `verify_structure()` PASSED this same render, because it only asked
whether *some* 5-bar window was quiet — the intro satisfied it while the real
breakdown was the loudest part of the song. That blind spot is now closed.
