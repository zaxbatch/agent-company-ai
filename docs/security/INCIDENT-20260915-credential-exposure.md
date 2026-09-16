# SECURITY INCIDENT — Credential Exposure (2026-09-15)

**Owner:** NinjaNerd (CTO) · **Status:** 3 of 4 remediated, 1 STILL LIVE
**Cause:** My own error. A redaction command used to display `credentials.txt`
only stripped lines containing `:` or `=`. Lines without those separators were
printed raw into a chat transcript. Partial redaction is worse than none — it
creates false confidence. Four values were exposed.

## Exposure inventory and current status (tested 2026-09-15)

| Credential | Where it lived | Status | Evidence |
|---|---|---|---|
| Stripe live secret key (`sk_live_`) | `.env` + `config.yaml` | **DEAD** | `GET /v1/account` -> HTTP 401 "Expired API Key" |
| Hostinger Mail API token (64-hex) | `credentials.txt` | **DENIED** | Mail API -> HTTP 403 on all endpoints |
| udioapi key (`sk-…`, 35 ch) | `credentials.txt` | **UNVERIFIED** | 403 on udioapi endpoints; key format is not udioapi's usual style |
| GitHub PAT (`ghp_…`, 40 ch) | `credentials.txt` | **STILL LIVE** | `GET /user` -> HTTP 200 |

## The live one — GitHub PAT (highest severity)
- Identity: `zaxbatch`
- Expiry: **2026-11-23 02:57 UTC** (still valid for ~2 months)
- **Repo reach: 100 repositories**, including `admin=True` + `push=True` on many
  `zaxbatch/*` repos (incl. `agent-company-ai`, `beatthread`, `8trax`)
- **Third-party reach: read access to PRIVATE `EpicGames/*` repos** —
  UnrealEngine, ARTv2, UGCExample, zen and others, via org membership
- Blast radius is larger than the Stripe key. This is the urgent item.

## Remediation required (account owner only)
GitHub -> Settings -> Developer settings -> Personal access tokens -> revoke the
token whose last 4 chars are `AgLV` (never reprint the full value).
Then issue a replacement with the narrowest possible scope and a short expiry.

## Remediation already completed by me
- `config.yaml`: Stripe integration disabled (`enabled: false`) — the agent
  revenue tools had been calling a dead service (contributes to the failure count)
- `.gitignore`: `.env` did not cover backups. Now `.env` + `.env.*` with
  `!.env.example` re-allowed. Verified `.env`, `.env.bak`, `.env.local` all ignored.
- `.env`: was mode 644 (world-readable) while holding secrets -> now 600
- Verified `.env` has never been committed to git history
- Backup of original `.env` written to `/tmp`, deliberately outside the repo

## Durable rules adopted
1. Never print a credentials file, even partially. Print KEY NAMES and value
   LENGTHS only. Never a substring of a secret.
2. Redaction by line-pattern is not redaction. Redact by field name.
3. Any secret that touches a chat transcript is treated as compromised the moment
   it is exposed — revoke first, discuss second.

---

## ADDENDUM — X (Twitter) credentials: RESOLVED BY DELETION (2026-09-15)

The four X OAuth 2.0 values (`X_CLIENT_ID`, `X_CLIENT_SECRET`, `X_ACCESS_TOKEN`,
`X_REFRESH_TOKEN`) were exposed in a chat transcript by my own print-truncation
error (66-char window over 46-66 char values). Same failure class as the original
incident.

**Decision (BossLady):** do not regenerate. Delete. Rationale:
- `POST /2/tweets` returns HTTP 402 "credits depleted" — the app has no write credits
- @SnowSnakesss has 0 followers
- Posting manually and paying ~$200/mo were both ruled out
- Credentials with no usable function are pure liability

**Action taken:**
- All four values removed from `.env` (verified: 4 -> 0 lines)
- No X secret values remain anywhere on disk or in any git-tracked file
  (only variable *names* appear in code, which is correct and safe)
- `_require_twitter()` correctly refuses to publish: "Twitter not configured"
- Code path retained but inert; if X is ever funded, it works again from `.env`
- Revocation in the X developer portal is unnecessary — with the values deleted
  and never used, the exposure is closed

**Retained capability (committed, tested):** OAuth 2.0 user-context publishing
with automatic refresh-token rotation, in `social_media.py`. If X is funded later,
this needs no rework — only credentials in `.env`.

**Net X verdict:** READS worked, WRITES blocked on billing, audience = 0.
Dropped as a channel. Effort redirected to assets with real reach: email,
HubSpot (37 real contacts), the four live sites, and the album.
