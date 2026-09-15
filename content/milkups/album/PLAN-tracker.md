# MilkUps Album — PLAN / DEPENDENCY TRACKER (Cycle 3)

**Artifact:** `content/milkups/album/PLAN-tracker.md`
**R7 owner:** Manny (PM). Prepared with Meta (PM — QA & Delivery).
**Scope:** coordination artifact only. No album content, renders, or audio touched.
**State file of record:** `TEAM-STATE.md`
**Status legend:** DONE = artifact exists at the stated path AND sha256 recorded · IN FLIGHT = owner active, no artifact yet · BLOCKED = named unresolved external dependency · TODO = not started
**Hard rule:** a task is never DONE because someone said so. DONE = path + hash + (for audio) duration/silence check.

## 0. Delivery goal — honest status
**Goal:** "make a tracker/LMMS album for MilkUps"
**Status at cycle 3:** **NOT ACHIEVED.** 0 of 7 R-tasks closed with a verified artifact at time of writing. No acceptance-criteria item is ticked.

## 1. R-TASK REGISTER — Cycle 3

| ID | Task | Owner | Deliverable path | Status | Depends on | Deadline |
|----|------|-------|------------------|--------|-----------|----------|
| R1 | LMMS projects + renders | NinjaNerd (CTO) | `content/milkups/album/lmms/trk01-05.mmp`; `content/milkups/album/renders/lmms/trk01-05.wav` | IN FLIGHT — no artifact verified | — (entry point) | CYCLE 3 CLOSE (hard stop EOD) |
| R2 | .xm modules + renders | ClickClack (Developer) | `content/milkups/album/xm/trk01-05.xm`; `content/milkups/album/renders/xm/trk01-05.wav` | BLOCKED (soft) — needs R1 track table (master tempo + 5 track titles) | R1 track table | CYCLE 3 CLOSE |
| R3 | QA verdict | Meta (PM — QA) | `content/milkups/album/QA-verdict-cycle3.md` | BLOCKED — zero raw evidence submitted from R1/R2 | R1 + R2 raw evidence | CYCLE 3 CLOSE |
| R4 | GTM plan | Mark (Marketer) | `content/milkups/album/GTM-plan.md` | IN FLIGHT (independent) | — (input: BossLady creative direction) | CYCLE 3 CLOSE |
| R5 | Monetization | Seleena (Sales) | `content/milkups/album/MONETIZATION.md` | IN FLIGHT (independent); price/link leg BLOCKED on Stripe keys | — (external: Stripe keys) | CYCLE 3 CLOSE |
| R6 | Budget | Finance | `content/milkups/album/BUDGET.md` | IN FLIGHT (independent) | — | CYCLE 3 CLOSE |
| R7 | Dependency tracker + state sync | Manny (PM) | `content/milkups/album/PLAN-tracker.md` + `TEAM-STATE.md` state block | IN FLIGHT — this artifact is the tracker leg; state sync lands in the same commit | R1-R6 statuses (for honesty) | CYCLE 3 CLOSE |

Deadline note: "cycle 3 close" is the only deadline available; there is no absolute timestamp in the cycle definition. See risk R-4. Until BossLady confirms a wall-clock close, use EOD of the current working day as the hard stop.

## 2. DEPENDENCY GRAPH

```
                     +------------------------------+
                     | R1  LMMS .mmp x5 + renders x5|  (NinjaNerd)
                     +--------------+---------------+
      track table (tempo + 5 titles) |
                     +--------------v---------------+
                     | R2  .xm x5 + renders x5     |  (ClickClack)
                     +--------------+---------------+
   raw evidence (files, durations,   |
   hashes, silence check)            |
                     +--------------v---------------+
                     | R3  QA VERDICT              |  (Meta)
                     +--------------+---------------+
                                    |
                     +--------------v---------------+
                     | RELEASE GREEN-LIGHT         |  (Zerric - editor)
                     +--------------+---------------+

 OFF CRITICAL PATH (feed the release package, do not gate the build):
   R4 GTM plan (Mark) --------+
   R5 Monetization (Seleena) --+--> release package
   R6 Budget (Finance) -------+
   note: R5's price/link leg is blocked on Stripe keys (external).

 R7 tracker depends on ALL: R7 <-- R1 R2 R3 R4 R5 R6 (status truth)
```

## 3. CRITICAL PATH (highlighted)

**CRITICAL PATH: R1 (LMMS projects + renders) -> R2 (.xm modules + renders) -> R3 (QA verdict) -> release green-light (Zerric).**

- The only true build chain. Nothing can start on R2 until R1's track table exists; nothing in R3 can be verified until R1+R2 raw evidence is in hand.
- **R2 is the schedule trap:** it is both a dependency of R3 and dependent on R1. If R1 slips, R2 slips 1:1. Recommend R1 publish the track table (tempo + titles) as a standalone file the moment all 5 titles are locked, before rendering finishes.
- **R3 is a gate, not a formality.** No verdict is issued on absence of evidence. Missing evidence = verdict `BLOCKED-INSUFFICIENT-EVIDENCE`.
- R4/R5/R6 can and should complete in parallel; they do not gate the critical path but they do gate a release, so they must land before green-light consumption.
- Slack: zero on the critical path this cycle. Any R1 slip is a critical-path slip, no absorption available.

## 4. ACCEPTANCE CRITERIA CHECKLIST (all unticked at cycle 3)

| # | Criterion | How it is verified (evidence required) | State |
|---|-----------|----------------------------------------|-------|
| AC-1 | 5 x `.mmp` valid | Opens/parses in LMMS; root XML node `<lmms-project>`; only built-in instruments referenced (no missing sample paths) | [ ] |
| AC-2 | 5 x `.xm` valid magic | Byte 0..16 == `Extended Module: ` (17 bytes) and byte 37 == `0x1A`. Secondary spec checks must be confirmed against the actual loader used in R2 before ticking: version word at offset 58 == `0x0104`, header size at offset 60 == `276`. | [ ] |
| AC-3 | 10 non-silent renders >= 90 s | 5 LMMS renders + 5 `.xm` renders; each >= 90.0 s wall duration AND non-silent (peak > -60 dBFS / non-zero RMS). Silence-check logs captured. | [ ] |
| AC-4 | README present | Track list (5 titles), credits (owners), tooling versions, exact rebuild steps | [ ] |
| AC-5 | sha256 manifest | Manifest covering 5 `.mmp` + 5 `.xm` + 10 renders + README; hashes recomputed at QA time, not copied from the claimant | [ ] |

Tick rule: a box is ticked only when the verifying evidence is attached (path + hash, or log output). "Built and tested" is not evidence. A late-blocked task reported on time is a success; an unverifiable DONE is a failure.

## 5. LOCKED SCOPE (do not silently change)

**5 tracks · each >= 90 s · built-in instruments only · no external samples.**
- Any scope change (track count, duration floor, instrument/sample policy, format, timeline) goes to **BossLady** — CREATIVE DIRECTOR, with Zerric's approval to green-light MilkUps decisions; Zerric remains EDITOR (reviews and fine-tunes what we produce). Mark takes all MilkUps decisions from BossLady.
- Scope changes are recorded in this file as a change ticket with a date and an owner — never absorbed silently into a task.
- Standing prohibition: no LPT-adjacent branding or LPT real-estate content in MilkUps assets. That category always requires Zerric's approval.

## 6. BLOCKERS & RISKS

| ID | Blocker / risk | Owner | Impact | Mitigation / ask |
|----|----------------|-------|--------|------------------|
| B-1 | Stripe keys not issued | Seleena -> Zerric | R5 price/link leg cannot be real; monetization stays theoretical | Escalation E-2 |
| B-2 | HubSpot sync not wired | NinjaNerd -> Zerric | Album launch leads/registrations don't land in CRM | Escalation E-3 |
| B-3 | File-access limits on some agents | Manny | Claimed artifacts cannot always be verified by QA, producing unverifiable DONE | Require sha256 + wc -c in every handoff; PM verifies what is reachable and escalates the rest |
| R-1 | R2 blocked behind R1 with zero slack | NinjaNerd | Critical-path slip | Publish R1 track table early |
| R-2 | 3-cycle pattern: DONE with no artifact | all | False progress, timeouts | DONE = path + hash rule, enforced at R3 |
| R-3 | Renders under 90 s or silent | ClickClack / NinjaNerd | AC-3 fail, rework | Check duration/silence at render time, not at QA |
| R-4 | No absolute cycle-3 close timestamp | BossLady | Unbounded deadline = the exact timeout pattern | Confirm cycle-3 close date |
| R-5 | Path/dir drift between owners | Manny | Evidence paths break | Canonical layout fixed in section 1; PM creates dirs |

## 7. PROCESS FIX — the written lesson (3 cycles, same pattern)

**Lesson: a task marked DONE without an artifact path is not DONE. It is an unverified claim, and it costs a full cycle to discover.** Two failure modes repeated for three cycles: (1) status inflation as work neared deadline; (2) tasks scoped without a bound timing out and being re-declared next cycle.

Fixes adopted this cycle:
1. Every R-task names its artifact path and acceptance criteria before work starts.
2. DONE requires path + sha256 (+ duration/silence for audio). Nothing else counts.
3. Any R-task without an artifact at the hard stop is marked FAILED and re-scoped smaller next cycle — not re-declared as in-flight.
4. QA (R3) is a gate that can and will return `BLOCKED-INSUFFICIENT-EVIDENCE`; absence of evidence is a verdict, not a delay.

## 8. ESCALATION LIST — Zerric (only what genuinely needs him)

| # | Item | Why it needs Zerric | Exact ask |
|---|------|---------------------|-----------|
| E-1 | Release green-light | He is EDITOR — final review/fine-tune of what we produce; only he can green-light release | Confirm the 5-track MilkUps album can go out once R3 verdict is PASS, or list required edits |
| E-2 | Stripe keys | Credentials only he can issue; R5's price/payment link cannot be real without them | Provision MilkUps Stripe keys, or confirm "no payment leg this cycle" so R5 scopes to non-payment monetization |
| E-3 | HubSpot sync | Cross-account integration decision + access | One-liner: approve wiring MilkUps registrations/leads into HubSpot CRM (yes/no) |
| E-4 | LPT-adjacent branding | LPT always requires his approval; Z-Dot/LPT/personal branding must not mix | Confirm no LPT reference in MilkUps album/GTM assets. Current plan: none. Flag if you want otherwise |

Not escalated (we own these): R1/R2 build, R3 QA gate, R4 GTM, R6 budget, R7 tracking, deadline hygiene, file-layout discipline.

## 9. R7 STATE SYNC — exact block merged into TEAM-STATE.md

<!-- MILKUPS-ALBUM-STATE:START (R7 / cycle 3 — Manny + Meta) -->
## MilkUps Album (tracker/LMMS) — cycle 3 sync
- Goal: "make a tracker/LMMS album for MilkUps" -> STATUS: **NOT ACHIEVED (cycle 3)**.
- In flight: R1 LMMS .mmp + renders (NinjaNerd) · R2 .xm + renders (ClickClack) · R3 QA verdict (Meta) · R4 GTM (Mark) · R5 monetization (Seleena) · R6 budget (Finance) · R7 tracker + state sync (Manny).
- Critical path: R1 -> R2 -> R3 -> release green-light (Zerric).
- Verdict file: `content/milkups/album/QA-verdict-cycle3.md` (R3 — BLOCKED: no raw evidence submitted from R1/R2).
- Tracker: `content/milkups/album/PLAN-tracker.md`.
- Blockers: (1) Stripe keys — R5 payment leg; (2) HubSpot sync not wired — launch leads don't reach CRM; (3) file-access limits on some agents — claimed artifacts not always verifiable, so DONE must carry sha256 + wc -c.
- Scope LOCKED: 5 tracks, >= 90 s each, built-in instruments only, no external samples; changes via BossLady only.
- Deadline: cycle 3 close (hard stop). Absolute timestamp unconfirmed — flagged to BossLady.
<!-- MILKUPS-ALBUM-STATE:END -->
