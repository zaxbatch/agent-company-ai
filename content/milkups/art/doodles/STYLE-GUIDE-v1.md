# DOODLE STYLE GUIDE — Z-Dot LLC
**Revision:** `STYLE-GUIDE-v1`
**Created (UTC):** 2026-09-12T05:40:00Z
**Owner:** NinjaNerd (CTO)
**Status:** Rev 1 — first revision. **No prior revision exists.** Any statement
referencing an earlier revision ID is unsupported and should be treated as a
false-completion claim until that revision is produced with a path and hash.

## 1. Why this file exists
QA item 5 (style consistency) has been unverifiable because no revision was named.
An unnamed style guide cannot be checked against, so "on-brand" was unfalsifiable.
This revision is deliberately written as **measurable numbers**, not adjectives.

## 2. Canvas and format
| Property | Value |
|---|---|
| Canvas | 700 x 900 px (matches the SnowSnakes doodle canvas) |
| Safe margin | 40 px on all sides |
| Colour mode | RGB (screen) / convert to CMYK only for print runs |
| Export (programmatic) | PNG |
| Export (vector, if hand-drawn) | SVG or 300 dpi PNG minimum |
| Naming | `<template_id>-seed<int>.png` (programmatic) / `doodle-<YYYY-MM-DD>-<nn>-<slug>.<ext>` (batch) |

## 3. Palette lock (hex — exact values, no substitutions)
| Token | Hex | Use |
|---|---|---|
| paper | `#FDFCF7` | Background only |
| ink | `#24344A` | All line work, text |
| body | `#DFF2FF` | Primary character fill |
| accent | `#E24A4A` | One focal accent per panel, maximum |
| snow | `#78BEF0` | Cold/motif accents, labels |

Any pixel cluster outside this list occupying >0.5% of canvas = **divergence**.
Divergences are logged with asset ID + measured value + severity. They are never
silently retouched.

## 4. Line work
| Property | Target | Tolerance |
|---|---|---|
| Modal stroke width | 4 px @ 700 px canvas (5.7 px @ 1000 px) | ±15% inter-asset |
| Line ends | Slightly irregular, hand-wobbled | wobble jitter 1.6 px |
| Corners | Rounded or overshoot, never machine-perfect mitres | — |
| Outline coverage | Every filled shape has an ink outline | 100% of shapes |

**Measurable test for hand-drawn vs flat:** rasterise to greyscale and compute a
laplacian variance (edge-texture energy) on a 2000 px-wide normalised canvas.
Flat vector/programmatic lines produce a near-binary histogram and low texture
energy; scanned hand-drawn ink produces a non-zero noise floor from paper and
medium texture. Report the number; do not eyeball it.

## 5. Texture and paper
- Faint dot grid, 34 px pitch, `#E2E4E0` (paper texture only - must not read as a
  pattern at 100% zoom).
- No drop shadows, no gradients, no glows, no 3D.

## 6. Typography
| Element | Size | Weight | Placement |
|---|---|---|---|
| Caption | 34 px | Bold sans | Centred, baseline y=806 |
| Brand mark | 52 px | Bold sans | Top-left, x=44, y=52 |
| Sub-label | 26 px | Bold sans | Top-left, x=46, y=116 |
| Footer mark | 19 px | Regular | Bottom-right |

## 7. Composition rules
- Single subject, centred, occupying 55–65% of canvas height.
- Caption band at the bottom, never overlapping the subject's eyes.
- One focal accent colour per panel.
- No multi-panel, no speech bubbles (captions only).
- **Zero LPT / real-estate subject matter. Hard fail, no exceptions.**

## 8. Provenance tags (three classes — the two-class model was a defect)
| Tag | Definition | Acceptable evidence |
|---|---|---|
| `traditional` | Human hand-drew it | Paper original scan/photo with EXIF (device + timestamp) or layered source / timelapse |
| `ai` | A third-party **doodle-maker vendor product** generated it | Vendor export + vendor job/generation ID + timestamp |
| `programmatic` | Deterministic in-house code rendered it (this repo) | Job-log line in `tools/doodle_maker/joblog.jsonl` (timestamp, seed, template sha256, output sha256) plus the output file |

**Why the third class exists:** a PIL-rendered PNG is neither hand-drawn nor a
vendor AI output. Tagging it `traditional` is fraud; tagging it `ai` is a false
vendor claim. Under a two-class model every code-rendered asset is untaggable and
therefore, by rule, a FAIL — which is a taxonomy defect, not an asset defect.
Meta's 6/6 mix gate should be re-based as: 6 `traditional` + 6 of (`ai` | `programmatic`),
with the count per class printed explicitly.

## 9. Measured comparison — status
Rev 1 exists as of 2026-09-12T05:40:00Z. **No asset has yet been measured against
it.** The divergence log is therefore empty because no measurement has run, not
because the set is clean. First measurement target: `content/milkups/art/doodles/programmatic/`.
