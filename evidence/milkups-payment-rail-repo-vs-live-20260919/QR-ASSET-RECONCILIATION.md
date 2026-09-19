# milkUps payment rail — repo vs live reconciliation

**Task:** ITEM 1 (corrected premise) — P1, deadline 2026-09-20
**Operator:** NinjaNerd (CTO), Z-Dot LLC
**Date of evidence:** 2026-09-19 (UTC)
**Constraints honoured:** live page NOT edited · nothing rebuilt · Stripe untouched · no LPT content

---

## 0. Headline

| question | answer |
|---|---|
| Does `assets/cashapp-zdotllc-qr.png` exist on the live host at the path the page expects? | **YES. HTTP/2 200.** The QR is NOT broken. |
| Is the QR asset in version control next to `milkups.html`? | **YES — added by the commit that carries this file (see `git log` for the hash; recorded in this directory).** |
| Is the repo copy the live source? | **NO — it is a byte-exact synced mirror.** Live primary is Hostinger docroot, not deployable from this repo. |

**No revenue-path outage.** The QR image serves, and its decoded payload matches the
text link on the page exactly.

---

## 1. Live QR asset probe (raw status)

URL the page actually requests (relative `src`, resolved against the live document):

    https://milkups.zerric.xyz/assets/cashapp-zdotllc-qr.png

### Browser-like UA (Chrome 124, `Accept: image/*`)

    HTTP/2 200
    content-type: image/webp
    content-length: 1544
    cache-control: public, max-age=3600
    server: hcdn
    x-hcdn-cache-status: MISS
    x-hcdn-upstream-rt: 0.048

    HTTP_CODE=200  CONTENT_TYPE=image/webp  SIZE_DOWNLOAD=1544

The 1544-byte `image/webp` body is Hostinger's `hcdn` image-optimisation path: it
re-encodes the PNG on the fly for browsers that advertise WebP. That is expected
behaviour, not a broken asset.

### Forcing the original PNG (`Accept: image/png`)

    HTTP/2 200
    content-type: image/png
    content-length: 2047

    HTTP_CODE=200  CONTENT_TYPE=image/png  SIZE_DOWNLOAD=2047
    file: PNG image data, 396 x 396, 8-bit/color RGB, non-interlaced
    sha256: ca7954a4ea1f96cafee86b0759bba3ac0bd9f64456319311d3366d69519b264f

**Verdict: 200, not 404. The payment rail renders for real users.**

### Payload verification (QR actually decodes)

Decoded with OpenCV `QRCodeDetector` (venv, cv2 5.0.0):

    .agent-company-ai/default/landing_pages/assets/cashapp-zdotllc-qr.png  ->  'https://cash.app/$zdotllc'
    content/milkups/_live-archive/2026-09-18/cashapp-zdotllc-qr.png        ->  'https://cash.app/$zdotllc'
    content/milkups/assets/cashapp-zdotllc-qr.png                          ->  'https://cash.app/$zdotllc'

The QR payload is **identical to the page's own outbound link**
`<a class="tag-link" href="https://cash.app/$zdotllc">`. The rail is coherent
end-to-end: image -> decode -> handle -> destination.

---

## 2. The 403 could not be reproduced

The premise stated the live page returns 403 to non-browser clients (Cloudflare
managed challenge). **Not reproducible.** All client classes returned 200:

| client | target | status |
|---|---|---|
| empty UA | `/` | **200** |
| `Go-http-client/1.1` | `/` | **200** |
| `python-httpx/0.27.0` | `/` | **200** |
| `python-requests/2.31.0` | `/` | **200** |
| `curl/8.5.0` | `/` | **200** |
| `Mozilla/5.0 (compatible; Googlebot/2.1)` | `/` | **200** |
| browser-like Chrome 124 | `/assets/cashapp-zdotllc-qr.png` | **200** |

Also 200 over IPv4 (`191.101.104.119`) and IPv6 (`2a02:4780:4a:83dd:...`), and
across 5 rapid sequential hits.

**Correction to the premise:** the edge in front of `milkups.zerric.xyz` is
**Hostinger `hcdn`** (`server: hcdn`, `platform: hostinger`, `panel: hpanel`), *not*
Cloudflare. There is no managed challenge on this host.

Most likely explanation for the earlier 403 — the repo's own tooling documents it:
`scripts/sync_milkups_netlify.py` carries the comment *"Hostinger CDN 403s httpx as a
bot; FTP is the reliable path"* and its `fetch()` helper retries 5x with backoff
because *"Hostinger rate-limits rapid bulk pulls (403)"*. So a 403 here is a
transient **bot/rate-limit** response from Hostinger, self-clearing, and it is why
this task previously looked blocked. It is not a permission wall around the page.

---

## 3. Is `default/landing_pages/milkups.html` the live source?

**Answer: it is a byte-exact MIRROR of the primary live page, but it is NOT the
deploy source.** This is the one genuinely unresolved item, and it is unresolved in
the direction of "we do not control the live primary from git."

Evidence for the mirror claim:

    live https://milkups.zerric.xyz/       13716 B  sha256 c20ca096f12f27641a20096a3b9e42dc949451a42da0db0f77bc95825bff2c9d
    repo .agent-company-ai/default/landing_pages/milkups.html
                                           13716 B  sha256 c20ca096f12f27641a20096a3b9e42dc949451a42da0db0f77bc95825bff2c9d
    cmp -> identical, byte for byte

Evidence against it being the deploy source:

1. **The live primary is Hostinger, not git.** Response headers on
   `milkups.zerric.xyz` are `platform: hostinger`, `panel: hpanel`, `server: hcdn`.
   The docroot is `/domains/zerric.xyz/public_html/milkups` (named explicitly in
   `scripts/sync_milkups_netlify.py`, which pulls binaries from there over FTP).
   Nothing in this repo pushes to that docroot; the sync script reads *from* it.
2. **There is no CI/CD that deploys these pages.** `.github/workflows/` contains only
   `publish.yml` (PyPI release) and `test.yml`. `netlify.toml` only defines
   `/api/tasks` redirects. No workflow reads `default/landing_pages/`.
3. **The file is not even normally tracked.** `default/landing_pages/` sits under
   `.agent-company-ai/`, which `.gitignore` line 1 excludes. It is only in git
   because a previous run force-added it. A gitignored path cannot be a deploy source.

Therefore:

> **`default/landing_pages/milkups.html` is verified-equal to live, not verified-to-be
> live's origin.** Treat it as a trustworthy *record* of the primary page — safe as a
> rebuild base content-wise — but do NOT assume editing it changes the live site.

### What would answer it definitively

- **Read the Hostinger docroot over FTP** (`/domains/zerric.xyz/public_html/milkups/index.html`)
  and hash it. If it equals `c20ca096...`, the primary is a hand/script-maintained
  file on the host and git holds only a copy.
- **Identify the writer.** Check the host's `last-modified: Thu, 17 Sep 2026 01:37:59 GMT`
  against deploy logs / action-history in hPanel to see which mechanism wrote it.
- **Establish the deploy path for the primary.** Today the documented "working rail"
  (`DEPLOY-NOTES.md`) is Netlify, which is a *mirror* — see below. The primary's
  deploy mechanism is undocumented.
- **Rule on which host is canonical**, then wire it to git so a rebuild is reviewable.

---

## 4. There are TWO live front doors, and they differ

| | primary | mirror |
|---|---|---|
| URL | `https://milkups.zerric.xyz/` | `https://milkups.netlify.app/` |
| host | Hostinger `hcdn` (hPanel) | Netlify (`x-nf-request-id`) |
| homepage bytes | 13716 | 12834 |
| homepage sha256 | `c20ca096f12f2764...` | `1f65e5c306eb3041...` |
| QR bytes | 2047 | 1834 |
| QR sha256 | `ca7954a4...` | `9b7013d7...` |
| deploy source | FTP/hPanel to docroot — **not in git** | `content/milkups/` via `scripts/sync_milkups_netlify.py` |

Both front doors serve the payment rail, and **both QRs decode to
`https://cash.app/$zdotllc`**.

`content/milkups/index.html` is 12114 B / `52e364a24ab1f740...` and the Netlify site
serves 12834 B / `1f65e5c3...` — so the Netlify mirror is **stale** relative to its
own source (6 differing lines). The mirror is not the rail, but it is a second
public URL that can drift.

---

## 5. Which QR bytes should the repo hold? (and a correction)

The repo already held `content/milkups/assets/cashapp-zdotllc-qr.png` (1834 B,
`9b7013d7...`). The live primary serves 2047 B, `ca7954a4...`. A previous commit
(`e9eae7ad`) recorded the delta as "the repo copy is not the published artifact."

**At byte level that is true. At image level it is misleading, and it matters for the
rebuild base.** Verified this turn:

    decode both                     -> both 'https://cash.app/$zdotllc'
    max absolute pixel difference   -> 0
    pixels differing by >16/255     -> 0 of 156816
    thresholded dark-matrix mismatch-> 0
    IDAT chunk length in both       -> 1777 bytes (identical)

The 213-byte difference is **PNG metadata only**: the live file carries extra
`pHYs` (9 B) and `eXIf` (180 B) chunks that the repo copy lacks.

    live  chunks: IHDR, pHYs, eXIf, IDAT(1777), IEND
    repo  chunks: IHDR, IDAT(1777), IEND

**Conclusion: the two files are the same raster and the same QR payload. The repo
copy was never a wrong or broken graphic — it is the published image minus metadata.**
So there is no "we don't hold the real asset" problem of substance; there was a
*mirroring/provenance* problem, which is now fixed.

`assets/` also holds `qr-zdotllc.png` and `qr-zdotllc-5.png` (600x600, palette).
Both decode — the second to `https://cash.app/$zdotllc/5`, i.e. a **$5-preset** variant.
Those two are the ones used by the `/album/v2/` cut, not by the homepage.

---

## 6. What was changed in the repo (only the repo)

- **Added** `.agent-company-ai/default/landing_pages/assets/cashapp-zdotllc-qr.png`
  — the live primary's exact bytes (2047 B, `ca7954a4...`), so the repo holds the
  payment rail *and* the asset the page points at, in the same directory. This is the
  directory that previously did not exist at all, which is what made the `src`
  attribute a dangling reference **inside the repo** even though it resolved on the host.
- **Added** this evidence directory.

**NOT changed:** the live page (no writes to the host), the HTML of `milkups.html`
(sha256 unchanged), any Stripe integration, any LPT/real-estate content.

### Residual risk / technical debt

1. `default/landing_pages/assets/` is a **web-served directory**. It was deliberately
   left containing the PNG only — no README, no provenance text — so that a future
   deploy of this directory cannot publish documentation files to a public docroot.
   Provenance lives in `evidence/` and `content/milkups/_live-archive/` instead.
2. The path is gitignored (`.gitignore` line 1, `.agent-company-ai/`), so the asset is
   force-added and **a future `git clean -fdx` or careless re-clone can silently drop
   it again**. If the payment rail must be durable in version control, the real fix is
   to stop tracking live-page sources under a gitignored directory — move the canonical
   copy to `content/milkups/` and symlink or document the relationship. **Recommend
   doing this before the cassette-shelf rebuild, not during it.**
3. The primary's deploy path is undocumented. Until it is, every edit to the live page
   is an out-of-band host edit and cannot be code-reviewed or rolled back.
