# Stripe Unlock Checklist — ready to execute the moment BossLady provides keys
Prepared: NinjaNerd (CTO) · 2026-08-24 · Status: AWAITING STRIPE KEY

## What already exists (verified in repo)
- src/agent_company_ai/tools/stripe_tools.py (payment links)
- src/agent_company_ai/tools/stripe_subs.py (subscriptions)
- config.py expects: STRIPE_SECRET_KEY + STRIPE_WEBHOOK_SECRET (env vars)
- DB tables ready: payment_links, subscription_links, revenue, invoices (all empty)

## What we need from BossLady/Zerric (2 keys)
1. STRIPE_SECRET_KEY — the API key (sk_live_... or sk_test_...)
2. STRIPE_WEBHOOK_SECRET — for webhook signing (needed to confirm payments server-side)

## Execution steps (once keys arrive)
1. Add both to .env (git-ignored, safe)
2. Verify with a test call: create a test payment link via stripe_tools
3. Wire the money loop: prospect -> CRM -> outreach -> close -> Stripe payment link
4. Test subscription flow (SaaS MVP)
5. Confirm webhook endpoint receives events

## First monetization targets (BossLady liked the ideas)
- SaaS MVP subscriptions (the agent-company product)
- Z-Dot services payment links (consulting, website builds)
- SnowSnakes later monetization (separate track)

## Note
Zerric said he'll get a Stripe key for us (2026-08-24). This checklist is the ignition.
