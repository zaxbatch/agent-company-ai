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
