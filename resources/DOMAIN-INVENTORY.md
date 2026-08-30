# Z-Dot Domain Inventory & Infrastructure Reference
Canonical list of company domains, purpose, registrar, DNS, mail, and usage policy.
Last verified: 2026-08-30 (NinjaNerd/CTO). Source of truth for "which domain do we use for what."

## DOMAIN USAGE POLICY (BossLady directive, 2026-08-30)
| Domain          | Use                                                          |
|-----------------|--------------------------------------------------------------|
| @zdotllc.com    | REAL Z-Dot correspondence ONLY (staff, clients, vendors). Never for dummy/test/QA/seed accounts. |
| @zerric.xyz     | PLAY-which-is-business: SnowSnakes, MilkUps, SpreadDaWord, Snitch, games. Content owners use @zerric.xyz mailboxes: milkups@, snowsnakes@, spreaddaword@, snitch@ (forward to ez@zerric.xyz). Keeps play separate from work. |
| @zdot-dummy.com | ALL dummy/test/QA/seed/persona accounts. NEVER real correspondence. |

## DOMAINS
| Domain            | Status        | Registrar               | DNS (NS)                 | MX (mail)                 | Purpose / Notes |
|-------------------|---------------|-------------------------|--------------------------|---------------------------|-----------------|
| zdotllc.com       | REGISTERED    | Squarespace Domains II LLC (IANA 895); reg 2020-06-24, exp 2027-06-24 | byte.dns-parking.com / pixel.dns-parking.com (Hostinger parking) | mx1/mx2.hostinger.com (pri 5/10) | Real business domain. 14 live mailboxes (zerric@, bosslady@, bots@, info@, sales@, support@, ceo@, team@ + 6 agent boxes) all forward to zerric@zdotllc.com. ON HOLD for web work per BossLady 2026-08-24 — email stays live. |
| zerric.xyz        | REGISTERED    | (registrar TBD — Identity Digital RDAP; registered via XYZ/registrar, verify in hPanel) | ns1/ns2.dns-parking.com (Hostinger) | mx1/mx2.hostinger.com (pri 5/10) | Nexus hub / playground. 5 mailboxes (ez@, snowsnakes@, milkups@, spreaddaword@, snitch@) forward to ez@zerric.xyz. |
| zdot-dummy.com    | **FICTIONAL — NEVER REGISTERED** (Zerric 2026-08-30: no purchase, no hPanel) | — | — | **NONE** (fictional by design) | TEST/QA/SEED/persona domain per BossLady policy. **HubSpot label only** — easy to sort/delete/manage dummy records. Never used for real mail. |
| snowsnakes.zerric.xyz | LIVE subdomain | n/a (subdomain)      | zerric.xyz               | n/a                        | Lead-collection app; registrations feed HubSpot CRM. |
| tasks.zdotllc.com | LIVE subdomain | n/a (subdomain) | zdotllc.com (Hostinger)  | n/a                        | Checklist portal (PHP, hostinger_tasks/). Team logins. |
| snitch.zerric.xyz | LIVE subdomain | n/a            | zerric.xyz               | n/a                        | Snitch app (email capture, tag 'snitch'). |
| spreaddaword.zerric.xyz | LIVE (pending final) | n/a | zerric.xyz          | n/a                        | SpreadDaWord game. |
| milkups.zerric.xyz | LIVE (pending final) | n/a | zerric.xyz            | n/a                        | MilkUps band page. |

## MAIL DECISION — zdot-dummy.com (Zerric 2026-08-30: FICTIONAL, never registered)
**Decision: NO MX records, NO catch-all mailbox. zdot-dummy.com is a NON-DELIVERABLE SYNTAX DOMAIN.**
- Verified 2026-08-30: NO Z-Dot app sends email to registered users today. SnowSnakes registration = instant HTTP 201 + HubSpot contact (no verification email). SDW v1 sign-in = name+email, no password, no reset flow. Internal tools (dashboard/portal) = no email verification. Only SMTP usage in the codebase is TEAM OUTBOUND (scripts/send_email.py from ez@zerric.xyz / bots@zdotllc.com) — real correspondence, never app-generated user mail.
- Consequence of "no MX": any accidental test email to @zdot-dummy.com bounces immediately at DNS → visible in app logs → surfaces bugs in QA instead of silently hitting a real mailbox. This is a FEATURE.
- Zero mailbox cost (vs Hostinger mail plans). Protects HubSpot: dummy emails can't become real contacts that get contacted.
- **Anti-abuse (Zerric 2026-08-30): NOT REGISTERED BY DESIGN** — no DNS at all, so @zdot-dummy.com can never send or receive real mail. No SPF/DMARC needed. HubSpot label only.
- **NO UPGRADE PATH — FICTIONAL BY DESIGN (Zerric 2026-08-30):** do not add MX/mailboxes. If an app ever needs to send test emails, use a real throwaway provider (e.g. Mailinator-style) — never register this domain.

## NO REGISTRATION — zdot-dummy.com (Zerric 2026-08-30)
Zerric confirmed: DO NOT register this domain, DO NOT touch hPanel. It exists purely as a HubSpot sort/delete/manage label for fictional/dummy records. No DNS, no MX, no SPF/DMARC needed — never real mail.


## MIGRATION SURFACE (delegated ClickClack)
- 8 SnowSnakes personas (ids 72-79) in .snowsnakes_real_users.json currently use gmail.com emails → switch to @zdot-dummy.com (e.g. sam.rivera@zdot-dummy.com) once domain registered. Update local JSON + live user records (backend admin) + any seed/test fixtures. Do NOT touch real users or real mailboxes.
- MilkUps brand account (id 86) deliberately has NO email (HubSpot cleanliness) — leave as-is.
- Future rule: every new dummy/QA/seed/persona account uses @zdot-dummy.com from day one.

## COSTS (annual, est.)
- zdot-dummy.com: $0 (fictional, never registered — Zerric 2026-08-30). No mailbox plan. No other domain costs.
- No other domain costs introduced by this change.
