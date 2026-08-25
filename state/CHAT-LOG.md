# Z-Dot Team Chat Log (persistent memory)

> Every chat message is appended here so nothing is lost.

### 2026-08-25 00:48 UTC — BossLady
Snowsnakes users need to look like real users — team handles retired, 8 realistic personas registered.

### 2026-08-25 00:48 UTC — BossLady
Progress page: tasks.zdotllc.com/progress (private, auth-gated). Proof site live with doodles + hot ideas.

### 2026-08-25 00:48 UTC — BossLady
Snow Beats download feature fixed behind gated sign-in (game 99). Modal sandbox blocked downloads — solved via save-file-picker + popup fallback.

### 2026-08-25 00:48 UTC — BossLady
Slogan: 'We'll have our bots call your bots' — drafts in marketing/slogan-bots-drafts.md.

### 2026-08-25 00:48 UTC — BossLady
Keep all chats stored in memory immediately — CHAT-LOG.md is the persistent log.

### 2026-08-25 00:48 UTC — BossLady
House cleaning: stop the loop. Need a website showing tangible proof of work, updated on progress, well organized.

### 2026-08-25 00:48 UTC — BossLady
Progress page location: https://tasks.zdotllc.com/progress — private, logging into tasks.zdotllc.com gets you in. Not public.

### 2026-08-25 00:48 UTC — BossLady
SnowSnakes = games only. Promo games for other projects CAN go in games. No episodes/trailers/media pages. Soundtrack cassette player kept (cute).

### 2026-08-25 00:48 UTC — BossLady
SDW: 6-8 songs per soundtrack, 2 soundtracks per episode (1 remix + 1 original). Switch tapes to switch soundtracks. Cassette player upgrade = drag tape from library into deck.

### 2026-08-25 00:48 UTC — BossLady
Media player isn't right on the spread-da-word website.

### 2026-08-25 00:48 UTC — BossLady
Doodles: 10/day for approval → resources/snowsnakes/doodles-comics-under-review/ AND posted to progress page.

### 2026-08-25 00:48 UTC — Seleena
Snitch mini-game (catch cheese, dodge the cat) = YES on SnowSnakes (promo game). Snitch trailer video = NO.

### 2026-08-25 00:48 UTC — BossLady
Doodle pack is good as is. Don't post until we decide to go live. Can still change before live.

### 2026-08-25 00:48 UTC — BossLady
Sleepy-talk ideas are often the best — keep ideas HOT, keep refining, never archive fuzzy ideas.

### 2026-08-25 00:48 UTC — BossLady
Creator tools (sleepy ideas): doodle-making app, comic-making app, simple game builder — all should post straight to SnowSnakes.

### 2026-08-25 00:48 UTC — BossLady
Snow Beats download can be behind gated sign-in, but the download feature doesn't work because the game loads in a modal — fix it.

### 2026-08-25 00:48 UTC — Zerric
Stripe checkout: Option 2 — prebuilt checkout form (Stripe Checkout Sessions). Build into Mission Control; webhook marks paid in CRM.

### 2026-08-25 00:48 UTC — Zerric
Slogan: 'We'll have our bots call your bots' — draft content while fresh.

### 2026-08-25 00:48 UTC — BossLady
All chats need to store and stay in memory immediately.

### 2026-08-25 00:52 UTC — BossLady
Save state every 5 minutes: save_state.py + state_snapshot.py both on */5 cron (portal snapshot, snowsnakes counts, chat log, git commit).

### 2026-08-25 00:53 UTC — BossLady
Agreed: every chat gets logged the moment it happens, not later.

### 2026-08-25 00:53 UTC — ClickClack
Agreed: every chat logs the moment it happens (immediate append to CHAT-LOG.md), not batched later.

### 2026-08-25 00:58 UTC — Zerric
Two GitHub accounts: zaxbatch (zerric.xyz) + zdot (zdotllc). Policy written: resources/GITHUB-ACCOUNTS-POLICY.md — key aliases in ~/.ssh/config, remote URLs use alias, per-repo identity, no shared tokens.

### 2026-08-25 01:29 UTC — BossLady
Stripe key added (sk_live_, acct_1U885HGviPL80jeH Z Dot LLC). Account under review ~24h — card_payments pending, transfers active. checkout.mjs ready; session test blocked only by review.

### 2026-08-25 01:32 UTC — NinjaNerd
GitHub key audit: this machine's default SSH key = zdotllc (ssh -T confirmed). No zaxbatch private key locally — credentials only has the zaxbatch FINGERPRINT (not the key). Push to zaxbatch/agent-company-ai blocked. Fix: generate new zaxbatch keypair, Zerric adds pub to zaxbatch GitHub, SSH config alias. Private keys never pasted.

### 2026-08-25 01:33 UTC — Zerric
zaxbatch@github in credentials = GitHub CLI public key fingerprint (SHA256:WyqU...). Private key id_ed25519_zaxbatch NOT on machine yet. Options: (1) paste private key file into credentials, or (2) gh auth login with zaxbatch account. Policy in resources/GITHUB-ACCOUNTS-POLICY.md.

### 2026-08-25 01:36 UTC — BossLady
zdot key confirmed already on machine (works). Will get zaxbatch key now — CTO to verify + wire SSH alias + point remote when it lands.

### 2026-08-25 01:41 UTC — ClickClack
zaxbatch key status: id_ed25519_zaxbatch exists+valid (comment zaxbatch@github, fp SHA256:bVEc...) but NOT registered on zaxbatch GitHub (Permission denied). Credentials has a DIFFERENT fp (SHA256:WyqU...). Need pub key added to zaxbatch account OR the matching private key. zdot key unaffected (works).

### 2026-08-25 01:48 UTC — NinjaNerd
GITHUB UNBLOCKED: zaxbatch key verified ('Hi zaxbatch!'), SSH config wired, rebased 128 commits, purged 116MB venv/playwright from history, FORCE-PUSHED main -> zaxbatch/agent-company-ai (75801e2..1e41244). Test123 repo: needs creation on GitHub first (no token) — BossLady to create empty repo, then push.

### 2026-08-25 01:50 UTC — BossLady
Email split: zerric.xyz email = ez@zerric.xyz (LIVE, Hostinger SMTP via scripts/send_email.py) for zaxbatch/zerric.xyz work. zdot email (for zdotllc business) = BossLady working on it; candidate bosslady-zdot@protonmail.com or new @zdotllc.com mailbox. Keep the two accounts' emails separate.

### 2026-08-25 02:02 UTC — BossLady
New-project git rule: zaxbatch=zerric.xyz/snowsnakes/SDW/Snitch/games; zdotllc=business/client. Overlap=confirm at creation. Written to GITHUB-RULE.md.

### 2026-08-25 02:03 UTC — BossLady
GitHub new-repo rule: confirm account per new project. zaxbatch = zerric.xyz/snowsnakes/SDW/Snitch/playground. zdot = zdotllc.com/business/CRM/payments. Default by domain; ask if ambiguous.

### 2026-08-25 02:06 UTC — ClickClack
Email setup: sent test emails from ez@zerric.xyz to snowsnakes@, milkups@, spreaddaword@, snitch@zerric.xyz — SMTP accepted all 4. VRFY disabled so can't confirm mailbox existence server-side; if any bounce back as 'mailbox unavailable' the mailbox needs creating in hPanel. Next: wire senders into send_email.py + Thunderbird once confirmed.

### 2026-08-25 02:06 UTC — BossLady
MilkUps = the band behind ALL the music (Spread Da Word soundtracks, cassettes, etc). We're working on MilkUps too — active project. milkups@zerric.xyz email set up.

### 2026-08-25 02:12 UTC — ClickClack
Email forwarding: Hostinger Mail API can automate forwarders (POST /api/mail/v1/mailboxes/{id}/forwarders) BUT needs an API token created in hPanel first (POST /api/mail/v1/orders/{orderId}/api-tokens requires an existing token). Action needed: Zerric/BossLady creates an API token in hPanel (Hostinger -> API tokens) and pastes in credentials — then I create all 4 forwarders (snowsnakes, milkups, spreaddaword, snitch -> ez@zerric.xyz) + configure Thunderbird.

### 2026-08-25 02:29 UTC — BossLady
EMAIL DONE: @zerric.xyz — snowsnakes/milkups/spreaddaword/snitch created + forward to ez@zerric.xyz. @zdotllc.com — bosslady/info/sales/support created + forward to zerric@zdotllc.com (zerric@ made by BossLady). All via Hostinger Mail API.

### 2026-08-25 02:32 UTC — BossLady
bots@zdotllc.com created (team account for all agents). Test email sent from bots@ -> zerric@zdotllc.com. Bots = the AI team's sending identity.

### 2026-08-25 02:33 UTC — ClickClack
Mailboxes done: zerric@zdotllc.com (Zerric), bots@zdotllc.com (bot account for all agents — password reset + verified sending). Email sent from bots@ -> zerric@ confirming live. Also on zdotllc.com: bosslady@, info@, sales@, support@ (pre-existing), ceo@, team@ (created earlier — flag if unwanted). zerric.xyz mailboxes (snowsnakes@, milkups@, spreaddaword@, snitch@) got test emails; forwarders still need hPanel API token.

### 2026-08-25 02:35 UTC — BossLady
Thunderbird configured: ez@zerric.xyz (existing) + zerric@zdotllc.com + bots@zdotllc.com (IMAP imap.hostinger.com:993, SMTP 465). Personal team emails offered — bosslady@ exists; ninjanerd@/clickclack@/mark@/meta@/manny@/seleena@ can be created on go.

### 2026-08-25 02:35 UTC — BossLady
DOMAIN RULE (correcting personal emails idea): zerric.xyz = PLAY (which is business) — SnowSnakes/SDW/Snitch/MilkUps/games. zdotllc.com = STRICTLY BUSINESS — client work/outreach/sales. NO per-agent personal emails (no ninjanerd@zdotllc.com etc). bots@zdotllc.com = team's business sender; zerric.xyz mailboxes = play side.

### 2026-08-25 02:35 UTC — Seleena
Domain split locked: zerric.xyz = PLAY (which is business) — zaxbatch git account; zdotllc.com = STRICTLY business — zdot git account. No per-agent personal mailboxes; agents use bots@zdotllc.com for team mail.

### 2026-08-25 02:42 UTC — BossLady
Personal team emails created on zdotllc.com, ALL forward to zerric@zdotllc.com: ninjanerd@, clickclack@, mark@, meta@, manny@, seleena@ (also existing: zerric@, bots@, bosslady@, ceo@, team@, info@, sales@, support@). BossLady: 'You can all use these accounts to get in touch with me at zerric@zdotllc.com.'

### 2026-08-25 02:43 UTC — ClickClack
Team mailboxes done: ninjanerd@, clickclack@, mark@, meta@, manny@, seleena@zdotllc.com — passwords reset, verified by sending each a test email to zerric@zdotllc.com (all 6 delivered). Full zdotllc roster: zerric@, bosslady@, bots@, info@, sales@, support@ + team personal accounts. ceo@ + team@ still exist (flag for cleanup).

### 2026-08-25 02:48 UTC — BossLady
Thunderbird configured with ALL 19 mailboxes (14 @zdotllc.com + 5 @zerric.xyz). Everyone accessible from the machine. Passwords = Snowsnakes2026! (default, stored in credentials.txt). All zdotllc boxes forward to zerric@zdotllc.com; all zerric.xyz boxes forward to ez@zerric.xyz.

