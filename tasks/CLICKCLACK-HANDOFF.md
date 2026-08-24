CLICKCLACK HANDOFF - TECHNICAL INSTRUCTIONS
From: NinjaNerd (CTO) / BossLady
Date: 2026-08-23
Status: PRIORITY - these are your assigned tasks on the checklist

READ THIS FIRST
- The checklist portal (t10) is already BUILT and VERIFIED by the CTO. Do not rebuild it.
- Your job is your remaining open tasks below, in priority order.
- Every task you work on: update its status on the portal as you go (assigned -> in_progress -> done). Do not mark anything done without a result text describing what you delivered and how to verify it.

HOW TO RUN THE CHECKLIST PORTAL (it is your tracking board)
1. From /home/zax/Biz/z-dot-team:
   cd /home/zax/Biz/z-dot-team
   export PYTHONPATH=src
   python3 -m uvicorn agent_company_ai.checklist.server:app --port 8430
2. Open http://127.0.0.1:8430 in a browser.
3. Pick your name in the "Who are you?" dropdown, then click "Check in".
4. Data persists to src/agent_company_ai/checklist/data/checklist.json.
5. Watchdog (run anytime, or Manny runs it): python3 scripts/checklist_watchdog.py

------------------------------------------------------------------
TASK 1 (HIGHEST PRIORITY): t2-retry - SnowSnakes registration + dad jokes
Goal: Register on snowsnakes.zerric.xyz with your REAL NAME (BossLady approved this) and post a few original dad jokes.
Site: https://snowsnakes.zerric.xyz  (live, HTTP 200, React SPA - needs a JS-capable browser)
Why Playwright: the site is a React single-page app. Plain HTTP/requests tooling cannot drive it. Use Playwright.
Setup:
  pip install playwright
  playwright install chromium
Approach:
  - Launch Chromium via Playwright, navigate to https://snowsnakes.zerric.xyz
  - Find the register/login flow on the page (React SPA - look for register buttons/forms)
  - Register using your real name as username. Use a throwaway or team password you can retrieve; do NOT invent a fake name.
  - After registering, post 3-5 original dad jokes through the UI.
  - The public API for verification: GET https://snowsnakes.zerric.xyz/api/jokes (JSON list)
Verify and report:
  - Confirm your username appears in the jokes you posted (check /api/jokes)
  - Report your exact username here in the group chat - the CTO needs it to reconcile author records (t3)
  - Update t2 on the portal: status done, result = username used + how to find your posts + screenshot or API proof
Blockers: if Cloudflare JS challenge blocks you, note it in the t2 blocker field and report here. Do NOT give up after one try.

------------------------------------------------------------------
TASK 2: t7-network - Zerric's Network posting diagnosis
Goal: Diagnose why posting to Zerric's Network fails, and seed the first posts.
Site: Zerric's Network = https://botcity.zerric.com (live, early beta)
Known state: admin dashboard and bot templates are configured; public feed has ZERO posts; community features marked "coming soon".
Approach:
  - Inspect the admin dashboard and bot config for how posts are supposed to be created
  - Attempt to create/seed one test post through the intended path
  - Capture the exact failure point (endpoint, error, log) if it fails
Verify and report:
  - Report what works, what fails, and the exact error at each step
  - Update t7 on the portal with status and result
  - Do NOT publish bot-generated content publicly without Zerric's go-ahead (see blocker field)

------------------------------------------------------------------
TASK 3: t9-housekeeping - repo version drift, tests, CI, secrets
Repo: /home/zax/Biz/z-dot-team (git repo, remote github.com/zaxbatch/agent-company-ai)
1. Version drift: align the package version.
   - pyproject.toml currently 0.6.1; src/agent_company_ai/__init__.py currently 0.5.0; CHANGELOG.md stops at 0.5.0
   - Pick one version, make all three agree (recommend 0.6.1), update CHANGELOG.
2. Tests:
   - Install pytest: pip install pytest (venv is at ./venv)
   - Run: python3 -m pytest tests/ - existing tests are test_config.py, test_cost_tracker.py, test_task.py, test_tools_registry.py
   - Fix any that fail; report the pass count.
3. CI: the .github/workflows/ directory is empty (workflow was removed). Add a minimal CI workflow:
   - On push/PR: checkout, setup-python 3.11, pip install -e ., run pytest
   - File: .github/workflows/ci.yml
4. Secrets: a live DeepSeek API key sits in plaintext in .agent-company-ai/default/config.yaml
   - Move it to an environment variable (config supports env override - check config.py for the pattern, e.g. AGENT_AI_* env vars)
   - Keep the local working config functional - do not break the running system
Verify and report: pytest green, version numbers consistent, ci.yml present, no plaintext API key in committed config. Update t9 on the portal.

------------------------------------------------------------------
TASK 4: t17-notif-ui - Dashboard notification UI (QUEUED, needs spec)
Do NOT start this until the CTO writes you a spec. Known blockers (from the PM verification report):
  - src/agent_company_ai/notifications/service.py and webhooks.py are MISSING - package import fails
  - The notification DB schema is coded but never applied to company.db
  - No notifications section in runtime config.yaml
If you want this task, tell the CTO and I will write the backend spec first. Otherwise it stays queued.

------------------------------------------------------------------
TASK 5: t16-user-email-list (BLOCKED - do not start)
Blocked on: SnowSnakes DB access or HubSpot token, plus Zerric's ownership decision on using the user list for promos.
If the blocker clears, the task is: source registered SnowSnakes users (DB users table or HubSpot contacts) into a list for updates/promos, respecting privacy and Zerric's approval.

------------------------------------------------------------------
RULES FOR YOU
1. Never mark a task done without a result: what you did, where the code/artifact is, and how to verify it.
2. Update status as you work. Check in on the portal regularly (the watchdog flags anyone stale after 2 hours).
3. If you are blocked, put the exact blocker in the blocker field and say so in the chat. Do not go silent.
4. If a task needs a spec you don't have, ask for it by task ID instead of guessing.
5. BossLady and Zerric's instructions outrank the checklist. When in doubt, ask.
