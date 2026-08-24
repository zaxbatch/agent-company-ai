# "Spread Da Word" — Free/Cheap Quality Animation Options
Owner: NinjaNerd (CTO) · Date: 2026-08-24 · Status: BRAINSTORM — BossLady to pick direction

## Context
Spread Da Word = an ANIMATED SERIES to feature on snowsnakes.zerric.xyz.
Goal: quality look, free/cheap, web-native (React SPA), on-brand with the 8-bit fun vibe.

## Options (best → pragmatic)

### 1. Code-driven pixel-art animation (canvas) — $0, we build it
- We already do this (Food Truck Frenzy, Snow Snake are canvas games).
- Episodes = animated canvas scenes (characters move, talk via text boxes, 8-bit style).
- Pros: 100% free, on-brand (matches site DNA), interactive possible, no licensing, infinite episodes.
- Cons: needs art/design effort from us; stylized (not "realistic" animation).

### 2. Lottie — $0, huge free library
- LottieFiles has thousands of high-quality vector animations, free to use.
- Tiny JSON files, buttery smooth, scale perfectly, web-native.
- Pros: instant quality for character loops, intros, transitions; no code beyond embedding.
- Cons: library animations may not be unique; custom ones need After Effects (paid) or an animator.

### 3. Rive — $0 tier, interactive character animation
- Free tier; web runtime; state machines (characters can react to clicks/keyboard).
- Pros: interactive characters ("talking head" style episodes), great for a series.
- Cons: learning curve; free tier limits.

### 4. AI video (cheap/free credits) — cinematic clips
- Kling AI, Hailuo/MiniMax (free credits), Pika (free tier), Runway (paid, best quality).
- Generate short cinematic clips from prompts; stitch into episodes.
- Pros: looks impressive, fast, no drawing skill needed.
- Cons: quality varies, free credits run out, may not match 8-bit brand unless styled.

### 5. Classic 2D tools (free) — hand-drawn
- Pencil2D, OpenToonz (Ghibli-grade, free), Synfig (vector).
- Pros: real animation, unique look. Cons: slow, needs talent/time.

### 6. Motion graphics (free) — DaVinci Resolve / Blender
- Resolve's Fusion = free motion graphics; Blender = free 3D.
- Pros: pro-grade. Cons: steep learning curve, heavy.

## CTO recommendation
- **Phase 1 (now): Lottie + code-driven canvas.** Free, web-native, on-brand. Build the series as animated canvas episodes with Lottie for smooth intro/outro/transitions.
- **Phase 2 (later): AI video clips (Kling/Hailuo free credits)** for cinematic moments / episode teasers.
- Skip heavy 2D/3D for now — slow and expensive; revisit if the series takes off.

## Next step
BossLady picks the vibe: (a) pure 8-bit pixel episodes (fully ours, zero cost), (b) smooth vector (Lottie), or (c) cinematic AI clips. Then we build a 1-2 min pilot episode.
