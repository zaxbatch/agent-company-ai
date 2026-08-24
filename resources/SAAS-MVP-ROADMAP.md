# Bizzy Bee Solutions — SaaS MVP Scope & Roadmap
Owner: NinjaNerd (CTO) · Draft: 2026-08-24 · Status: DELIVERED, pending BossLady sign-off on scope priorities

## 1. What we are building (positioning)
The product already tells the story: "Spin up an AI agent company — a business run by AI agents, managed by you."
- It is a CLIENT-FACING SaaS for small businesses (solopreneurs, local service companies).
- Z-Dot is the first customer (dogfooding). We run it on ourselves before we sell it.
- Recurring revenue model: $30–50/mo per seat/company (target), paid via Stripe subscription.

## 2. The MVP = the money loop
A small business owner pays us because ONE loop works end to end:
Prospect → CRM → Outreach → Close → Invoice/Pay

| Step | Tool/Feature | Status today |
|---|---|---|
| 1. Prospect search | prospect_tool (web search + contact extraction) | BUILT (creates local contacts) |
| 2. CRM sync | HubSpot contacts upsert | TOKEN ADDED (pat-…, contacts scope OK), NO CODE YET |
| 3. Outreach | Email send (Resend/SendGrid) | NOT BUILT (t13, blocked on provider key) |
| 4. Landing page | landing_page tool + netlify deploy | BUILT (needs polish + live deploy wiring) |
| 5. Close | Stripe payment link / subscription | TABLES EXIST, KEYS MISSING (t5, blocked on Zerric) |
| 6. Visibility | Mission Control dashboard + checklist portal | BUILT (t10 done) |

## 3. MVP scope — IN vs OUT
IN (must work for first paying customer):
- One-company onboarding (setup wizard from existing CLI presets)
- Prospect search → contacts → HubSpot sync (upsert by email)
- Email outreach with templates (Resend/SendGrid) + follow-up cadence
- Landing page per campaign, deployed to Netlify
- Stripe payment link + subscription checkout
- Dashboard showing funnel: prospects → contacted → replied → paid
- Notifications (bell + email) so the owner sees activity (t17)
- Version consistency, CI, secrets hygiene (t9) — trust layer, no exceptions

OUT (post-MVP):
- Public self-serve signup (v1 sells via Z-Dot concierge onboarding)
- Multi-tenant billing/usage metering (single-tenant MVP)
- Blockchain wallet features (keep as optional module, not MVP)
- Advanced analytics/BI
- Agent marketplace / custom role builder

## 4. Roadmap phases
### Phase 0 — Stabilize the foundation (this week) [UNBLOCKERS]
- t9: version drift (pyproject 0.6.1 vs __init__ 0.5.0), CI workflow, move DeepSeek key out of config.yaml
- t13: email provider (Resend or SendGrid) key → email channel live
- t17: finish notifications (service.py + webhooks.py missing; DB schema not applied; config section missing)
- t5: Stripe keys → payment links/subscriptions live
Exit: no plaintext secrets, tests green, email + payments can send real things.

### Phase 1 — MVP money loop (next 2 weeks) [REVENUE]
- HubSpot sync script (contacts upsert from company.db) — unblocks Mark/Seleena immediately
- Email outreach flow: prospect → contact → templated send → reply tracking
- Landing page pipeline: create → deploy → track visits
- Stripe checkout integration (payment link + subscription)
- Funnel dashboard view (Mission Control section)
Exit: a demo company runs the full loop and closes one paid engagement.

### Phase 2 — Sellable SaaS (following month) [PRODUCT]
- Onboarding wizard (company name, industry, team roles, LLM provider choice)
- Per-company data isolation + admin
- Subscription billing with trial (Stripe), dunning, upgrade/downgrade
- Usage limits (searches, emails, pages per month) + overage pricing
Exit: a paying customer (non-Z-Dot) runs on it for 30 days.

### Phase 3 — Scale (later)
- Public signup, self-serve checkout, Stripe webhooks
- Email deliverability monitoring, spam-score checks
- Agent template marketplace, custom roles, API
- Referral/affiliate program (Mark)

## 5. Key risks / decisions
1. NAME: package says "Bizzy-Bee-Solutions"; pyproject description says agent company. Naming affects every landing page — DECISION NEEDED (ties to t11 domain strategy).
2. Email provider: Resend (simple, good deliverability) vs SendGrid (feature-rich). CTO recommends Resend for MVP.
3. Stripe keys (t5) and HubSpot token ownership: both are live credentials that gate revenue. Zerric must provide/enable.
4. HubSpot token scope: currently contacts-only. Deals/owners scopes needed for sales pipeline — requires HubSpot settings change (Zerric's account).
5. SnowSnakes (t1) ownership decision: if it becomes a lead-gen funnel, registrations → HubSpot is a 1-day add; but it is NOT part of the SaaS MVP and must not block it.

## 6. What I need from BossLady (sign-off)
1. Confirm MVP scope IN/OUT above (or trim).
2. Confirm the money-loop priority: leads-first (prospect→CRM→email) vs payments-first (Stripe checkout).
3. Confirm product name direction (Bizzy Bee vs rename) so landing pages can be finalized.
4. Confirm email provider choice: Resend recommended.
