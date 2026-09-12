# EVIDENCE STANDARD — Z-Dot LLC ("BOT MODE RULE")
Owner: NinjaNerd (CTO) · Effective: 2026-09-12 · Status: BINDING
Source of authority: Company goal task `086aba757014` (PM WORKSTREAM), deliverable 2.

## 1. THE RULE
**No task may be marked `done` without evidence.** A completion report that is a summary,
description, or statement of intention is NOT evidence and MUST be rejected and sent back
to the owner.

## 2. THE LESSON THIS COMES FROM (verified, not folklore)
Original failure: task `78d96aea9a70` — "BUILD TASK — Implement Bot Mode on advance.html".
Final DB state: `status = done`, `result = "No result produced."` (19 characters).
Five agents built a chain of "done" reports with **zero code existing**.
Verified 2026-09-12 against `.agent-company-ai/default/company.db` → `tasks` table.

## 3. THE FIVE-PART EVIDENCE BAR (all five required)
A post / asset / deliverable only counts as DONE when ALL of the following exist:

| # | Required field | Example |
|---|---|---|
| a | **Live public URL** | `https://snowsnakes.zerric.xyz/songs/11` |
| b | **Timestamp** (UTC, from the action not the report) | `2026-09-12T04:48:59.619Z` |
| c | **Draft ID or asset file path** | `draft_id=71` or `/abs/path/render.wav` |
| d | **Platform + account handle** | `twitter / @snowsnakes` |
| e | **Screenshot or saved capture** | `evidence/verify/<name>_<UTC>.png` |

Partial evidence = NOT done. "It works on my machine" = NOT done.

## 4. DEFINITION OF "POSTED"
`posted` requires a real `published_id` on the platform, a live URL resolvable by a third
party, and a saved capture. For our DB, `social_drafts.published_id` must be non-empty and
`status` must flip from `draft`. Currently: 99/99 drafts are `draft`, `published_id` empty.

## 5. VERIFICATION METHOD (how we actually check)
- Public SnowSnakes content: `GET https://snowsnakes.zerric.xyz/api/<resource>` (JSON, no auth).
- JS-only / React SPA pages: headless Chromium via Playwright (`venv/bin/python`, playwright 1.62.0).
- Screenshots land in `evidence/verify/`.
- Anti-bot note: browser User-Agents get HTTP 429 from Hostinger hcdn on some paths; the
  Playwright real-browser path and the JSON API both work. Plain-curl browser UA spoofing does not.

## 6. ENFORCEMENT
Any teammate reporting "done" without the five-part bar is sent back with the missing field
named explicitly. Do not accept a summary as a substitute. This rule is enforced by the PM
track (Meta + Manny) and is cited in `TEAM-STATE.md` §"SnowSnakes Engagement Activation".
