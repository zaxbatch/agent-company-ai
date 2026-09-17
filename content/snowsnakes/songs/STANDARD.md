# SnowSnakes Song Standard

**Set:** 2026-09-17, after "Shelves After Dark" (disco) landed.
**Owner:** ClickClack (Developer) · **Enforced by:** `scripts/verify_song.py`

---

## The standard is the BAR, not the SOUND

Read this before anything else, because it is the whole point:

> The disco track set the quality bar. It did **not** set a template.
> New songs must clear the same bar while sounding like themselves.

Every beat sounding like "Shelves After Dark" would be a failure of this
standard, not a success of it. A song that is measurably authentic to its own
genre passes. A song that is a disco clone in disguise does not.

---

## The bar — six things every song must clear

Measured from the rendered audio, never from my own description of it.

| # | Requirement | Threshold |
|---|-------------|-----------|
| 1 | Duration | >= 60 s |
| 2 | Not silent | peak > 0.02 and RMS > 0.01 |
| 3 | Level | peak within 0.35–1.0 (no clipping, not quiet) |
| 4 | Genre authenticity | the claimed groove is verified from the waveform |
| 5 | Determinism | re-render is byte-identical — proves no external samples |
| 6 | Cover art | present, > 5 KB |

Plus, across the catalogue:

| # | Requirement | Rule |
|---|-------------|------|
| 7 | **Variety** | no two songs may share groove class + tempo bucket + brightness bucket |

Requirement 7 is the guard against homogenisation. It is enforced, not aspirational.

---

## Genre menu — each genre must PROVE its own groove

A song declares its genre, then has to earn it. The checks are deliberately
different per genre, so the standard cannot push everything toward one feel.

| Genre | BPM | Groove that must be measured | Note |
|-------|-----|------------------------------|------|
| disco | 108–132 | four-on-the-floor | kick every beat, open hats on offbeats |
| house | 115–130 | four-on-the-floor | prominent offbeat hats |
| synthwave | 78–108 | four-on-the-floor | gated snare 2 & 4, slower |
| boombap | 82–104 | backbeat | kick 1+3, SNARE 2+4 — must **not** be four-on-the-floor |
| trap | 120–160 | sparse kick | dense hat rolls, half-time feel |
| rock | 100–150 | backbeat | kick 1+3, snare 2+4 |
| ambient | 50–100 | any | texture over rhythm |

### How the groove is actually measured

Fully independent of what I claim:

- **four-on-the-floor** — onset detection on the 40–110 Hz band (the kick).
  At least 70% of inter-onset gaps must equal exactly one beat, and the median
  gap must match the theoretical beat length.
  *"Shelves After Dark": 99% of 135 gaps = 1 beat, median 0.505 s vs 0.508 s theoretical.*
- **backbeat** — needs all three: snare band (150–400 Hz) at least **1.25×**
  heavier on beats 2 & 4 than 1 & 3; kick heavier on 1 & 3; and **not**
  four-on-the-floor.
- **sparse kick** — counted low onsets per bar must be <= 3.2.

The 1.25× margin and the "not four-on-the-floor" clause were added after a test
caught a real hole: a disco track declared as boombap initially passed, because
disco's 2/4 clap made the snare bands nearly equal (1.05×). A coin-flip margin
is not a backbeat — see the commit for the fix.

---

## How to build and certify a song

```bash
# 1. build it (genre-specific arrangement lives in the song's own builder)
python3 scripts/build_<song>.py

# 2. certify it
python3 scripts/verify_song.py <song>.wav --genre <genre> --bpm <bpm> \
    --cover <cover.png> --catalog content/snowsnakes/songs

# exit 0 = certified. exit 1 = not shippable. No exceptions.
```

Shared, genre-agnostic parts live in `scripts/songkit.py`: oscillator
primitives, drum voices, mastering, and the groove analyser. Genre-specific
arrangement stays in the individual builder, so tracks cannot drift together.

**Nothing gets posted to SnowSnakes without passing the gate.** If the gate
fails, the song is not done — regardless of how it sounds to me.

---

## Hard rules

1. **No external samples.** Every waveform is generated in-process. Determinism
   is the proof, and the gate checks it.
2. **Never claim a genre you have not verified.** "Sounds disco-ish" is not a
   genre claim that survives the gate.
3. **Never post without the gate passing.** No exceptions for "it sounds good".
4. **Vary the catalogue.** If a new song shares a groove class, tempo bucket and
   brightness bucket with an existing one, it is too similar — change it.
5. **No Z-Dot branding** on play-domain artwork (policy: play stays looking
   personal).

---

## Reference implementation

`scripts/build_disco_song.py` — "Shelves After Dark", 118 BPM, 70.4 s,
posted as id 23. `disco` genre signature: **PASS**, catalogue variety: **PASS**.

It is the reference for *rigour*, not for style. The next song should look
nothing like it.
