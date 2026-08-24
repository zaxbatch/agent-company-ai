# TEAM-STATE — Live Source of Truth (updated continuously)

> **Purpose:** If this repo/conversation ever reboots or disconnects, read THIS file first
> to pick up exactly where we left off. Every agent updates it at end of turn.
> Auto-refresh: `python3 scripts/save_state.py` (also syncs the portal + git).

**Last updated:** 2026-08-24T06:32:09Z
**How to resume:** 1) read this file  2) read souls/*.md  3) hit the checklist portal
(https://tasks.zdotllc.com, creds in communication/portal_credentials.txt)  4) run
`./venv/bin/python scripts/checklist_watchdog.py` to see who's stale.

---

## 0. LATEST SESSION (2026-08-24b)
- **Games:** FTF deleted by Zerric (glitchy) ✅. NEW: SNOW SNAKE RUSH id83 (manny, endless runner). Vin Negar Bottle Flip id81, Snowball Blitz id80. Others live: Snowball Breakout 82, Iceberg Hopper 79, Snowball Fight 78, Snow Snake 76, UFO Hunter 70.
- **Vin Negar rig v2:** darker ACV amber bottle, gold chain (V pendant), gold-rimmed shades, gold tooth, gold watch, gold-tip kicks — face ON the bottle, no human head. → content/spread-da-word/vin-negar-rig.html
- **Spread Da Word Episode 1 teaser:** content/spread-da-word/episode-1-teaser.html — South Park cutout animation (Snow + Vin Negar), speech bubbles, intro music (intro-music.wav), play/mute. Style = CONFIRMED cutout.
- **zerric.xyz is the focus** (zdotllc.com on hold per BossLady). Need zerric.xyz FTP/repo access to edit.

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
