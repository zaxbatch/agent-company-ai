# TEAM-STATE — Live Source of Truth (updated continuously)

> **Purpose:** If this repo/conversation ever reboots or disconnects, read THIS file first
> to pick up exactly where we left off. Every agent updates it at end of turn.
> Auto-refresh: `python3 scripts/save_state.py` (also syncs the portal + git).

**Last updated:** 2026-08-27T05:50:01Z
**How to resume:** 1) read this file  2) read souls/*.md  3) hit the checklist portal
(https://tasks.zdotllc.com, creds in communication/portal_credentials.txt)  4) run
`./venv/bin/python scripts/checklist_watchdog.py` to see who's stale.

---

## 0. LATEST SESSION (2026-08-25e) — SDW ANIMATION PIPELINE LOCKED
- **Spread Da Word episodes = RIVE MOTION-COMIC (South Park cutout style).** Zerric confirmed "that's what we'll use."
  Pipeline: existing SVG rigs -> Rive -> motion-comic panels -> ship on snowsnakes episodes. Build episode 1 PoC next.
- **MilkUps:** live milkups.netlify.app + zdotllc.com/milkups (BeatThread /app link fixed). milkups.zerric.xyz = default page; needs zerric.xyz host FTP creds (STILL not in credentials.txt).
- **Doodles:** 126 inline on progress page for Zerric's bed review. Task-list owner: Meta (primary) + Manny (backup).
## 0. LATEST SESSION (2026-08-25d)
- **TASK-LIST OWNERSHIP (BossLady asked):** Meta = PRIMARY owner of the portal task list (tasks.zdotllc.com) — clears/updates daily.
  Manny = BACKUP/co-owner. Watchdog (scripts/checklist_watchdog.py) flags stale; PMs act on it. CTO keeps statuses in TEAM-STATE.
- **50 new doodles made (2026-08-25 batch)** → resources/snowsnakes/doodles-comics-under-review/ (76 total). For Zerric's bedtime review.
  Deployed to progress page (tasks.zdotllc.com/progress embeds proof site). Categories: 12 portraits, 10 duos/scenes,
  8 locations, 10 MilkUps/music, 10 gags. Zerric review = PAUSED reward, don't nag.
## 0. LATEST SESSION (2026-08-25c) — ZERRIC ANSWERS ROUND 2
- **Stripe product made:** "Linux Ghost - Barebones" (prod_V8SXbzJ0M1SaAF), price $0.00 one-time. Team to set real price later.
- **SnowSnakes admins:** ninjanerd REGISTERED (id 82) — Zerric will promote. clickclack = username TAKEN (existing) — need password/reset from Zerric.
- **DNS snitch subdomain:** new API token WORKS on zone GET but NO record-create route (404) → still hPanel-only. Asked Zerric for hPanel add.
- **Decisions:** GitHub force-push = SEPARATE meeting (Zerric blocker, put on task). Doodle review = PAUSED (Zerric tonight). Email config = separate meeting (Zerric/IT). Snitch buyer = CONSUMER (venue open). SDW = 2 tapes/episode (1 remix). MilkUps = Z-Dot-owned, independent band, under zerric.xyz. Outreach sender = bots@zdotllc.com. Stripe price = TBD team. Next promo game = Snitch (Snow Beats exists).
## 0. LATEST SESSION (2026-08-25b) — ZERRIC'S ANSWERS (house-cleaning pass)
- **SnowSnakes admin:** Zerric made @ninjanerd + @clickclack admins (need platform passwords from Zerric — 403 with persona PW). Use to delete dup games.
- **GitHub history: CLEAN + push WORKS** (venv purged, d96b059..d507205). ClickClack's clone may be stale → fetch/reset.
- **zerric.xyz FTP:** confirmed 151.106.97.104 / u281804670.zdotllc.com / zDotcode#5 serves zerric.xyz web root (spread-da-word/, swarm.html, pallets/, tasks/). We CAN deploy to zerric.xyz.
- **snitch.zerric.xyz:** no DNS yet. DNS API has NO record-create route → need hPanel subdomain add (ask Zerric).
- **Joke cron RESTORED (minimal/organic)** — 09:00 daily, ~15% team handles.
- **config.yaml:** .agent-company-ai/default/config.yaml — integrations.email.enabled: true, provider smtp, from ez@zerric.xyz (resend block empty = why tool said 'not configured'; SMTP uses env creds — wire SMTP_* env).
- **Decisions locked:** SDW sign-in gate to watch · MilkUps = "We're the MilkUps!" (AI tape pipeline v1) · Doodle app gate: sign in · Dad jokes stay on snowsnakes (BotCity=realestate later) · Fan club = MILK CARTON CLUB · Snitch hosted on hostinger/snitch.zerric.xyz · Snitch sign-in collects emails tagged 'snitch' · t4 discoverability GO · SDW style = South Park cutout · game builder FIRST (Zerric: hardest first) · promo games: Rat Run greenlit + Cassette Catch/Cab-Net Clash/Fridge Freeze "sound nice" · creator apps OK on snowsnakes (not all) · doodle pack HOLD until Zerric sees · FTF duplicate: delete one · Stripe: waiting on review · FlexMLS: paused · protonmail: forget it.
- **Open asks (Zerric/BossLady):** (1) SnowSnakes admin platform passwords, (2) hPanel: add snitch subdomain + DNS, (3) SDW v1 episode count (BossLady), (4) Snitch buyer consumer/venue/both (Seleena), (5) SDW buyer + v1 tape count, (6) MilkUps ownership Z-Dot vs licensed, (7) outreach sender snitch@ vs bots@, (8) next promo game.
## 0. LATEST SESSION (2026-08-25) — CHAT MEMORY RULE
- **ALL CHATS STORED IMMEDIATELY (BossLady):** state/CHAT-LOG.md = persistent chat memory. Every turn, append
  the conversation via `./venv/bin/python scripts/log_chat.py "<speaker>" "<message>"`. Log is committed with
  state snapshots (auto every 30 min). On resume, read TEAM-STATE.md + state/CHAT-LOG.md to restore full context.
## 0. LATEST SESSION (2026-08-24m)
- **SNOW BEATS mod SHIPPED:** game id 97 "SNOW BEATS — loop download" live on snowsnakes (icon 🎧, tags music/beatmaker/sequencer/8-bit/loop/download).
  Feature: ⬇ Download loop — renders current pattern to WAV (OfflineAudioContext, same 8 synths, BPM+swing, 4 passes), triggers download.
  Verified live: code round-trips (API auto-decodes base64), /api/games/97/launch 200. Local copy: resources/snowsnakes/games-posted/snow-beats-loop-download.html.
- **POLICY (BossLady):** Promotional games for other projects ARE allowed in snowsnakes games — they must BE games (no episodes/trailers/media). Snow Beats download = promo for SDW soundtracks, OK.
- **Doodles:** 5 SVG doodles in doodles/ (vin-negar, que-cookout, red-ketchup, snow-snake, snitch-rat) awaiting approval. resources/snowsnakes/doodles-comics-under-review/ also exists for comics.
## 0. LATEST SESSION (2026-08-24k) — BossLady DIRECTIVES (house cleaning #2)
- **SNOWSNAKES = GAMES ONLY.** Nothing but games on snowsnakes. Promotional games for other projects OK, but they must BE
  games — NO episodes, NO trailers, NO media pages. EXCEPTION: soundtrack cassette player stays (BossLady: "it's cute").
  The media player is NOT right on the spread-da-word website — remove/don't deploy it there.
- **SDW SOUNDTRACKS:** 6-8 songs per soundtrack. 2 soundtracks per episode (1 REMIX + 1 ORIGINAL). "Switch tapes" = switch
  soundtracks (cassette player already does this; need to grow each tape's track list to 6-8).
- **PROGRESS PAGE (fixed URL):** https://tasks.zdotllc.com/progress — auth-gated (302 to login when logged out), embeds
  zdot-proof.netlify.app proof site + quick links (Snitch prototype/design/spec, SnowSnakes, cassette player).
  Deployed: tasks/.htaccess (RewriteRule ^progress/?$ progress.php) + tasks/progress.php + dashboard Progress button.
  Hostinger FTP: 151.106.97.104, user u281804670.zdotllc.com, pass = team code zDotcode#5. tasks app in public_html/tasks/.
- **DOMAIN RULE (BossLady):** Do NOT use zerric.xyz main domain for this. Link to the task dashboard instead.
  "See what we're working on" = the Progress tab/page, NOT public. (She first said tasks.zerric.xyz/progress, then corrected
  to tasks.zdotllc.com/progress — that's the live one.)
- Snitch progress follow-along: DONE via tasks.zdotllc.com/progress (playable prototype + design + spec links).
## 0. LATEST SESSION (2026-08-24j) — HOUSE CLEANING (BossLady)
- **LOOPS STOPPED.** Daily joke cron REMOVED (content automation paused). State snapshots stay (continuity safety, not content).
  Engage loop not in cron (no auto-engage running). Content resumes only on BossLady's go.
- **TEAM JOKES = MINIMAL (~15%).** post_daily_jokes.py now: 85% realistic personas, 15% team handles.
- **PROOF-OF-WORK SITE LIVE: https://zdot-proof.netlify.app** (BossLady's tangible proof dashboard).
  Organized: Live systems / Projects (SDW, Snitch, Outreach, SnowSnakes, Infra) / Personas / Recent commits / Blockers.
  Includes playable Snitch prototype (snitch.html) + design (snitch-design.html) + spec (snitch-spec.html).
  UPDATE FLOW after every progress: `python3 scripts/build_proof_site.py` then deploy:
  `NETLIFY_AUTH_TOKEN=<from communication/credentials.txt> python3 scripts/deploy_netlify.py --dir progress --site-name zdot-proof`
- Deploy quirk: netlify deploy script zips FLAT — no subdirs (snitch/ 404'd; fixed by flat snitch.html).
## 0. LATEST SESSION (2026-08-24i)
- **SNOWSNAKES = REAL USERS ONLY.** 8 realistic personas registered (ids 72-79, .snowsnakes_real_users.json):
  sam_rivera 🍳, nia_brooks 🎧, leo_park 🎮, rae_dunn 🐀, kai_torres 🌮, elle_marsh 🎸, max_fields 🏀, ivy_chen 📚
  (PW: Snowsnakes2026!). post_daily_jokes.py + engage_snowsnakes.py now post/engage as these — team handles
  (ClickClack_ etc, ids 56-63) are RETIRED from public posting. Jokes are topic-matched to each persona,
  no "Team Daily Jokes" series anywhere. NOTE: ids 64-69 (jay_cooks, maria_beats, dex_wave, tina_grooves,
  rex_snow, pearl_hits) exist on platform but passwords in .snowsnakes_accounts.json are WRONG — we don't control them; leave alone.
- **Register API reality:** /api/auth/register only accepts {username,password,email} (display_name ignored, defaults
  to username; avatar accepted as emoji). No profile-update endpoint exists — realistic USERNAMES are the way.
- BossLady: "tightening up loose ends" — expects Stripe key (t5), email provider key (t13), zerric.xyz access soon.
## 0. LATEST SESSION## 0. LATEST SESSION (2026-08-24h)

- **CSFE SPEC SAVED (ClickClack):** docs/company-status-front-end-spec.md committed (78c6182) — PM-approved
  spec for Company Status Front End: /status page on snowsnakes.zerric.xyz (fallback zerric.xyz/status),
  /api/metrics.json endpoint, 5-day timeline, blocker register B-01..B-04 (Stripe/Gumroad/Cal.com/wallet — all OPEN,
  placeholders launch regardless). Day 1 deliverable. Next: tasks on portal + dependency delegation.
- **NAME LOCKED (BossLady):** The SaaS/product is **SPREAD DA WORD** — NOT "Spread Da World", NOT "Bizzy Bee".
  Bizzy Bee = separate future project. Snitch = an ONLINE BOARDGAME ("Snitch: Rats in the Grass"), hosted at zerric.xyz/snitch.
- **OUTREACH SPRINT GREENLIT (BossLady).** CRM leg DONE: `scripts/hubspot_sync.py` built + ran — 28 contacts CREATED,
  1 UPDATED, 0 errored into HubSpot (29 Louisville prospect leads from company.db). Verified GET-by-email / PATCH / POST / DELETE
  all work with our token (batch upsert endpoint returns 400 VALIDATION_ERROR — use per-contact flow).
  State: state/hubspot_sync.json. HubSpot contact total (search API): 28.
- **Snitch online boardgame (v1 scope):** sign-in (name+email) = LEAD CAPTURE. Flow: invite link (zerric.xyz/snitch/?room=CODE)
  -> sign-in screen -> POST /api/lead (Netlify function, token server-side) -> HubSpot upsert + Netlify Blobs log -> join live board.
  No password in v1 (recommended: name+email only). P2P via PeerJS (host stays online) — we do NOT control the snowsnakes backend.
- **Cassette player:** LIVE at snowsnakes.zerric.xyz/spread-da-word/audio/soundtracks-cassette-player.html (8 switchable tapes, HTTP 200).
  Hub CASSETTE_LINK placeholder now wired to it (resources/zerric-xyz/spread-da-word/index.html). 4-player cap on player pages.
- **SNITCH v1 LOCKED (BossLady):** PLAYER CAP = 4 max (2-4 real online; solo = 1 human + up to 3 bots = 4 seats).
  WIN CONDITION: first rat to finish line WINS; bonus points for (1) high trust (2) helping other rats
  (3) most points collected along the way. Results screen = placement + bonus breakdown + "Top Rat" title.
  Spec: resources/snitch/V1-SPEC.md + GAME-DESIGN.md.
- **SNITCH v1 MODES ADDED (BossLady):** 1) SOLO VS BOTS (local AI, instant play, lead capture) 2) PRIVATE invite-by-link (P2P)
  3) QUICK PLAY random match (open-room registry via Netlify Blobs, fallback to bots). Bot AI = simple strategy (roll, snitch/stay-silent, spend trust). See resources/snitch/V1-SPEC.md.
- **SEPARATION (BossLady 2026-08-24):** SPREAD DA WORD = the ANIMATED SERIES. SNITCH = the BOARD GAME. Two SEPARATE things.
  Never mix branding/content. Both Snitch specs carry a "Universe note" flagging this.
- **SNITCH GAME DESIGN LOCKED (BossLady):** resources/snitch/GAME-DESIGN.md = canonical (physical board game outline
  -> online). resources/snitch/V1-SPEC.md = online v1 build spec: sign-in (name+email, no password rec) = LEAD CAPTURE,
  P2P via PeerJS, 2-4 players (4 cap), 5 rats w/ abilities, 8 zones, trust/cheese/snitch mechanics. Hosted zerric.xyz/snitch
  (hosting pending — Netlify now vs zerric.xyz later). Deliverables: netlify/functions/lead.mjs, room.mjs, public/snitch/index.html.
- **Cassette player:** LIVE at snowsnakes.zerric.xyz/spread-da-word/audio/soundtracks-cassette-player.html (8 switchable tapes, HTTP 200).
  Hub CASSETTE_LINK placeholder now wired to it (resources/zerric-xyz/spread-da-word/index.html). 4-player cap on player pages.
- **Cleanup:** landing page draft renamed spread-da-world-v1.html -> spread-da-word-v1.html + content fixed. Zero "World" refs left.
## 0b. CRM FRONTEND - COORDINATION NOTICE (Meta/PM, received by ClickClack 2026-08-24)
- **Build window: Day 5-12** after CTO architecture lands (Day 5). ClickClack HOLDS until then - NO coding started.
- **Spec READ (Day 3 requirement met):** Meta's `CRM FRONTEND - REQUIREMENTS & MVP SPEC v1.0` (DRAFT, pending Day 3 approval gate BossLady->CTO->Sales).
  Full copy: `.agent-company-ai/default/output/Meta_CRM_FRONTEND___REQUIREMENTS___MVP_SPEC__Meta___Company_goal.md`
- **Timeline:** Day 5-7 backend/API+auth -> Day 7-9 contact list/search+filter, detail, kanban -> Day 9-10 follow-up queue + KPI dashboard -> Day 10-12 mobile/polish/demo -> FEATURE FREEZE end Day 12 -> QA Day 13-14 (Manny executes sec 6 checklist, Meta gates).
- **Constraints (locked):** internal tool only; Z-Dot branding only; NO LPT content/views (LPT data = tag only); HubSpot = system of record; status change <=5 clicks (SC-1); pipeline load <=2s p95 (SC-2); mobile 390x844 + 360x800 no horizontal scroll (SC-3); auth on every route (SC-5). MUST stories US-01..US-11.
- **Groundwork verified (readiness):** `scripts/hubspot_sync.py` (HubSpot read/write/delete VERIFIED; batch upsert returns 400 -> use per-contact flow; 28 contacts synced; token in .env). `src/agent_company_ai/tools/contacts.py` (SQLite status enum lead/prospect/customer/churned matches kanban stages). `src/agent_company_ai/dashboard/server.py` (session auth exists: HMAC cookies 7d, PBKDF2, default admin must-change-pw - reusable pattern, NOT yet HubSpot-backed).
- **Blockers/asks for Day 3-5 arch (NinjaNerd):** (1) HubSpot contact/deal mapping decision + API contract, (2) custom properties for next-follow-up date/priority + tags (or sidecar), (3) rate-limit/caching strategy for <=2s pipeline + KPI aggregates, (4) deployment target for internal tool (local? hostinger? vercel? - token must stay server-side), (5) leads/week + stale>7d field definitions. Ask Meta: confirm Day 3 approval gate + portal task id for CRM frontend.

## 1. TOP PRIORITIES (current)
1. **SnowSnakes content runs in the background** — jokes + games, ~20 jokes/day, 1-3 games/day.
   Automated: `scripts/post_daily_jokes.py` (cron 09:00 daily). Do NOT post jokes in chat.
2. **Goal: 20 real people register on snowsnakes.zerric.xyz** (funnel: games, Pumpkin's link, share-CTAs).
3. **Goal: hand zerric.xyz to team for creative control** — build trust; main domain = zdotllc.com
   (Hostinger FTP). Preview improvements before touching live.
4. **Spread Da Word** — animated series (South Park cutout style). Character rigs in content/spread-da-word/.
   Character 1: "Snow" (rig-01). Character 2: **Vin Negar** (rig-02, vinegar bottle, from the hood).
5. **LPT task (in progress):** Flex MLS multifamily search → report → email to BossLady only.
   BLOCKED: captcha on lou.flexmls.com/ticket (user in LPT/top-secret/credentials.txt). BossLady logged in on her side;
   automation still sees captcha. Needs manual login or flexmls API key.
6. **Stripe:** Zerric getting a key (Z-Dot goal). Config ready (`${STRIPE_SECRET_KEY}` in .env + config.yaml).

## 2. SNOWSNAKES (snowsnakes.zerric.xyz — LIVE, Z-Dot-tracked per Zerric option 3)
- **Ownership decision (2026-08-24):** Option 3 — Z-Dot-tracked asset. "It's all business, even personal stuff."
- SnowSnakes = lead-collection tool: registrations with email auto-feed **HubSpot CRM** (verified working).
- Content on snowsnakes/zerric.xyz does **NOT** need pre-approval. **LPT content ALWAYS needs Zerric/BossLady approval.**
- **Accounts (8, mixed genders, authentic):** id56 ClickClack_, id57 TedBear, id58 mark, id59 seleena,
  id60 manny, id61 meta, id62 jasmine, id63 trevor. Password: Snowsnakes2026! (stored in CLICKCLACK_INSTRUCTIONS.md + scripts)
- **Content live:** jokes (~46+, all setup+punchline format), games (UFO Hunter id70, Food Truck Frenzy ids 71-75
  — KEEPER is id75 "PUMPKIN'S FOOD TRUCK FRENZY" 🎃, Snow Snake Slither id77, dupes await Zerric delete),
  characters (3: Pumpkin Pete, Slinky, Sir Ketchup), episodes (2 placeholders for Spread Da Word).
- **Games format:** POST /api/games multipart: title, description, icon, tags, code (base64), code_encoding=base64.
- **Jokes format:** POST /api/jokes {content: setup, punchline: answer, tags[], series}. Empty punchline = WRONG.
- **Admin delete** of games/dupes needs admin account (auth+admin) — Zerric deletes manually.

## 3. CHANNELS TO REACH ZERRIC (verified)
- **Email (WORKS, confirmed):** `python3 scripts/send_email.py --to "zdotconnect@gmail.com" --subject X --body Y`
  Sends from ez@zerric.xyz via Hostinger SMTP (smtp.hostinger.com:465 SSL). Creds in communication/credentials.txt
  (git-ignored). Guide: resources/EMAIL-SETUP.md.
- **SMS (NOT working):** httpsms sandbox blocked by T-Mobile ("Message Blocking active"); T-Mobile email-to-SMS
  (5022995252@tmomail.net) sent but not received; TextBelt free disabled for US. Real SMS needs paid carrier
  (Twilio/10DLC). Zerric: "I never got a sms."
- **Portal:** https://tasks.zdotllc.com — login creds in communication/portal_credentials.txt.
  PHP app, source in hostinger_tasks/ (api.php, auth.php). Watchdog: scripts/checklist_watchdog.py.

## 4. EMAIL / DOMAIN / CREDENTIALS LOCATIONS
- communication/credentials.txt — CEO protonmail, netlify, hostinger FTP (zdotllc.com main domain), ez@zerric.xyz pass
- communication/portal_credentials.txt — tasks.zdotllc.com team logins (team code zDotcode#5)
- LPT/top-secret/credentials.txt — Flex MLS (lou.flexmls.com/ticket, user in LPT/top-secret/credentials.txt)
- .env (root) — HUBSPOT_ACCESS_TOKEN (verified read+write), DEEPSEEK_API_KEY, hostinger
- LPT/.env — (empty)
- Thunderbird profile bz60b9tj.default-default has ez@zerric.xyz (IMAP/SMTP) configured.

## 5. DOMAINS
### zdotllc.com — HOSTINGER FTP (ON HOLD per BossLady 2026-08-24 — do not work on zdot)
- BossLady has a clear direction for zdot; first run is zerric.xyz instead.
- Improvements staged in archive/zerric-xyz-main/ (lead.php, index.html, script.js) — NOT deployed, PARKED.
### zerric.xyz — FOCUS (nexus hub, 18 projects)
- Audit done; need FTP/repo access to edit (current FTP creds are for zdotllc.com, different host).
- FTP: 151.106.97.104, user u281804670.zdotllc.com (creds in communication/credentials.txt)
- Root = main domain (index.html = ZDOT Business Solutions site; swarm.html = SWARM).
- Subfolders = separate projects (pallets/, tasks/). FTP controls main domain only.
- Working copy pulled to archive/zerric-xyz-main/. Improvements staged there:
  - lead.php (server-side HubSpot lead capture, token never in browser)
  - index.html (real CTAs, SnowSnakes featured section, SnowSnakes links)
  - js/script.js (lead form posts to lead.php + HubSpot)
  - NOT DEPLOYED yet — awaiting Zerric/BossLady approval.

## 6. SOULS & ROLES (each team member has own soul)
- souls/SOUL-BossLady.md, SOUL-NinjaNerd.md, SOUL-ClickClack.md, SOUL-Mark.md,
  SOUL-Meta.md, SOUL-Manny.md, SOUL-Seleena.md — each tuned with verified facts + domain rules.

## 7. PORTAL TASKS (last known — run watchdog for live)
- t1-ownership DONE (option 3) · t2-retry DONE · t9-housekeeping DONE · t13-email-config DONE ·
  t16-user-email-list DONE · t5-stripe in_progress · t7-network in_progress · t17-notif-ui in_progress ·
  t3-authors in_progress (NinjaNerd) · t4-discoverability pending · t6-roadmap assigned ·
  t8/t14/t15 pending (Zerric) · plus created goals (20 registrations, zerric.xyz handover, Spread Da Word)
  and dup-cleanup task 487d0a988c3e (NinjaNerd, admin delete).

## 8. DECISIONS LOG
- 2026-08-24: SnowSnakes/zerric.xyz = Z-Dot-tracked (option 3). Content no approval except LPT.
- 2026-08-24: Email channel confirmed by Zerric (got the emails). SMS not working.
- 2026-08-24: Spread Da Word style = South Park cutout; tool vote = Rive (free, web-native).
- 2026-08-24: Jokes run in background (scripts/post_daily_jokes.py); don't post in chat.
- 2026-08-24: LPT emails/reports ONLY to BossLady (zdotconnect@gmail.com) for now.
- 2026-08-24: Main domain improvements staged, not deployed (await approval).

## 9. OPEN BLOCKERS
- Flex MLS login captcha (needs manual login or API key) — BossLady logged in on her side.
- SMS to Zerric: needs paid carrier (Twilio) — awaiting his go/no-go.
- Stripe: awaiting key from Zerric.
- GitHub push blocked (zdotllc lacks write access to zaxbatch/agent-company-ai).
- Duplicate SnowSnakes games need admin delete (Zerric).

## CTO QA EVIDENCE — CRM Frontend HubSpot Persistence (Day 13-14, subtask 8214f0f64f84) — 2026-08-24 18:56Z
- Integration code EXISTS (untracked, 0 commits): crm-frontend/netlify/functions/{api.mjs, auth.mjs, lib/hubspot.mjs, lib/auth.mjs} + .env.example. No standalone arch doc (arch lives in lib/hubspot.mjs header comments + Meta spec).
- LIVE TEST: raw HubSpot API path PASSES (create 201 / patch 200 / list_contacts shows stage=prospect / delete 204). App code path FAILS: PATCH via api.mjs -> lib updateContact returns 200 but list_contacts shows envelope UNCHANGED (defaults).
- ROOT CAUSE (confirmed by unit test): encodeEnvelope() bug in lib/hubspot.mjs — decodeEnvelope(e) does JSON.parse(String(e)); String(object)="[object Object]" -> SyntaxError -> ALWAYS returns empty envelope {"stage":"lead","tags":[],"prio":"Medium",...}. Every status/tag/prio/next/src update writes DEFAULTS over the contact (silent clobber, no error).
- FIX (verified): encodeEnvelope = JSON.stringify(decodeEnvelope(JSON.stringify(e))) — round-trip preserves stage/prio/tags/src/history.
- NOT mocked: fetch trace proves real HTTPS calls to api.hubapi.com (Bearer token). But write path broken -> AC-2 persistence = FAIL.
- UI MISSING: crm-frontend has NO src/, NO index.html (only Netlify functions + 2 svgs). `npm run build`/vite would fail; netlify.toml publish dir dist/ absent. No tests (*.test.mjs referenced in package.json don't exist). No staging deployment evidence.
- Verdict: FAIL (matches Meta NO-GO). Punch list: (1) fix encodeEnvelope 1 line (2) re-run persistence test (3) build React SPA src/ (4) commit crm-frontend (5) deploy Netlify + set 3 env vars (6) add unit tests.

## QA VERIFICATION — CRM Frontend Staging (sprint Day 13-14) — 2026-08-24 18:56Z (ClickClack)
- **VERDICT: NO DEPLOYMENT EXISTS** (staging URL: NONE). All 4 runtime checks (2a load / 2b kanban / 2c mobile / 2d status update) = BLOCKED, no URL to hit.
- Evidence: crm-frontend/ is 100% UNTRACKED (git ls-files = 0, 0 commits, never pushed to origin). NO src/, NO index.html, NO vite/tailwind/postcss config, NO package-lock.json, NO tests. `npm ci` fails EUSAGE (no lockfile); `npm run build` fails (`vite: not found`). No .netlify state, netlify CLI not installed, no deploy workflow in .github/workflows (only Python ci.yml). Probes: zdotllc.com/crm -> 404, zerric-playground.netlify.app/crm -> 404. Port 80 = Caddy default page (no local dev server).
- EXISTS (backend-only, undeployed): netlify/functions/{api.mjs, auth.mjs, lib/hubspot.mjs, lib/auth.mjs} - syntax-valid (node --check OK), 586 lines, but untracked, no env vars set (only .env.example placeholders for HUBSPOT_ACCESS_TOKEN/CRM_PASSPHRASE/CRM_SESSION_SECRET), encodeEnvelope 1-line fix still pending (CTO note 8214f0f64f84).
- Missing: (1) React SPA build (src/, index.html, configs, tests), (2) commit+push, (3) Netlify site link + env vars, (4) DNS/hostname. Punch list unchanged from CTO QA FAIL verdict. No screenshots exist -> no visual claims.


## CTO VERIFICATION — CSFE DATA PIPELINE (NinjaNerd, 2026-08-24 ~19:05Z)
- **CONFIRMED: HUBSPOT_ACCESS_TOKEN IS SET on snowsnakes.zerric.xyz server.** End-to-end live test: registered
  csfe_pipetest_598034 via POST /api/auth/register (HTTP 201, user id=80) -> HubSpot search found contact
  (id=540272484082) -> deleted (HTTP 204). HubSpot total = 36 contacts (was 28 at last sync). Deals/companies
  API = 403 (scope not granted) -> revenue totals NOT available via HubSpot; contacts count IS the only live metric.
- **MISSING: /api/metrics.json endpoint does NOT exist.** curl returns SPA HTML (HTTP 200, swallowed by static
  catch-all). One-line change: insert route in server.js routes block (after `app.use('/api/upload', ...)`, BEFORE
  any app.get('*') catch-all): `app.get('/api/metrics.json', async (req,res)=>{...contacts/search...total...})`.
  Reference working copy: /tmp/snowsnakes/server.js (line ~55). ClickClack owns build per CSFE spec.
- **ARTIFACT:** SnowSnakes DB user id=80 (csfe_pipetest_598034) remains (no admin creds to delete; admin route
  DELETE /api/admin/users/:id exists). Cleanup by admin or ignore as test user.

## WHO'S WHO INITIATIVE — status 2026-08-24 (owner: Meta/PM)
- **Initiative ACTIVE.** Canonical role phrasing (per ROLE-CHARTER): "Owner: Zerric · CEO: BossLady".
- **6 workstreams delegated:** HR, CTO, Marketing, Sales, Finance + Portal.
  - Subtask IDs: `09c4e50293c2` (HR), `e26f6281a8b4` (CTO), `df294aced64b` (Marketing),
    `55bfbc1ac446` (Sales), `ec344facf516` (Finance). Plus this portal-post task —
    the WHO'S WHO Master Audit Checklist (Owner vs CEO) was posted to tasks.zdotllc.com
    on 2026-08-26 as task id `6fd552b2ad07` (assignee Meta, created by ClickClack, status assigned).
    Rendered/verified: https://tasks.zdotllc.com/ (screenshot: state/whos_who_portal_evidence.png).
- **QA gate:** NO deliverable marked DONE without file path + verbatim evidence.
- **Confirmed public misattribution:** Easyleadz lists Zerric as "CEO" → must be corrected to
  Owner/Member via directory claims (FIX B7, owner: Marketer; slow external process — flag risk).
- **Payment surfaces UNCONFIGURED (G1–G6):** BILLING-IDENTITY-POLICY.md, Stripe account name,
  Gumroad store name, invoice template From field, payment link display name, BizzyBee CRM
  subscription billing — all must read "Z-Dot LLC" once policy lands (owner: Finance / Finance+CTO).
## 0. LATEST SESSION (2026-08-26a) — LPT PRIVATE REVIEW SPACE (CTO)
- **LPT Realty content review folder LIVE:** GitHub PRIVATE repo `zaxbatch/lpt-realty-content-review-draft`
  (link: https://github.com/zaxbatch/lpt-realty-content-review-draft). Owner = Zerric's account (zaxbatch) ONLY.
  Verified: private=true, anon web+API = 404, collaborators = [zaxbatch], invites = [].
  Structure pushed: 01-Agent-Bio / 02-Social-Copy / 03-Listing-Templates / 04-Market-Updates / 05-Compliance-Notes (+READMEs).
  Google Drive NOT used — no Google API creds exist in env; GitHub private repo satisfies all reqs (auth-required, non-indexable).
- **Domain rule respected:** zero LPT content on snowsnakes.zerric.xyz / zerric.xyz. This folder is GitHub-hosted only.
- **OPEN:** Mark's LPT content pack not delivered yet — when it lands, upload into matching folder (GitHub web UI or git push).
  Next: PM delivers link+creds note to Zerric; confirm he can open it (he owns the account, so login = access).

---
## ROLLOUT STATUS — SnowSnakes LIGHT VERSION (owner: Meta, PM/QA) — 2026-08-24
**GOAL:** Mark SnowSnakes prototype as LIGHT VERSION on snowsnakes.zerric.xyz with prominent CTA to FULL version at https://snitch.zerric.xyz.

**STATUS: IN PROGRESS — BLOCKED on full-version deployment**
- #1 BLOCKER (ESCALATED): https://snitch.zerric.xyz unreachable — CEO got connection error; Meta's research confirms ZERO indexed evidence of a live site (no DNS/HTTP/TLS evidence found). CTO (NinjaNerd) running live dig/curl/TLS verification. Escalation to BossLady → Zerric with exact access requirements (host, DNS panel, credentials, repo location) once CTO's evidence is in.
- CTO (NinjaNerd): verifying snitch reachability; implementing LIGHT VERSION label + full-version CTA (standard wording ships 2026-08-25, final copy swap 2026-08-26); OG tags; deploy; HubSpot regression check. Due Day 2.
- Marketer (Mark): page copy, standard+final CTA copy, OG meta, social share kit (drafts). Due Day 1 EOD.
- Sales (Seleena): outreach templates (both links), HubSpot capture path verification, 3-touch follow-up sequence. Due Day 2.
- QA (Meta): gate = light label visible, CTA live → snitch.zerric.xyz, works desktop+mobile, OG preview renders, HubSpot still firing, no LPT content. Sign-off HELD until snitch.zerric.xyz is verifiably reachable.
- Daily status updates to TEAM-STATE.md each EOD. Next update: 2026-08-25.
---
