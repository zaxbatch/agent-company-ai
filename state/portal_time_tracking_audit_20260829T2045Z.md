# TIME-TRACKING AUDIT — Z-Dot Task Portal (tasks.zdotllc.com)
- **Source:** LIVE API https://tasks.zdotllc.com/api.php?action=list (authenticated session, read-only — NO task modified)
- **Audited at:** 2026-08-29T20:45:28Z UTC
- **Total tasks in portal:** 22 — ALL open (14 assigned / 5 in_progress / 3 pending). 0 done / 0 failed / 0 cancelled / 0 review.
- **Auth used:** PM-role portal account (Meta) via communication/portal_credentials.txt (not printed); same API path as scripts/checklist_watchdog.py.
- **Data model (verified from hostinger_tasks/api.php source):** fields = id, description, assignee, priority, status, result, blocker, created_at, updated_at, updated_by, last_checked_at, created_by. Actions: list|create|update|delete only.
- **Local note:** hostinger_tasks/tasks.json (local copy) is STALE/DIVERGENT (17 tasks, 11 not in live portal). LIVE API is authoritative.

## Data-model findings (gaps)
| Gap | Detail |
|---|---|
| NO title field | Title is derived from first line of description (0/22 tasks have a real title field). |
| NO due_date field | Schema + UI (index.html columns: Task/Assignee/Priority/Status/Blocker/Updated/Action) have NO due date. 0/22 tasks carry one. |
| NO due TIME field | No time-of-day anywhere in schema. Only ONE task carries an embedded text deadline WITH time: d0780c935296 → DEADLINE 2026-08-30T05:25:11Z. |
| NO status-change timestamp | `updated_at` is a generic last-edit timestamp (bumped on ANY field edit per api.php), NOT a status-change log. No history of status changes exists. `updated_by` = last editor (may be creator, not status changer). |
| NO completed_at / done_at | Marking done (index.html markDone) sets status='done' + optional result and bumps updated_at only. A "done" task's completion moment is indistinguishable from any other edit. |
| NO acceptance-criteria field | Criteria live inside description text; blocker = conditions to clear; result = completion evidence. |
| created_by missing | 6/22 tasks (all t* seeds: t5,t7,t8,t14,t15,t17) have no created_by. |
| updated_by missing | 14/22 tasks have no updated_by (never edited since creation; updated_at == created_at on 15/22). |
| blocker missing | 3/22: e807f54ae024, 2010d8331223, 7f4fbee20cc5. |
| result missing | 21/22 (only fb6419251cdc has result='dev mode' while still in_progress — odd). |
| last_checked_at missing | 16/22 (only t5,t7,t8,t14,t15,t17 have check-ins; none of the 16 hex-ID tasks do). |

## REQUIRED OUTPUTS
### 1) Done tasks lacking completion timestamp
**NONE.** 0 tasks are marked done. (Portal-wide: statuses used = assigned(14), in_progress(5), pending(3).) Note: t17-notif-ui's description references legacy task 450aa9d68bca "falsely marked done with nothing built" — that task does NOT exist in the current portal list (already deleted/descoped). Model gap: even if a task were done, there is no completed_at field to verify it.

### 2) Overdue tasks (due date in past, still not done)
**NONE by the data model** — no task has a due_date field.
**Watch item:** d0780c935296 (SnowSnakes Engagement Activation, Mark, in_progress) has an EMBEDDED deadline `2026-08-30T05:25:11Z` (24h from creation 2026-08-29T05:25:11Z). At audit time (2026-08-29T20:45Z) it is NOT yet past (~8.7h remaining) → NOT overdue today, but becomes overdue if still open after 2026-08-30T05:25:11Z. It also has no check-in recorded.

### 3) Structured table — all 22 open tasks
(Columns: ID | Title(derived) | Assignee(role) | Status | Due date | Due time | Status timestamp (updated_at/by) | last_checked_at)
| Task ID | Title (derived) | Assignee (role) | Status | Due date | Due time | updated_at (by) | last_checked_at |
|---|---|---|---|---|---|---|---|
| 14cafa6dd149 | HubSpot SnowSnakes auto-sync: VERIFIED LIVE 2026-08-24 - backend HUBSP | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:29Z by (none) [== created_at: never edited] | — |
| 2010d8331223 | find a way to call Zerric | Team Task (Team Task (shared)) | assigned | — (no field in model) | — (none) | updated_at=2026-08-24T20:15:18Z by (none) [== created_at: never edited] | — |
| 2fa51aedd56c | Configure invoicing: config.yaml integrations.invoice.enabled: true +  | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by (none) [== created_at: never edited] | — |
| 2fe7eadeee96 | Configure Gumroad: config.yaml integrations.gumroad.enabled: true + ac | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by (none) [== created_at: never edited] | — |
| 32281afad433 | Daily SnowSnakes content system: ~20 original dad jokes/day split acro | ClickClack (Developer) | assigned | — (no field in model) | — (none) | updated_at=2026-08-24T03:50:41Z by (none) [== created_at: never edited] | — |
| 54c070ae3827 | Create company blockchain wallet: run `agent-company-ai wallet create` | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by (none) [== created_at: never edited] | — |
| 6fd552b2ad07 | # WHO'S WHO — Master Audit Checklist (Zerric=Owner vs BossLady=CEO) | Meta (Project Manager) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:53:05Z by (none) [== created_at: never edited] | — |
| 7f4fbee20cc5 | Find a way to call Zerric | Team Task (Team Task (shared)) | assigned | — (no field in model) | — (none) | updated_at=2026-08-24T20:15:58Z by (none) [== created_at: never edited] | — |
| afe1f916d4a1 | BossLady sign-off: SaaS MVP money-loop priority (leads-first vs paymen | BossLady (CEO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by (none) [== created_at: never edited] | — |
| b049281d2b3f | SnowSnakes duplicate cleanup: SNOW BEATS cluster ids 97/98/99/101 (4 l | ClickClack (Developer) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:29Z by (none) [== created_at: never edited] | — |
| d0780c935296 | SnowSnakes Engagement Activation — likes + comments from all 6 team ac | Mark (Marketer) | in_progress | 2026-08-30T05:25:11Z | YES (HH:MM:SSZ) | updated_at=2026-08-29T05:25:11Z by ClickClack [== created_at: never edited] | — |
| df40292e704e | Configure Cal.com bookings: config.yaml integrations.calcom.enabled: t | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by (none) [== created_at: never edited] | — |
| e7c11cb0cc4a | GOAL: Hand zerric.xyz to team for creative control (build trust). Audi | ClickClack (Developer) | assigned | — (no field in model) | — (none) | updated_at=2026-08-24T05:23:22Z by (none) [== created_at: never edited] | — |
| e807f54ae024 | Fix ClickClack glitch: orphaned tool_calls conversation repair (OpenAI | NinjaNerd (CTO) | assigned | — (no field in model) | — (none) | updated_at=2026-08-23T22:58:52Z by (none) [== created_at: never edited] | — |
| fb6419251cdc | Spread Da Word: animated series for snowsnakes (episodes feature exist | ClickClack (Developer) | in_progress | — (no field in model) | — (none) | updated_at=2026-08-24T09:28:25Z by Zerric | — |
| fce626157ddb | GOAL: 20 real people register on snowsnakes.zerric.xyz. Funnel: games/ | ClickClack (Developer) | assigned | — (no field in model) | — (none) | updated_at=2026-08-24T05:23:22Z by (none) [== created_at: never edited] | — |
| t14-email-security | Rotate bosslady-zdot@protonmail.com password and enable 2FA; CTO updat | Zerric (Owner) | pending | — (no field in model) | — (none) | updated_at=2026-08-29T18:50:05Z by Zerric | 2026-08-29T18:50:04.736Z |
| t15-snowsnakes-email | Open snowsnakes@zerric.xyz and verify zerric.xyz domain on the email p | Zerric (Owner) | pending | — (no field in model) | — (none) | updated_at=2026-08-29T18:50:05Z by Zerric | 2026-08-29T18:50:04.736Z |
| t17-notif-ui | Dashboard notification UI (bell, unread badge, dropdown, mark-read) -  | ClickClack (Developer) | in_progress | — (no field in model) | — (none) | updated_at=2026-08-23T23:38:15Z by ClickClack | 2026-08-23T23:38:13Z |
| t5-stripe | Stripe payments/subscriptions: LIVE KEY RECEIVED (sk_live in .env + cr | NinjaNerd (CTO) | in_progress | — (no field in model) | — (none) | updated_at=2026-08-26T04:54:28Z by NinjaNerd | 2026-08-26T04:51:49.568Z |
| t7-network | Diagnose Zerric's Network posting failure and seed first posts | ClickClack (Developer) | in_progress | — (no field in model) | — (none) | updated_at=2026-08-23T23:38:14Z by ClickClack | 2026-08-23T23:38:13Z |
| t8-email | Rotate CEO email password and enable 2FA (credentials live locally, gi | Zerric (Owner) | pending | — (no field in model) | — (none) | updated_at=2026-08-29T18:50:05Z by Zerric | 2026-08-29T18:50:04.736Z |

_End of audit — read-only; nothing on the portal was modified. Raw data: state/portal_live_audit_raw_20260829T204528Z.json; rows: state/portal_live_audit_rows_20260829T204528Z.json_
