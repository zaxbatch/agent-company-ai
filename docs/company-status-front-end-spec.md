# PROJECT SPEC — Company Status Front End (CSFE)

Sponsor: BossLady (CEO) | PM/QA: Meta | Build: NinjaNerd (CTO) | Copy: Mark (marketer) | Metrics: Seleena (sales) | Integrations: Finance

## Goal
Publicly showcase Z-Dot LLC status: service health, live metrics, revenue placeholders, and roadmap. Builds trust with prospects, clients, and investors.

## Scope
Public status page at https://snowsnakes.zerric.xyz/status (primary), fallback https://zerric.xyz/status.
Sections:
1. Service Status — health cards for all 5 games with REAL health data from live monitoring (NOT hardcoded)
2. Live Metrics — CRM lead counter with REAL HubSpot numbers
3. Revenue Placeholders — config-driven placeholder revenue cards (clearly marked) until Stripe/Gumroad/Cal.com/wallet are wired
4. Roadmap — next-90-days items (marketer copy)
5. Footer — Z-Dot branding + disclaimer
Endpoint: /api/metrics.json returns live JSON (per-game health, lead count, revenue placeholders).

## Out of scope
- LPT Realty content (never on these domains — license protection)
- Real revenue numbers until Zerric provides keys (placeholders launch regardless)
- Content pre-approval (SnowSnakes/zerric.xyz content needs no pre-approval per domain decision 2026-08-24; LPT remains the only pre-approval category)

## Success criteria
1. URL live, HTTP 200
2. All 5 game cards show real per-game health data (evidence: curl /api/metrics.json shows distinct values matching monitoring)
3. Lead counter returns real HubSpot numbers
4. Revenue cards render placeholders (visually marked)
5. /api/metrics.json valid JSON, documented schema
6. <3s load, mobile-responsive
7. QA sign-off requires evidence (curl output + screenshots), never verbal claims (Bot Mode precedent)

## Timeline (5 days)
- Day 1: spec approved; tasks created on portal; dependencies delegated; blocker register opened; escalation sent
- Day 2: copy (marketer), metric definitions (sales), integration status (finance) delivered
- Day 3: build complete (CTO) — live URL + /api/metrics.json
- Day 4: QA gate 1 — internal verification (curl endpoint, click-through all sections, real-vs-hardcoded check, placeholder check)
- Day 5: QA gate 2 — final verification, blocker close-out, launch, closure report

## Blocker register (initial)
| ID | Blocker | Owner | Needed for | Status | Escalation |
| B-01 | Stripe API keys | Zerric | Revenue integration | OPEN | SMS via scripts/send_message.py |
| B-02 | Gumroad token | Zerric | Revenue integration | OPEN | same |
| B-03 | Cal.com API key | Zerric | Booking/metrics | OPEN | same |
| B-04 | Wallet creation | Zerric | Payments | OPEN | same |
All 4 escalated Day 1; follow-up Day 3 if still open. Page launches with placeholders regardless.

## Risks
- Credential blockers (all Zerric-owned) delay revenue wiring → mitigated by placeholder launch
- Verbal "done" claims (Bot Mode precedent) → QA requires artifact inspection only
- HubSpot API limits → degraded mode shows counter as unavailable rather than fake data
- Domain/SSL issues → fallback URL documented

QA checklist (Day 4-5): HTTP 200; 5 game cards populated; health data real (per-game distinct values); lead counter real; revenue placeholders render; metrics.json valid; mobile OK; no LPT content.
