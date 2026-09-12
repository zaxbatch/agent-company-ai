---
template_id: doodle-prompt-v1
revision: 1
created_utc: 2026-09-12T05:40:00Z
owner: NinjaNerd (CTO)
vendor: UNASSIGNED
canvas: 700x900
paper: "#FDFCF7"
ink: "#24344A"
body: "#DFF2FF"
accent: "#E24A4A"
snow: "#78BEF0"
caption: TOO COLD TO STOP
tag: 128 BPM
brand: SNOW BEATS
stamp: SPICY
footer: Z-DOT
line_weight_px: 4
palette_lock: true
---

# Doodle prompt template v1 (vendor-neutral)

## What this file is
One file, two consumers:

1. **Programmatic render (works today, no vendor needed).**
   `venv/bin/python tools/doodle_maker/doodle_maker.py --template content/milkups/art/doodles/_templates/doodle-prompt-v1.md --seed 128 --out content/milkups/art/doodles/programmatic --tag programmatic`
   Front-matter fields above drive a deterministic PNG render. Output is tagged
   **programmatic** - never "ai", never "traditional".

2. **Vendor image-model prompt (BLOCKED - no seat exists).**
   When a doodle-maker vendor is selected and a real `@zdotllc.com` seat exists,
   the PROMPT BODY below is sent verbatim (with `{placeholders}` filled) to that
   vendor. Do not use this path until `vendor:` above names a real product and a
   seat is registered - see the licence memo for why that ordering is mandatory.

## PROMPT BODY (slot-filled; {placeholders} are the only things that change)
> A single-panel cartoon doodle on off-white paper (#FDFCF7), thick hand-wobbled
> ink outlines (#24344A) about {line_weight_px}px, flat spot colour only, no gradients,
> no photorealism, no 3D. Subject: {subject}. Composition: {composition}.
> Palette locked to {palette_hex_list}. Sparse texture: faint dot grid, slightly
> irregular line ends, visible construction wobble. Empty margin of ~40px on all
> sides. Caption text rendered in bold sans-serif, centred, reading "{caption}".
> Character must match the Z-Dot character bible (proportions, eye style, mouth
> style). No text other than the caption, the {tag} label and the {footer} mark.
> Do not render watermarks, logos, signatures, or third-party characters.
> Negative: gradients, airbrush, lens flare, photorealism, extra limbs, garbled text,
> real brand marks, real people, LPT/real-estate subject matter (hard block).

## Slot values (v1 demo sheet)
- subject: SnowSnakes mascot, headphones on, coiled tail, cold-weather gear
- composition: centred figure, mid-frame, 60% of canvas height, caption band at bottom
- palette_hex_list: #FDFCF7, #24344A, #DFF2FF, #E24A4A, #78BEF0
- line_weight_px: 4

## Hard constraints (both paths)
- **Zero LPT / real-estate content.** Ever. Hard fail on sight.
- Palette lock: any hue outside the list above is a reportable divergence, not a retouch.
- One doodle = one caption. No multi-panel.
- Provenance tag is mandatory on every output. Untagged = incomplete = not shipped.
