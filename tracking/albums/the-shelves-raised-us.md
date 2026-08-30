# Tracker — "The Shelves Raised Us" by milkup (Retro 80s / Synthwave, 8 tracks ≥60s)
Owner: Meta (PM, QA & Delivery) · Updated 2026-08-24 · Cycle 3 (production execution; supersedes cycle 2 initial tracking)
## Milestones
| ID | Milestone | Owner | Status | Due | Depends on | Acceptance criteria |
| M1 | Audio production (8 masters) | CTO | IN PROGRESS | 2026-08-26 17:00 | — | 8 files on disk, ≥60s each, retro 80s/synthwave mix |
| M2 | Cover art | Marketer | IN PROGRESS | 2026-08-26 17:00 | — | 3000×3000, RGB, JPG/PNG, <20MB |
| M3 | QA gate | Meta | PENDING | 2026-08-27 17:00 | M1+M2 | All 6 QA checks pass, sign-off issued |
| M4 | Distribution upload | Sales | PENDING | 2026-08-28 | M3 sign-off + M2 art | Submitted to distributor, correct metadata, ISRC/UPC allocated |
| M5 | Launch | Marketer | PENDING | 2026-09-11 | M4 + pre-save links live | Release live on stores, pre-save campaign active |
## QA gate (release gate — nothing ships without Meta sign-off)
1. Exactly 8 tracks exist
2. Artist="milkup", album="The Shelves Raised Us" (metadata tags + distributor form)
3. Every track ≥60s (ffprobe on actual files — no claims)
4. Genre retro 80s / synthwave (metadata + listening spot-check)
5. Cover art 3000×3000, RGB, JPG/PNG, <20MB
6. Distributor upload complete with correct metadata [Sales evidence]
## QA gate log (per track)
Status: PENDING — no master files verified yet. Evidence dispatch: cto 0688ba058a00, developer/ffprobe a2bee5a9ef8f, marketer 528647c0e8e9, sales 7fc4d11049d6. Per-track durations to be logged within 24h of M1 delivery; no track marked pass/fail without ffprobe output.
## Release calendar (LOCKED: Fri 2026-09-11)
- 08-26: M1 masters + M2 art due
- 08-27: M3 QA gate closes (24h) → sign-off
- 08-28: M4 distributor submission (audio+art+metadata bundle)
- 09-04: pre-save links live (D-7)
- 09-10: D-1 final link + metadata check
- 09-11: M5 launch + promo push
## Risks
- R1 CTO delivery slip (critical path, zero slack) → progressive QA on first 2 tracks
- R2 Cover art rejection → pre-validate with identify
- R3 Track <60s → CTO extends/loops before master
- R4 Metadata mismatch → single metadata sheet as source of truth
- R5 ISRC/UPC late → Sales requests at upload time
- R6 Distributor approval delay → submit ≥2 weeks before locked date (done)
