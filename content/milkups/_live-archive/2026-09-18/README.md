# MilkUps live snapshot — 2026-09-18

Immutable snapshot of the **live** page as served by the host, taken because the
copy versioned in the tree (`default/landing_pages/milkups.html`) was stale and
carried no payment rail.

## Provenance

| item | value |
|---|---|
| Source URL | `https://milkups.zerric.xyz/` |
| HTTP status | `200` |
| Content-Type | `text/html` |
| `last-modified` (host) | `Thu, 17 Sep 2026 01:37:59 GMT` |
| `etag` (host) | `W/"3594-6aab4477-60686a6fb6ae5f59;gz"` |
| Fetched | 2026-09-18 (curl, plain HTTP GET — no browser UA required) |
| Size | 13716 bytes |
| SHA-256 (HTML) | `c20ca096f12f27641a20096a3b9e42dc949451a42da0db0f77bc95825bff2c9d` |

| asset | URL | status | size | SHA-256 |
|---|---|---|---|---|
| CashApp QR | `https://milkups.zerric.xyz/assets/cashapp-zdotllc-qr.png` | `200` | 2047 B | `ca7954a4ea1f96cafee86b0759bba3ac0bd9f64456319311d3366d69519b264f` |

## Why the live QR is archived here

The live QR image is **not** byte-identical to `content/milkups/assets/cashapp-zdotllc-qr.png`
(2047 B vs 1834 B). The repo copy is therefore not the artifact that is actually
published. This snapshot records the bytes that really serve, so a future rebuild
has a known base instead of an assumption.

## Payment rail present in this snapshot

- `assets/cashapp-zdotllc-qr.png` — QR rendered in the "SUPPORT THE SHELF" section
- `cash.app/$zdotllc` — outbound tag link, `rel="noopener"`
- Handle `$zdotllc` verified working on a real device (Zerric)

## Rules

- **Read-only archive.** Do not edit these files; they are evidence of served state.
- Do not treat this directory as the deploy source. The homepage source of record is
  documented in `content/milkups/DEPLOY-NOTES.md`.
- No secrets belong in this directory.
