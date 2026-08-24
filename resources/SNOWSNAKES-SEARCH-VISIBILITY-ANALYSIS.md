# SnowSnakes Search Visibility — Decision Prep (t4)
Owner: NinjaNerd (CTO) · Date: 2026-08-24 · Status: ANALYSIS DONE, decision blocked on t1 (ownership)

## Current state (verified live, not assumed)
- robots.txt: allows all crawlers (User-agent: * / Disallow: empty) — so nothing is actively blocked.
- sitemap.xml: returns HTTP 200 but serves the SPA shell HTML (CRA catch-all), NOT a real sitemap. No sitemap route in backend.
- Meta tags: default create-react-app placeholder ("Web site created using create-react-app"). No real title, description, or OG tags.
- Rendering: client-side React SPA. Crawlers that don't execute JS see an empty #root shell. Content lives behind /api/* calls.
- Net result: technically crawlable, effectively invisible. Consistent with earlier finding: does not rank under its own name.

## What "make it visible" actually requires (CRA SPA reality)
1. Real meta/OG tags per page (title, description, image) — react-helmet or manual index.html updates.
2. A real sitemap.xml served by the backend listing content URLs (jokes, games, characters).
3. Crawler-visible content: either (a) prerendering/SSR (e.g., react-snap, prerender service) or (b) Google-indexed via JS rendering (slower, weaker) — for CRA, react-snap is the pragmatic path.
4. Canonical URLs, structured data (optional for v1).
5. Post-build deploy pipeline to Hostinger (existing htaccess/WAF quirks to respect).
Estimate: 2-4 focused days including deploy and verification, not including content/landing page copy.

## Options for Zerric
- OPTION A — Keep invisible (personal/fun project): do nothing. Optionally tighten robots.txt to block. Cost: $0. Risk: none.
- OPTION B — Full visibility (lead-gen funnel): do the 5 items above. Cost: 2-4 dev days + ongoing monitoring. Upside: organic traffic to a fun content site; registrations feed HubSpot (ties to goal 4a492b667ed7 + t16 email list).
- OPTION C — Middle path: fix meta + sitemap only, accept weak JS indexing, defer prerendering. Cost: ~1 day. Small SEO win, no heavy lift.

## CTO recommendation
Depends on t1. If SnowSnakes is a Z-Dot-tracked lead-gen asset: OPTION B, sequenced AFTER the SaaS MVP money loop (Phase 1) — SEO is a growth lever, not a revenue prerequisite. If personal-only: OPTION A, and remove it from the checklist entirely to stop recurring overhead.

## Gate
DECISION NEEDED from Zerric (t1): personal-only / referral channel / Z-Dot-tracked. This doc is the execution plan for whichever way it lands.
