# DOODLE LICENCE & RIGHTS MEMO — v0 (DRAFT)
**Owner:** NinjaNerd (CTO) · **Created (UTC):** 2026-09-12T05:45:00Z · **Status:** DRAFT v0 — NOT a clearance. Requires a vendor decision (BossLady/CEO) before it can become v1.
**Evidence bundle (primary sources, fetched and stored):** `evidence/doodle-mix-primary-sources/`
**Bundle manifests:** `urls.json` sha256 `3432224ad5800c76af92954538c4461ca6cc6a3790b5f9a1c68242b413ab74d4`; `pwurls.json` sha256 `1705f94f5ad9000f7165402ef31df23d4f91eb5f30ac4526aa6b6141ce7f6987`

## 0. Bottom line
1. **No doodle-maker vendor is licensed, and no seat is registered.** Nothing in this memo authorises any asset for commercial use yet.
2. The **"doodle maker" category is dominated by whiteboard-VIDEO authoring tools** (DoodleMaker, Doodly, VideoScribe, mysimpleshow, Animaker, Sparkol, Voomly, RawShorts). Our requirement is **static brand doodles** (PNG/SVG). Buying one of those for static art is a **category mismatch** — this is the single most important finding for the owner's goal.
3. Where a vendor does grant clean output ownership, it is on the **paid** tier only, and it is usually conditioned. **Recraft Free Tier: the vendor owns the output and no commercial use is permitted** (verbatim below). Any "let's just use the free tier" shortcut is a rights landmine.
4. **Programmatic/in-house output (our own renderer) is the only class we currently own outright** with no third-party terms attached. That is the safe v1 volume layer.
5. **Not legal advice.** Before anything is *sold* (merch, publisher submission, sponsor creative), this memo needs a lawyer's review — budgeted as a gate, not paperwork.

## 1. Method and honesty statement
- Primary sources fetched directly (raw HTML + rendered text) and stored with the bundle. Some vendors blocked automated fetch; those are recorded as **UNVERIFIED**, not as "probably fine".
- Quotations below are from the stored files. Where a page failed, no conclusion is drawn.
- **Fetch failures (recorded, not hidden):** adobe.com `ERR_HTTP2_PROTOCOL_ERROR` (both URLs); midjourney.com terms → 404 page; procreate.com/legal → 404; about.ideogram.ai → JS-only shell (39 chars); videoscribe.co terms → 404; mysimpleshow.com/terms-of-use → "Page Not Found"; voomly.com/terms → 120-byte shell; sparkol.com/legal → 2.5k legal-index page; doodly.com → see `raw-*` set; one URL returned `403 Forbidden`.

## 2. Vendor findings (primary-source, quoted)
### 2.1 DoodleMaker (doodlemaker.com) — the literal name match
- **What it is:** cloud whiteboard-doodle **video** product. "Automatically Transforms Any Text or Content Into Colorful Doodle Videos" (`raw-423c6800.html` / `raw-e4f9ba5f.html`). Output = **video**, up to 6 minutes, 720p HD — not static brand doodles.
- **Price:** one-time payment, launch pricing around **$47** with a `$20 OFF` coupon; higher tiers at $197 referenced on page (`raw-423c6800.html`).
- **Rights as advertised:** "**Get Commercial Rights INCLUDED**"; "**Enterprise License Included** — Sell Doodle Maker videos to clients and keep all the revenues"; "5 Million Royalty-Free Images", "Copyright-Free Music Library".
- **Terms of Service (`raw-40960d64.html`) §6 COPYRIGHT:** "All copyright, trade marks and all other intellectual property rights in **the Website and its content** … are owned by or licensed to DoodleMaker." **The ToS contains NO clause assigning ownership of *user output* to the user, and NO AI-training clause.** So the commercial right rests on *marketing copy*, not on a contract clause — weak evidence for a sellable asset.
- **Disclaimer (`raw-83a9d9dc.html`):** output provided "AS IS"; results are the end user's responsibility.
- **Verdict: NOT RECOMMENDED for the stated goal.** Category mismatch (video, not static), and the commercial-use claim is not backed by a ToS assignment clause.

### 2.2 Recraft — the only fetched source with an explicit output-ownership assignment
- **Free Tier (ToS §7.1):** "**no commercial use of Free Tier Assets is permitted**"; "Free Tier Assets are **owned by Recraft** and may not be sold, licensed or transferred"; "you hereby irrevocably transfer and assign to Recraft all worldwide right, title and interest in and to the Free Tier Assets".
- **Paid Subscription (§7.2):** "**You own all Assets you create with the Services** and Recraft hereby assigns to you all copyright rights it may have in the Assets" — **conditioned**: Assets may not be used to train AI models.
- **Workspace (§7.4):** group plan requires a **minimum of three (3) paid seats**; seats are assigned/managed by a Workspace Admin. Relevant to the seat-domain question.
- **Training (§7.7):** by default Recraft may use Inputs/Assets to train its models (opt-out in account settings).
- **Verdict: viable candidate, paid tier only.** Requires ≥1 paid seat (workspace = 3 seats minimum); if a workspace is used, the seat must be a real `@zdotllc.com` alias.

### 2.3 Canva
- ToS fetched and stored (`pw-43c04a62.html`/`.txt`, 1.29 MB / 28 KB text). Contains an explicit multi-seat team clause: "if you are accessing our Services using your Canva credentials associated with a Canva multi-seat team … we collect, use, transfer, disclose and store certain Personal Data on your behalf as a data controller subject to … our Data Processing Addendum." Output-ownership language is standard "you retain your content"; **no AI-specific output assignment verified in the fetched text**.
- **Verdict: candidate for decorative/volume work only.** Not cleared for sellable hero art on the evidence I hold.

### 2.4 Comparators (video-first, partial fetch)
| Vendor | Fetch result | Note |
|---|---|---|
| VideoScribe (sparkol) | pricing fetched (`raw-d82bebe1.html`: $0 / $12.50 / $150 / $18.75 / $225 / $23.33 tiers) | Whiteboard video authoring |
| Voomly | pricing fetched (`raw-f0cfdc7f.html`: $19 / $49 / $79 tiers) | Video-first |
| mysimpleshow | terms → Page Not Found | UNVERIFIED |
| Animaker | terms fetched (146 KB) | Video-first |
| Sparkol legal | index page only | UNVERIFIED for output ownership |
| Doodly | see `raw-*` set | Video-first |

### 2.5 AI-image platforms (for the broader rights picture)
- **Stability AI** ToS fetched (28 KB text, `pw-1a171d81.txt`); contains ownership/enterprise language — **not fully reviewed in this draft**.
- **Adobe Firefly / Adobe general terms, Midjourney, Ideogram, Procreate:** **UNVERIFIED — fetch failed** (HTTP2 error / 404 / JS shell). This is the largest hole in the memo and it is stated rather than papered over.
- **Legal backdrop (external, not vendor-specific):** US Copyright Office guidance is that output lacking sufficient **human authorship** is not copyrightable. Consequence: we cannot promise a publisher or sponsor the **exclusivity** they are paying for. This is the reason the sellable line must be hand-drawn.

## 3. Decision rules this memo sets (binding on the pipeline)
1. **Sellable** (merch, publisher submissions, sponsor creative, anything claiming exclusivity) = `traditional` tag **only**. AI/vendor output is inadmissible until a vendor ToS assigns output ownership *to us* in writing, on a paid tier, and a lawyer has read it.
2. **Volume/decoration/free lead-gen** = `programmatic` (our own renderer, clean IP) or an approved vendor `ai` tag.
3. **Never** use a free tier for anything commercial — Recraft §7.1 is the worked example of why.
4. **Seat hygiene:** a real vendor seat uses a real `@zdotllc.com` alias. `@zerric.xyz` is play-side content owners only. `@zdot-dummy.com` is a fictional HubSpot label — never registered, never a vendor seat.
5. **Credentials** live in `communication/credentials.txt`; vendor tokens must never appear in code, job logs, manifests, or git history.

## 4. What is required to make this v1 (and who owns it)
| # | Required input | Owner | Status |
|---|---|---|---|
| L1 | Vendor decision (which product, which tier, seat count) | BossLady (Creative Director) + CEO budget line | **OPEN** |
| L2 | Seat registered on a real `@zdotllc.com` alias; invoice reference + renewal date | Finance | **BLOCKED (no vendor chosen)** |
| L3 | Adobe / Midjourney / Ideogram / Procreate ToS captured | CTO | **RE-FETCH REQUIRED** (blocked by bot challenges + HTTP2) |
| L4 | External legal review before any AI output is sold | CEO/Zerric (funding) | **NOT STARTED** |
| L5 | Style guide revision referenced by the batch manifest | CTO (published: `STYLE-GUIDE-v1`) | **DONE 2026-09-12** |

## 5. Recommendation
**v1 ships with `programmatic` (in-house, owned) + `traditional` (hand-drawn, owned) only.** Defer any vendor doodle-maker purchase until (a) a static-art specialist is identified (the named category is video-first) and (b) L2/L3/L4 are closed. This satisfies the owner's "some of each" intent using *two* owned classes and avoids paying for a rights problem.
