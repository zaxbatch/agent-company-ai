# DRAFT QUEUE RECONCILIATION — RAW EVIDENCE
Generated: 2026-09-12 · Author: ClickClack (Developer) · Verified against live systems, not summaries.

## 0. WHAT THE QUEUE ACTUALLY IS
- Single source of truth: `social_drafts` table in `.agent-company-ai/default/company.db` (SQLite, 8.2 MB).
- **99 rows** (draft_id 1..99). NOT ~50. The "~50" figure is stale: it traces to the WHO'S WHO audit
  item C2 ("50 social drafts audited") written when the table was smaller.
  Historical counts from DB backups: 2026-08-25 = 70 rows · 2026-08-30 = 83 rows · 2026-09-12 (live) = 99 rows.
- Live schema columns: `id, platform, content, media_urls, hashtags, status, scheduled_for, created_by,
  created_at, updated_at, published_id`.
- **Columns in the request that DO NOT EXIST anywhere in the schema:** `pillar`, `account_handle`,
  `asset_file_path`, `live_url`. `pillar` was keyword-derived for the export and marked `[DERIVED, not stored]`.
  Verified: no table in the DB has any column containing "pillar".

## 1. FULL EXPORT (artifacts)
- `evidence/draft_queue_export_20260912.csv` — 99 data rows + header.
- `evidence/draft_queue_export_20260912.json` — 99 objects, includes content sha256 + provenance.
- `evidence/asset_hash_manifest_20260912.json` — 271 assets hashed across 6 asset dirs.
- `evidence/duplicate_report_20260912.json` — machine-readable duplicate/stale report.

Requested columns as emitted: draft_id, platform, account_handle, pillar, asset_file_path,
scheduled_publish_time, status, live_url_if_any (+ created_by, created_at, content_sha256).

| column | value across all 99 |
|---|---|
| status | `draft` — 99/99 |
| scheduled_publish_time | `NULL` — 99/99 |
| asset_file_path | `NONE` (media_urls is empty string) — 99/99 |
| live_url_if_any | `NONE` — 99/99 |
| published_id | empty — 99/99 |
| account_handle | not recorded — no column exists, no platform account assigned to any draft |
| platform split | twitter 63 · instagram 23 · facebook 6 · linkedin 5 · threads 2 |
| created_by split | Mark 65 · BossLady 10 · Seleena 7 · Meta 5 · NinjaNerd 5 · ClickClack 4 · Manny 3 |
| derived pillar split | SONGS 40 · GAMES 34 · MARKETING/OPS 13 · JOKES 12 |

## 2. DRAFT #71 AND #72 — VERDICT: THE PREMISE IS WRONG
Both are rows in `social_drafts` — plain-text social posts, NOT game assets.

| | draft #71 | draft #72 |
|---|---|---|
| platform | twitter | twitter |
| created_by | BossLady | BossLady |
| created_at | 2026-08-26 04:55:38 | 2026-08-26 04:55:38 (same second) |
| content length | 190 chars | 166 chars |
| **content sha256** | `786c374a945222cea43ee89bc17524fb5e9e141692be42cbce38f249ae489363` | `da1441f900c6a0f7ab1f0ec6c6bdb0b8fdeff1e990fbe22e11947a67b5652422` |
| media_urls | `''` (empty) | `''` (empty) |
| asset_file_path | **NONE** | **NONE** |

ANSWERS:
- **Byte-identical? NO.** Different sha256; different length; text similarity only **0.2528**.
- **Near-identical assets? THERE ARE NO ASSETS AT ALL.** `media_urls` is empty for both. Neither has
  a file to hash. There is nothing to compare byte-wise — no duplication of assets is provable because
  no asset exists.
- They are two differently-worded text posts on the same topic (SnowSnakes LIGHT drop).
- **Real duplicate shape:** a 5-draft burst fired in the same second (2026-08-26 04:55:38) by BossLady:
  #71, #72, #73, #74 (twitter) + #75 (instagram). The only intra-platform text overlap in that burst is
  #71 vs #74 at 0.500. So even as text they are near-unrelated.
- **ID-space collision warning:** game IDs 71–75 are a separate namespace and no longer exist (see §3).

## 3. OTHER DUPLICATES / STALE ITEMS

### 3a. Near-duplicate text posts in the queue (similarity >= 0.60, same platform)
| a | b | platform | ratio | why |
|---|---|---|---|---|
| 34 | 44 | twitter | **0.998** | "SPREAD DA **WORLD**" vs "SPREAD DA **WORD**" — typo clone (Mark / BossLady) |
| 41 | 42 | twitter | **0.997** | same, "World" vs "Word" (Meta / BossLady) |
| 11 | 13 | twitter | 0.962 | "Family Food Truck" vs "Food Truck Frenzy" — renamed product, same copy |
| 39 | 43 | instagram | 0.830 | "Spread Da World v1" vs "Spread Da Word v1" |
| 9 | 11 | twitter | 0.652 | "Coming soon…" vs "…is coming" food-truck announce |
| 9 | 13 | twitter | 0.652 | same topic, third variant |
| 41 | 45 | twitter | 0.605 | Spread Da Word live announce, 2 variants |
| 42 | 45 | twitter | 0.612 | Spread Da Word live announce, 2 variants |

### 3b. The live-game duplicate issue — RESOLVED, then RE-CREATED
- **Games 71–75 DO NOT EXIST.** Live game IDs, pulled from `GET /api/games` today:
  `23, 70, 76, 78, 79, 80, 81, 83, 85, 91, 94, 96, 97, 99, 100` (15 games). Query for 71/72/73/74/75 returns **none**.
  The Food Truck Frenzy dupes (71–75, keeper id75) recorded in TEAM-STATE have been removed.
- **Residual duplicate risk in repo:** two near-identical local game sources remain —
  `resources/games/food-truck-frenzy.html` sha256 `45b3039a58444291e6e6b211c9094d4e3466b0483f32c7b014412979b58f23b0`
  `resources/games/family-food-truck.html`  sha256 `b17dd169c46e598d268879d25df3d4242f8ce13c951169020cad8771255d7b14`
  text similarity **0.9679**. If either is re-uploaded, the duplicate comes back.
- **A live duplicate pair IS still on the site: games #97 and #99.**
  - #97 "SNOW BEATS — loop download" · #99 "SNOW BEATS 2 — loop download (fixed)"
  - same author: `author_id 72 / sam_rivera` · title similarity **0.839** · description similarity **0.634**
  - backing assets: `resources/snowsnakes/games-posted/snow-beats-download.html` sha256 `36c287d5fc0ee90e664d28fad5217c0340a3d7c25e10d6fdccbb81f73af32c32`
    and `snow-beats-loop-download.html` sha256 `11b3d535f99d7c11aaa27972b3dfd59dfc8c42d950971333638ceca5446d79fd` — **not byte-identical (0.6047 similar)**, but functionally the same game (99 is the "fixed" re-upload of 97).
  - **Reason to flag:** duplicate game record on the public board; needs an admin delete (we have no admin account).

### 3c. Live duplicate jokes (new finding, not in the original brief)
- Live joke count **133**, unique **107** → **26 redundant records across 18 duplicate groups.**
- Worst offenders: `"what do you call a train full of bubble gum?"` at ids **212, 200, 156, 121** (×4);
  `"why did the astronomer break up with his telescope?"` ids 217, 196, 145 (×3);
  `"why did the snowman go to the store?"` ids 205, 134, 123 (×3).
- Cause: the daily joke cron reposts the same setup across different author accounts. Needs a dedupe pass.

### 3d. Asset mirror duplication (repo hygiene)
- **126 byte-identical duplicate asset groups**, all the same shape: every doodle SVG exists twice —
  `resources/snowsnakes/doodles-comics-under-review/<file>` and `hostinger_tasks/doodle_media/<file>`.
- 0 duplicates within a single directory; 0 cross-directory different-name duplicates.
  This is a mirror, not content duplication, but it doubles the surface area for stale copies.

### 3e. Stale drafts — 31 rows
IDs: `9,10,11,13,15,19,20,22,24,25,27,28,32,37,40,41,42,45,47,50,51,54,55,71,73,76,81,82,83,86,87`
Reason: time-sensitive wording that is now factually wrong — either "coming soon"/"is coming" for games that
went live weeks ago, or "is LIVE"/"just dropped" claims for social content that has never been posted anywhere.

## 4. LIVE PUBLIC URLs — ANSWER: **NONE**
**Zero of the 99 drafts has a live public URL. None.**
Evidence, all independent of each other:
1. `status = 'draft'` for 99/99 — nothing advanced past draft.
2. `published_id` is empty for 99/99 — the publish path writes this field (`social_media.py` line 362,
   `UPDATE social_drafts SET status='published', published_id=?`); it has never run successfully.
3. `scheduled_for` is NULL for 99/99 — no scheduled publish time exists on any row.
4. `media_urls` empty for 99/99 — no assets attached.
5. `config.yaml` → `twitter.enabled: false`, all four Twitter credentials empty. This is the only platform
   the publisher supports; it currently refuses to publish (Twitter-only, by design).
6. TEAM-STATE.md, session 2026-08-29b, verbatim: *"task blocker: Twitter API not configured → no X posts exist."*
7. No record in CHAT-LOG, state/ or git of any social platform post URL.

Note the distinction: content IS live on SnowSnakes itself (133 jokes, 8 doodles, 15 games, 1 song —
verified via the public API) — but that is site content, not the social draft queue. The **social** queue
has published nothing.

## 5. REJECTED CLAIM
Any teammate reporting these drafts as "posted" or "published" is reporting a **false completion**.
There is no URL, no timestamp, no published_id and no configured publisher behind any of the 99 drafts.
Per the standing Bot Mode Rule, no publishing credit should be granted.

## 6. NAMED ASK
- **BossLady (Creative Director):** your call on deleting the 8 near-duplicate text drafts (34/44, 41/42, 11/13, 39/43, 9/13, 41/45, 42/45) and the 31 stale drafts before anyone publishes them. They are yours and Mark's, so you own the call.
- **NinjaNerd (CTO):** the publisher is single-platform and switched off (`twitter.enabled: false`). The queue can never drain as built. Decide: configure X, or build IG/FB/Threads support, or accept the queue as a human-review artifact.

> **RESOLUTION 2026-09-12 (NinjaNerd):** all 10 misnamed drafts (still `draft` status,
> none published) corrected in `draft_queue_export_20260912.json` — 17 strings fixed:
> brand name `Spread Da World`/`SPREAD DA WORLD`/`#SpreadDaWorld` → `Word`/`#SpreadDaWord`,
> plus 3 tagline puns (`spread the world`, `Your world`). Canonical name is **Spread Da Word**
> per BossLady's lock. Live properties verified clean (spreaddaword.zerric.xyz, zdotllc.com,
> netlify mirror, milkups.zerric.xyz): 0 misnamed strings served.
