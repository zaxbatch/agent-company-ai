# Spread Da Word — Animation Style Vote Tally

Date: 2026-08-24
Context: BossLady asked for a quick vote on the best animation approach for the
Spread Da Word animated series on snowsnakes.

## Options considered
1. Rive — free, browser-native vector cutout animation (best for South Park style)
2. Wick Editor / Synfig / Pencil2D — free 2D tools, steeper learning curve
3. Canvas motion-comic — animated panels, zero cost, on-brand 8-bit
4. AI video (Runway/Hedra free tiers) — occasional cinematic shots
5. Blender Grease Pencil — free, powerful, biggest time sink

## Votes
- ClickClack (dev): **Rive** — free, flat-shape cutout, plays natively in browser, no video files, fast iteration
- BossLady/Zerric: "Animation like South Park will work" — **cutout style** (flat shapes, simple joints)

## Result
**South Park-style cutout animation using Rive.** Flat vector characters with
simple joints, rendered in-browser on snowsnakes. Episodes are Rive files
embedded in the episodes feature (no render farm, no video hosting, free).

## Next
- Build character rig 1 (SVG cutout rig, Rive-ready) — DONE below
- Build episode 1 proof of concept
