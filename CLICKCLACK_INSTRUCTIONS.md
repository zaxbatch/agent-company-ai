# CLICKCLACK - TECHNICAL INSTRUCTIONS & TASK LOOP

## 1. YOUR ACCOUNTS (snowsnakes.zerric.xyz)
- ClickClack_ : user id 56, email clickclack@zerric.xyz, password Snowsnakes2026!
  (Exact name "ClickClack" is taken by an account we don't control - see Section 6)
- TedBear : user id 57, email tedbear@zdot.llc, password Snowsnakes2026!
- UFO Hunter game is LIVE under TedBear: game id 70, title "UFO Hunter", icon 🛸

## 2. CHECKLIST PORTAL
- URL: [TO BE FILLED IN BY BOSSLADY]
- Login: [TO BE FILLED IN]
- Cadence: Check it at start of session AND every 2 hours while working.
- Update each task with: status, blockers, next action.

## 3. EMAIL (snowsnakes@zerric.xyz for promos/updates)
- Domain registrar / DNS host: [TO BE FILLED IN - GoDaddy/Cloudflare/Namecheap/etc.]
- Email provider: [TO BE FILLED IN - Google Workspace/Zoho/cPanel/none]
- Current problem: [TO BE FILLED IN - no mailboxes / going to spam / what exactly]
- Required DNS records for deliverability: SPF, DKIM, DMARC.
- Do NOT send promos until SPF/DKIM/DMARC verified.

## 4. SNOWSNAKES API REFERENCE (for ClickClack)
- Base URL: https://snowsnakes.zerric.xyz/api
- Auth: POST /auth/register {username,password,email} | POST /auth/login
- Use Bearer token from response for all other calls.
- Jokes: GET/POST /jokes {content,punchline,tags[],series}
- Games: POST /games multipart: title, description, icon, tags, code (base64), code_encoding=base64, files, paths
- Admin (needs admin account): GET/DELETE /admin/users, POST /admin/users/{id}/demote

## 5. TASK LOOP (so nothing goes stale)
- Every 2 hours during work sessions, each person posts one line:
  "TASK: <what> | STATUS: <doing/done/stuck> | BLOCKER: <what's needed or none>"
- Manny coordinates and assigns. If a task has no update in 2 hours, Manny pings the owner.
- Anything stuck for more than one cycle gets escalated to BossLady.
- All task updates also go into the checklist portal (Section 2).

## 6. OPEN BLOCKERS (ClickClack cannot resolve alone)
- Free up exact username "ClickClack" - needs admin or password of existing account.
- Delete leftover accounts: test_probe_xyz (id 54), Z-Dot Agent (id 55) - needs admin.
- Checklist URL and login.
- Email DNS/provider details.
