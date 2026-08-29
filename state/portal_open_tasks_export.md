# Z-Dot Task Portal — Open Task Extraction (READ-ONLY)

- **Source:** https://tasks.zdotllc.com/api.php?action=list (live API, authenticated session)
- **Fetched at:** 2026-08-29T05:23:53Z UTC
- **Total tasks in portal:** 21 — ALL are open (14 assigned / 4 in_progress / 3 pending); 0 done/failed/cancelled
- **Auth used:** PM-role portal account (Meta) — no credentials committed; read-only; NO task statuses modified

## Field availability notes (IMPORTANT)
- **Title:** portal has no separate title field → derived from first line of `description` (marked below).
- **Due date:** portal data model has **no due_date field** → `due_date: null` for every task.
- **Acceptance criteria:** no explicit field; criteria are embedded in `description`; `blocker` = conditions to clear; `result` = completion evidence (all null for open tasks).

## 1. t5-stripe — Stripe payments/subscriptions: LIVE KEY RECEIVED

| Field | Value |
|---|---|
| **ID** | `t5-stripe` |
| **Title** (derived) | Stripe payments/subscriptions: LIVE KEY RECEIVED |
| **Status** | in_progress |
| **Assignee** | NinjaNerd |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T14:00:00Z |
| **Updated** | 2026-08-26T04:54:28Z (by NinjaNerd) |
| **Last checked** | 2026-08-26T04:51:49.568Z |

**Description:**

```
Stripe payments/subscriptions: LIVE KEY RECEIVED (sk_live in .env + credentials.txt, verified via balance API 2026-08-26 livemode). NEXT (CTO): 1) config.yaml integrations.stripe.enabled: true 2) api_key: ${STRIPE_SECRET_KEY} 3) add STRIPE_WEBHOOK_SECRET to .env 4) test payment link (stripe_tools) + subscription link (stripe_subs). Product 'Linux Ghost - Barebones' exists (prod_V8SXbzJ0M1SaAF, $0.00 one-time - set real price).
```

**Blocker / conditions:** STRIPE_WEBHOOK_SECRET needed from Zerric's Stripe dashboard (key itself already in .env).

**Completion evidence (result field):** None (open task)

---

## 2. t7-network — Diagnose Zerric's Network posting failure and seed first posts

| Field | Value |
|---|---|
| **ID** | `t7-network` |
| **Title** (derived) | Diagnose Zerric's Network posting failure and seed first posts |
| **Status** | in_progress |
| **Assignee** | ClickClack |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T14:00:00Z |
| **Updated** | 2026-08-23T23:38:14Z (by ClickClack) |
| **Last checked** | 2026-08-23T23:38:13Z |

**Description:**

```
Diagnose Zerric's Network posting failure and seed first posts
```

**Blocker / conditions:** Diagnosis started 2026-08-23; needs Zerric's go-ahead before publishing bot content publicly

**Completion evidence (result field):** None (open task)

---

## 3. t8-email — Rotate CEO email password and enable 2FA

| Field | Value |
|---|---|
| **ID** | `t8-email` |
| **Title** (derived) | Rotate CEO email password and enable 2FA |
| **Status** | pending |
| **Assignee** | Zerric |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T14:00:00Z |
| **Updated** | 2026-08-26T06:42:37Z (by Zerric) |
| **Last checked** | 2026-08-26T06:42:37.316Z |

**Description:**

```
Rotate CEO email password and enable 2FA (credentials live locally, git-ignored at mode 600)
```

**Blocker / conditions:** Zerric action: rotate CEO email password and enable 2FA

**Completion evidence (result field):** None (open task)

---

## 4. t14-email-security — Rotate bosslady-zdot@protonmail.com password and enable 2FA; CTO updates local credenti...

| Field | Value |
|---|---|
| **ID** | `t14-email-security` |
| **Title** (derived) | Rotate bosslady-zdot@protonmail.com password and enable 2FA; CTO updates local credenti... |
| **Status** | pending |
| **Assignee** | Zerric |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T15:00:00Z |
| **Updated** | 2026-08-26T06:42:37Z (by Zerric) |
| **Last checked** | 2026-08-26T06:42:37.316Z |

**Description:**

```
Rotate bosslady-zdot@protonmail.com password and enable 2FA; CTO updates local credentials after
```

**Blocker / conditions:** Zerric action on Proton account

**Completion evidence (result field):** None (open task)

---

## 5. t15-snowsnakes-email — Open snowsnakes@zerric.xyz and verify zerric.xyz domain on the email provider so update...

| Field | Value |
|---|---|
| **ID** | `t15-snowsnakes-email` |
| **Title** (derived) | Open snowsnakes@zerric.xyz and verify zerric.xyz domain on the email provider so update... |
| **Status** | pending |
| **Assignee** | Zerric |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T15:00:00Z |
| **Updated** | 2026-08-26T06:42:37Z (by Zerric) |
| **Last checked** | 2026-08-26T06:42:37.316Z |

**Description:**

```
Open snowsnakes@zerric.xyz and verify zerric.xyz domain on the email provider so updates/promos can send to SnowSnakes users
```

**Blocker / conditions:** DNS access for zerric.xyz + provider account

**Completion evidence (result field):** None (open task)

---

## 6. t17-notif-ui — Dashboard notification UI (bell, unread badge, dropdown, mark-read)

| Field | Value |
|---|---|
| **ID** | `t17-notif-ui` |
| **Title** (derived) | Dashboard notification UI (bell, unread badge, dropdown, mark-read) |
| **Status** | in_progress |
| **Assignee** | ClickClack |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T15:30:00Z |
| **Updated** | 2026-08-23T23:38:15Z (by ClickClack) |
| **Last checked** | 2026-08-23T23:38:13Z |

**Description:**

```
Dashboard notification UI (bell, unread badge, dropdown, mark-read) - PM report shows task 450aa9d6 falsely marked done with nothing built; re-open and build or explicitly descope
```

**Blocker / conditions:** Queued: needs CTO spec; notifications/service.py + webhooks.py missing; schema not applied to company.db

**Completion evidence (result field):** None (open task)

---

## 7. e807f54ae024 — Fix ClickClack glitch: orphaned tool_calls conversation repair (OpenAI 400)

| Field | Value |
|---|---|
| **ID** | `e807f54ae024` |
| **Title** (derived) | Fix ClickClack glitch: orphaned tool_calls conversation repair (OpenAI 400) |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-23T22:58:52Z |
| **Updated** | 2026-08-23T22:58:52Z (by —) |
| **Last checked** | never |

**Description:**

```
Fix ClickClack glitch: orphaned tool_calls conversation repair (OpenAI 400). Rewrote _repair_conversation, 5 regression tests, 73 total pass, committed eeb61cd.
```

**Blocker / conditions:** None

**Completion evidence (result field):** None (open task)

---

## 8. 32281afad433 — Daily SnowSnakes content system: ~20 original dad jokes/day split across 8 accounts

| Field | Value |
|---|---|
| **ID** | `32281afad433` |
| **Title** (derived) | Daily SnowSnakes content system: ~20 original dad jokes/day split across 8 accounts |
| **Status** | assigned |
| **Assignee** | ClickClack |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T03:50:41Z |
| **Updated** | 2026-08-24T03:50:41Z (by —) |
| **Last checked** | never |

**Description:**

```
Daily SnowSnakes content system: ~20 original dad jokes/day split across 8 accounts (ids 56-63: ClickClack_, TedBear, mark, seleena, manny, meta, jasmine, trevor), 1-3 games/day (post own ideas freely). Doodles/comics go to approval folder (NOT posted). Zerric deletes unwanted/duplicates. Owner: whole team, ClickClack coordinates.
```

**Blocker / conditions:** None - live since 2026-08-24 (24 jokes + 3 games posted today)

**Completion evidence (result field):** None (open task)

---

## 9. fce626157ddb — GOAL: 20 real people register on snowsnakes.zerric.xyz

| Field | Value |
|---|---|
| **ID** | `fce626157ddb` |
| **Title** (derived) | GOAL: 20 real people register on snowsnakes.zerric.xyz |
| **Status** | assigned |
| **Assignee** | ClickClack |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T05:23:22Z |
| **Updated** | 2026-08-24T05:23:22Z (by —) |
| **Last checked** | never |

**Description:**

```
GOAL: 20 real people register on snowsnakes.zerric.xyz. Funnel: games/jokes as hooks, Pumpkin's sphere, share-CTAs, high-score challenge. Each registration with email auto-feeds HubSpot CRM.
```

**Blocker / conditions:** None - funnel strategy drafted; needs Mark's challenge copy + Pumpkin share link

**Completion evidence (result field):** None (open task)

---

## 10. e7c11cb0cc4a — GOAL: Hand zerric.xyz to team for creative control (build trust)

| Field | Value |
|---|---|
| **ID** | `e7c11cb0cc4a` |
| **Title** (derived) | GOAL: Hand zerric.xyz to team for creative control (build trust) |
| **Status** | assigned |
| **Assignee** | ClickClack |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T05:23:22Z |
| **Updated** | 2026-08-24T05:23:22Z (by —) |
| **Last checked** | never |

**Description:**

```
GOAL: Hand zerric.xyz to team for creative control (build trust). Audit done 2026-08-24: nexus hub listing 18 projects. Improve descriptions, live status, CTAs, mobile polish, then present changes for approval.
```

**Blocker / conditions:** None - audit complete; awaiting approval to edit zerric.xyz

**Completion evidence (result field):** None (open task)

---

## 11. fb6419251cdc — Spread Da Word: animated series for snowsnakes (episodes feature exists, 2 seeded)

| Field | Value |
|---|---|
| **ID** | `fb6419251cdc` |
| **Title** (derived) | Spread Da Word: animated series for snowsnakes (episodes feature exists, 2 seeded) |
| **Status** | in_progress |
| **Assignee** | ClickClack |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T05:23:23Z |
| **Updated** | 2026-08-24T09:28:25Z (by Zerric) |
| **Last checked** | never |

**Description:**

```
Spread Da Word: animated series for snowsnakes (episodes feature exists, 2 seeded). Brainstorm free/cheap quality animation: Rive/Wick/Synfig (free 2D), Blender grease pencil, AI (Runway/Hedra free tiers), or canvas motion-comic consistent with 8-bit aesthetic. Recommend motion-comic + Rive hybrid.
```

**Blocker / conditions:** Needs Zerric's pick on animation style before building episode 1

**Completion evidence (result field):** dev mode

---

## 12. 2010d8331223 — find a way to call Zerric

| Field | Value |
|---|---|
| **ID** | `2010d8331223` |
| **Title** (derived) | find a way to call Zerric |
| **Status** | assigned |
| **Assignee** | Team Task |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T20:15:18Z |
| **Updated** | 2026-08-24T20:15:18Z (by —) |
| **Last checked** | never |

**Description:**

```
find a way to call Zerric
```

**Blocker / conditions:** None

**Completion evidence (result field):** None (open task)

---

## 13. 7f4fbee20cc5 — Find a way to call Zerric

| Field | Value |
|---|---|
| **ID** | `7f4fbee20cc5` |
| **Title** (derived) | Find a way to call Zerric |
| **Status** | assigned |
| **Assignee** | Team Task |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-24T20:15:58Z |
| **Updated** | 2026-08-24T20:15:58Z (by —) |
| **Last checked** | never |

**Description:**

```
Find a way to call Zerric
```

**Blocker / conditions:** None

**Completion evidence (result field):** None (open task)

---

## 14. 6fd552b2ad07 — # WHO'S WHO

| Field | Value |
|---|---|
| **ID** | `6fd552b2ad07` |
| **Title** (derived) | # WHO'S WHO |
| **Status** | assigned |
| **Assignee** | Meta |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:53:05Z |
| **Updated** | 2026-08-26T04:53:05Z (by —) |
| **Last checked** | never |

**Description:**

```
# WHO'S WHO — Master Audit Checklist (Zerric=Owner vs BossLady=CEO)
Canonical phrasing (per ROLE-CHARTER): "Owner: Zerric · CEO: BossLady"

A. PUBLIC WEB SURFACES
- [ ] A1 zerric.xyz footer — states "Owner: Zerric · CEO: BossLady" (owner: CTO)
- [ ] A2 zerric.xyz About page — role attribution correct (owner: CTO)
- [ ] A3 snowsnakes.zerric.xyz footer/landing — "A Z-Dot LLC project — Owner: Zerric · CEO: BossLady" (owner: CTO)
- [ ] A4 snowsnakes.zerric.xyz lead form "powered by" line (owner: CTO)
- [ ] A5 DNS/registrar — both domains registered to Z-Dot LLC / Zerric (owner: CTO)

B. SOCIAL ACCOUNTS
- [ ] B1 Twitter/X bio — no CEO claim for Zerric; CEO=BossLady stated (owner: Marketer)
- [ ] B2 LinkedIn — Zerric personal profile title = Owner (NOT CEO) (owner: Marketer)
- [ ] B3 LinkedIn — Z-Dot company page: Owner vs CEO listed correctly (owner: Marketer)
- [ ] B4 Instagram @zerric bio — role line correct/absent, no CEO claim (owner: Marketer)
- [ ] B5 Facebook page — same (owner: Marketer)
- [ ] B6 Threads bio — same (owner: Marketer)
- [ ] B7 Third-party directories (Easyleadz, Buzzfile, ZoomInfo) — CONFIRMED FIX: Easyleadz lists Zerric as "CEO"; must be corrected to Owner/Member via directory claims (owner: Marketer; slow external process — flag risk)

C. MARKETING
- [ ] C1 Brand voice guide created (owner: Marketer)
- [ ] C2 50 social drafts audited — full 50-row table (owner: Marketer)
- [ ] C3 All FIX drafts corrected (owner: Marketer)

D. SALES
- [ ] D1 Outreach templates audited + fixed (owner: Sales)
- [ ] D2 Who's Who one-pager created (owner: Sales)
- [ ] D3 Signature line standard defined (owner: Sales)

E. CRM
- [ ] E1 HubSpot company/contact notes — no role confusion; Owner/CEO fields correct (owner: Sales, with Marketer)
- [ ] E2 SnowSnakes→HubSpot lead mapping includes role attribution (owner: CTO)

F. INTERNAL
- [ ] F1 ROLE-CHARTER.md created (owner: HR)
- [ ] F2 TEAM-STATE.md — role lines for Zerric (Owner) and BossLady (CEO) correct (owner: PM)
- [ ] F3 Portal (tasks.zdotllc.com) — role descriptions correct (owner: PM)

G. PAYMENT/LEGAL (currently unconfigured — policy first, then config)
- [ ] G1 BILLING-IDENTITY-POLICY.md — payee = "Z-Dot LLC" everywhere (owner: Finance)
- [ ] G2 Stripe account name = Z-Dot LLC (owner: Finance+CTO)
- [ ] G3 Gumroad store name = Z-Dot LLC (owner: Finance+CTO)
- [ ] G4 Invoice template From field = Z-Dot LLC (owner: Finance)
- [ ] G5 Payment link display name = Z-Dot LLC (owner: Finance+CTO)
- [ ] G6 BizzyBee CRM subscription billing — payee Z-Dot LLC (Free/Pro $19/Business $49) (owner: Finance+CTO)

H. CREDENTIALS/ACCESS COORDINATION
- [ ] H1 Documented access-routing: domains + portal 403 bots; CTO access requests → PM → BossLady (email/SMS) (owner: PM)
```

**Blocker / conditions:** Coordination task from PM Meta — Who's Who initiative; subtasks: 09c4e50293c2 (HR), e26f6281a8b4 (CTO), df294aced64b (Marketing), 55bfbc1ac446 (Sales), ec344facf516 (Finance)

**Completion evidence (result field):** None (open task)

---

## 15. afe1f916d4a1 — BossLady sign-off: SaaS MVP money-loop priority

| Field | Value |
|---|---|
| **ID** | `afe1f916d4a1` |
| **Title** (derived) | BossLady sign-off: SaaS MVP money-loop priority |
| **Status** | assigned |
| **Assignee** | BossLady |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:28Z |
| **Updated** | 2026-08-26T04:54:28Z (by —) |
| **Last checked** | never |

**Description:**

```
BossLady sign-off: SaaS MVP money-loop priority (leads-first vs payments-first) + scope IN/OUT. Doc: resources/SAAS-MVP-ROADMAP.md (delivered, pending decision). Decision gates Phase 1 build order.
```

**Blocker / conditions:** CEO decision required

**Completion evidence (result field):** None (open task)

---

## 16. 2fe7eadeee96 — Configure Gumroad: config.yaml integrations.gumroad.enabled: true + access_token

| Field | Value |
|---|---|
| **ID** | `2fe7eadeee96` |
| **Title** (derived) | Configure Gumroad: config.yaml integrations.gumroad.enabled: true + access_token |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:28Z |
| **Updated** | 2026-08-26T04:54:28Z (by —) |
| **Last checked** | never |

**Description:**

```
Configure Gumroad: config.yaml integrations.gumroad.enabled: true + access_token. Currently UNCONFIGURED (enabled: false, access_token: ''). Tools exist.
```

**Blocker / conditions:** Gumroad access token from Zerric/BossLady

**Completion evidence (result field):** None (open task)

---

## 17. 2fa51aedd56c — Configure invoicing:

| Field | Value |
|---|---|
| **ID** | `2fa51aedd56c` |
| **Title** (derived) | Configure invoicing: |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:28Z |
| **Updated** | 2026-08-26T04:54:28Z (by —) |
| **Last checked** | never |

**Description:**

```
Configure invoicing: config.yaml integrations.invoice.enabled: true + company_name/company_address/payment_instructions/currency. Currently UNCONFIGURED (enabled: false).
```

**Blocker / conditions:** Company billing details from BossLady

**Completion evidence (result field):** None (open task)

---

## 18. df40292e704e — Configure Cal.com bookings:

| Field | Value |
|---|---|
| **ID** | `df40292e704e` |
| **Title** (derived) | Configure Cal.com bookings: |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:28Z |
| **Updated** | 2026-08-26T04:54:28Z (by —) |
| **Last checked** | never |

**Description:**

```
Configure Cal.com bookings: config.yaml integrations.calcom.enabled: true + api_key + default_duration. Currently UNCONFIGURED (enabled: false, api_key: '').
```

**Blocker / conditions:** Cal.com account + API key from Zerric

**Completion evidence (result field):** None (open task)

---

## 19. 54c070ae3827 — Create company blockchain wallet: run `agent-company-ai wallet create`

| Field | Value |
|---|---|
| **ID** | `54c070ae3827` |
| **Title** (derived) | Create company blockchain wallet: run `agent-company-ai wallet create` |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 2 (P2-Med) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:28Z |
| **Updated** | 2026-08-26T04:54:28Z (by —) |
| **Last checked** | never |

**Description:**

```
Create company blockchain wallet: run `agent-company-ai wallet create` (sets config wallet.enabled: true, generates encrypted keystore, registers in DB). Currently NOT created (wallet.enabled: false in config.yaml).
```

**Blocker / conditions:** None - self-serve

**Completion evidence (result field):** None (open task)

---

## 20. b049281d2b3f — SnowSnakes duplicate cleanup: SNOW BEATS cluster ids 97/98/99/101

| Field | Value |
|---|---|
| **ID** | `b049281d2b3f` |
| **Title** (derived) | SnowSnakes duplicate cleanup: SNOW BEATS cluster ids 97/98/99/101 |
| **Status** | assigned |
| **Assignee** | ClickClack |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:29Z |
| **Updated** | 2026-08-26T04:54:29Z (by —) |
| **Last checked** | never |

**Description:**

```
SnowSnakes duplicate cleanup: SNOW BEATS cluster ids 97/98/99/101 (4 live entries: 'loop download', 'Download Your Loop' x2, 'loop download (fixed)'). Keep ONE canonical (recommend 101), delete rest via admin route. Verify no other dup titles. NOTE: FTF dup ids 71/72 already gone (verified 404, single FTF = id 96).
```

**Blocker / conditions:** Admin platform password for @clickclack (Zerric) - promoted but password not received

**Completion evidence (result field):** None (open task)

---

## 21. 14cafa6dd149 — HubSpot SnowSnakes auto-sync: VERIFIED LIVE 2026-08-24

| Field | Value |
|---|---|
| **ID** | `14cafa6dd149` |
| **Title** (derived) | HubSpot SnowSnakes auto-sync: VERIFIED LIVE 2026-08-24 |
| **Status** | assigned |
| **Assignee** | NinjaNerd |
| **Priority** | 1 (P1-High) |
| **Due date** | — not set in portal (field does not exist) |
| **Created** | 2026-08-26T04:54:29Z |
| **Updated** | 2026-08-26T04:54:29Z (by —) |
| **Last checked** | never |

**Description:**

```
HubSpot SnowSnakes auto-sync: VERIFIED LIVE 2026-08-24 - backend HUBSPOT_ACCESS_TOKEN is SET, registration -> contact auto-created (csfe_pipetest_598034 -> contact 540272484082), token read+write+delete. One-line env change DONE. Remaining: Zerric go/no-go to keep auto-sync ON (privacy). Local scripts/hubspot_sync.py clean (28 created/1 updated, last run 2026-08-24).
```

**Blocker / conditions:** Zerric go/no-go (auto-sync already live since 2026-08-24)

**Completion evidence (result field):** None (open task)

---
