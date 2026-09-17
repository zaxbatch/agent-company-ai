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

---

## Gate self-test matrix (regression suite)

The gate is only trustworthy if it can REJECT. Verified 2026-09-17:

| Track | Claimed as | Result | Why |
|-------|-----------|--------|-----|
| Shelves After Dark (disco) | disco @ 118 | **PASS** | 99% of kick gaps = 1 beat |
| Dust on the Shelf (boombap) | boombap @ 92 | **PASS** | snare 2,4 at 49.8× beats 1,3; 6% 4-on-floor |
| Shelves After Dark | boombap @ 92 | **FAIL** | measured 118.1 BPM vs claimed 92 |
| Dust on the Shelf | disco @ 118 | **FAIL** | only 25% of gaps = 1 beat |

Both reference tracks PASS their own genre and FAIL the other's. That is the
standard working as intended: **same bar, different music.**

Their measured profiles, which the catalogue rule keeps apart:

| | tempo | brightness | groove |
|---|---|---|---|
| Shelves After Dark | 118.1 BPM | 7,617 Hz | four-on-the-floor |
| Dust on the Shelf | 90.3 BPM | 10,177 Hz | backbeat |

---

## Two real holes found by testing (both fixed)

Both were found because the gate was tested against tracks it should REJECT,
not just ones it should accept. Recording them so the reasoning survives:

1. **Backbeat check accepted a four-on-the-floor track.** The original rule was
   "snare on 2 & 4 louder than 1 & 3". Disco's 2/4 clap made those bands
   nearly equal (1.05×) and it squeezed through. Fixed by requiring a **1.25×
   margin**, kick heavier on 1 & 3, **and** not-four-on-the-floor.

2. **Sustained energy was used to measure a transient.** Boom-bap's Rhodes
   chords sat in the 150–400 Hz snare band and made beats 1/3 read *louder*
   than 2/4. A backbeat is a transient, so it is now measured as energy
   **flux** (the positive jump), not level. Margin went from a wrong 0.75× to
   a correct 49.8×.

3. **A track could dodge the groove rules by lying about its tempo.** The
   groove checks compare onset gaps to the *claimed* beat length, so declaring
   118 BPM disco as "92 BPM boombap" silently disabled them. The gate now
   **measures the tempo from the audio** and fails any claim off by more than 6%.

The general lesson, which is now the rule: **a gate that has only ever been run
against passing inputs has not been tested.**

---

## Feedback loop case study: "Last One on the Shelf" (2026-09-17)

Zerric's verdict on the album: *"all of em slap except for last one on the shelf.
I guess that's a relaxing outro. Maybe we'll keep it."*

**The gate had already flagged the same track.** Independent of his ear, the
measurement said it was the weakest:

| # | Track | Sustained climax | Length |
|---|-------|-----------------|--------|
| 1 | Midnight Aisle | 0.99 | 83s |
| 2 | Slack in the Cooler | 0.98 | 130s |
| 3 | Frostbite Boulevard | 0.98 | 130s |
| 4 | Milk Carton Club | 0.99 | 78s |
| 5 | Sour Turn | 0.89 | 84s |
| **6** | **Last One on the Shelf** | **0.83** ← lowest | **172s** ← longest |

Two problems, and the second is the real one: the weakest track was also the
**longest**, which is backwards for an outro. A human ear and an RMS-per-bar
measurement agreeing on the same track is the best evidence yet that the gate
measures something real.

### What changed

- **New `outro` shape** in albumkit: settle → warm → swell → dissolve → coda.
  Short by design: 29 bars instead of 51.
- **Climax is now a distinct section**, not an even wash. 6 bars → 8 bars wide, so
  a 5-bar measurement window fits inside it.
- **The swell must be the unambiguous peak.** The first attempt failed: the coda's
  ringing tonic chord out-peaked the swell (0.74 on the 5-bar window), so the
  resolution was shouting louder than the climax. Tamed the coda, widened the
  swell.
- **A real harmonic resolve.** The progression now lands on a sustained A minor
  with a rising bell figure as a sign-off, so it *ends* rather than just stopping.

### Result

| | before | after |
|---|---|---|
| Length | 172.0s | **98.7s** |
| Sustained climax | 0.83 | **0.96** |
| Dynamic range | 7.5× | **9.5×** |
| Gate | pass (marginal) | **pass** |

The gate's own threshold (0.86) had let 0.83 through. Worth remembering: a
marginal pass is a signal, not a pass. The bar for a track that made it is
0.96-0.99 — anything sitting near the threshold deserves a second look.
