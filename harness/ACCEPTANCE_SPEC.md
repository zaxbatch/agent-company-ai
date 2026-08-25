# Acceptance Verification Spec — Virtual-Mode Dashboard Fix
**Harness:** `harness/acceptance_verify_dashboard.sh` (ready-to-run, **not yet executed**)
**Bug under test:** `Exception in ASGI application` — FastAPI/Starlette
`BaseHTTPMiddleware.dispatch()` returning a `JSONResponse` for the virtual-mode
auth path at `src/agent_company_ai/dashboard/server.py:571` (and sibling 403
paths at 579/584), producing a conflicting/duplicate ASGI send sequence under
uvicorn.
**Status:** ⚠ CTO REVIEW REQUIRED before running. The CTO is still finalizing
the fix; this harness validates the fix once it lands.

---

## 0) Acceptance Criteria (from Meta's tracker — confirmed with owner/CTO)
| # | Criterion | How the harness proves it |
|---|-----------|---------------------------|
| AC-1 | App starts successfully in **virtual mode** using the **owner's exact command** | `_start_server` runs `$VIRTUAL_MODE_CMD`, waits for uvicorn to serve, asserts the process comes up |
| AC-2 | **No `Exception in ASGI application`** in logs — after startup and after **every** request | `_assert_no_asgi` scans the full server log after startup, after each of the repeated endpoint probes, and at the end |
| AC-3 | All key dashboard endpoints → **HTTP 200 + valid JSON** | `_probe` asserts the HTTP code and pipes the body through `python3 -m json.tool` |
| AC-4 | **Normal (non-virtual) mode still works** — no regression | Second pass runs the README-documented command against the same endpoints/assertions |

Sign-off rule: ALL FOUR must PASS. Any FAIL blocks release.

---

## 1) Startup Commands

### 1a. VIRTUAL mode — owner's command (AC-1)
The PM tracker states the CTO confirmed the owner's exact acceptance command,
but the literal string is **not recorded in the repo** (searched `start.sh`,
`README.md`, `src/agent_company_ai/cli/app.py`, `.agent-company-ai/…/output/`,
`state-backup/`, `communication/`, git history). The harness therefore defaults
to the repo's canonical owner launcher (`start.sh`), which mirrors the dashboard
config in `.agent-company-ai/default/config.yaml` (`host: 0.0.0.0, port: 8420`):

```bash
# Default in harness (override with VIRTUAL_MODE_CMD or --virtual-cmd):
source venv/bin/activate && exec agent-company-ai dashboard --host 0.0.0.0 --port 8420
```
`start.sh` wraps this exact sequence (create venv → `pip install -e .` → create
default config → `exec agent-company-ai dashboard --host 0.0.0.0 --port 8420`).

> **⚠ CTO ACTION:** confirm the owner's literal virtual-mode command and, if it
> differs, drop it into the harness at the `VIRTUAL_MODE_CMD` variable (or pass
> `--virtual-cmd "…"`). Everything else in the harness is mode-agnostic.

### 1b. NORMAL (non-virtual) mode — no-regression baseline (AC-4)
README-documented standard launch:

```bash
agent-company-ai dashboard --host 127.0.0.1 --port 8420
```
(Override with `NORMAL_MODE_CMD` or `--normal-cmd`.)

---

## 2) Dashboard Endpoints Under Test
Source of truth: `src/agent_company_ai/dashboard/server.py` (verified — full
route inventory in §2a). The harness selects the **health**, **dashboard
index**, and **3 primary data/API endpoints**:

| # | Role in task | Path | Method | Auth | Expected | Body assertion |
|---|--------------|------|--------|------|----------|----------------|
| 1 | Health | `/api/status` | GET | session | 200 | valid JSON |
| 2 | Dashboard index | `/` | GET | session | 200 | non-empty HTML page |
| 3 | Primary data 1 | `/api/agents` | GET | session | 200 | valid JSON |
| 4 | Primary data 2 | `/api/tasks` | GET | session | 200 | valid JSON |
| 5 | Primary data 3 | `/api/cost` | GET | session | 200 | valid JSON |
| 6 | (extra) | `/api/org-chart` | GET | session | 200 | valid JSON |
| 7 | BUG-PATH probe | `/api/status` | GET | **none** | 401 | valid JSON `{"error":"Unauthorized"}` — must **not** raise an ASGI exception |

Each endpoint is probed `REPEAT_PER_ENDPOINT` (default 5) times, with a log scan
after every probe (matches the PM verification table).

### 2a. Full route inventory (from `server.py`)
- **HTML pages:** `/login` (GET/POST), `/logout` (POST), `/change-password`
  (GET), `/users` (GET, admin), `/` (dashboard index — **HTML, not JSON**),
  `/style.css`, `/app.js`
- **API (JSON):** `/api/auth/me`, `/api/auth/change-password`,
  `/api/lead-trap`, `/api/users` (GET/POST), `/api/users/{username}` (DELETE),
  `/api/users/{username}/reset-password`, `/api/status`, `/api/agents`,
  `/api/org-chart`, `/api/tasks` (GET/POST), `/api/chat/{agent_name}`,
  `/api/goal`, `/api/stop`, `/api/hire`, `/api/cost`, `/api/cost/recent`,
  `/api/messages`, `/api/artifacts`, `/api/artifacts/{artifact_id}`,
  `/api/output-dir`, `/api/profit-engine` (GET/POST),
  `/api/profit-engine/templates`, `/api/wallet/balance`,
  `/api/wallet/address`, `/api/wallet/payments`
- **WebSocket:** `/ws`

### 2b. Two spec clarifications (flagged for CTO review)
1. **`/health` does not exist** in the current `server.py`. The harness maps the
   "health" check to `/api/status` (the status/health-equivalent JSON endpoint).
   If the CTO's fix adds `/health`, add it to `ENDPOINTS` in the harness — the
   harness will then verify it like any other JSON endpoint.
2. **Dashboard index `/` returns HTML**, not JSON. Asserting `valid JSON` on the
   index page would fail by design. The harness asserts **HTTP 200 + non-empty
   HTML body** for `/` and reserves the strict "200 + valid JSON" assertion for
   the `/api/*` data endpoints. If the acceptance criteria truly require the
   index to be JSON, that is a product/spec change, not a verification detail.

---

## 3) Verification Steps (what the script executes)

### Step 0 — Preconditions
- `python3`, `curl`, and the repo's `venv` present (the harness does not create
  the venv; `start.sh` does).
- Port 8420 free (harness force-frees it at each start).

### Step 1 — Virtual-mode run (AC-1, AC-2, AC-3)
1. Kill anything on port 8420; start server via `$VIRTUAL_MODE_CMD`, tee output
   to `$LOG_DIR/virtual-mode.log`.
2. Poll `GET /login` (auth-free) until any HTTP code ≠ 000 (up to 60 s).
   Failure → row `virtual: startup (AC-1)` = FAIL, dump log tail.
3. **Startup log scan:** `grep -q "Exception in ASGI application"` → FAIL.
4. **Login:** `curl -c jar -d "username=admin&password=admin123" /login`
   → expect 303 + session cookie. (Current `dashboard_users.json` has
   `must_change_password: false`; if a forced change is hit, the harness's login
   step fails loudly and the operator must reset the admin password first.)
5. **Dashboard index:** `GET /` with session → 200 + non-empty HTML.
6. **Data endpoints** (status/agents/tasks/cost/org-chart): `GET` with session →
   200 + `python3 -m json.tool` validates the body; repeated 5× each.
7. **BUG-PATH probe (the fix's real target):** `GET /api/status` **without** a
   session → expect 401 + valid JSON, then scan log → must contain **no**
   `Exception in ASGI application`. This exercises the exact
   `JSONResponse`-from-`dispatch()` path that was crashing.
8. **Final log scan:** full `virtual-mode.log` must be clean of the pattern.
9. Stop the server.

### Step 2 — Normal-mode no-regression run (AC-4)
Repeat Step 1 verbatim with `$NORMAL_MODE_CMD` and `$LOG_DIR/normal-mode.log`.
Same endpoints, same assertions, same log scans.

### Step 3 — Summary
Print the PASS/FAIL table (label | RESULT | detail), the total counts, and the
verdict:
- `FAIL == 0` → `VERDICT: ALL PASS ✔ (AC-1 ✓ AC-2 ✓ AC-3 ✓ AC-4 ✓)`, exit 0.
- otherwise → `VERDICT: FAILURES PRESENT ✘`, exit 1 (blocks owner sign-off).

---

## 4) PASS/FAIL Summary Table (template — produced by the harness)
```
Check                                                     | RESULT | Detail
-----------------------------------------------------------+--------+------------------------------------
virtual: startup (AC-1)                                    | PASS   | server ready, no ASGI exception
virtual: startup log scan (AC-2)                           | PASS   | no ASGI exception
virtual: login (admin session)                             | PASS   | session cookie acquired
virtual: dashboard index                                   | PASS   | HTTP 200 + valid html
virtual: health (status)                                   | PASS   | HTTP 200 + valid json
virtual: primary data: agents                              | PASS   | HTTP 200 + valid json
virtual: primary data: tasks                               | PASS   | HTTP 200 + valid json
virtual: primary data: cost                                | PASS   | HTTP 200 + valid json
virtual: primary data: org-chart                           | PASS   | HTTP 200 + valid json
virtual: BUG-PATH probe (no session)                       | PASS   | HTTP 401 + valid json
virtual: post-request log scan (AC-2) ×N                   | PASS   | no ASGI exception
virtual: final log scan (AC-2)                             | PASS   | no ASGI exception
normal: startup (AC-4)                                     | PASS   | server ready
normal: … (same rows as virtual)                           | PASS   | …
TOTAL: 2N PASS, 0 FAIL                                     |        |
VERDICT: ALL PASS ✔ (AC-1 ✓ AC-2 ✓ AC-3 ✓ AC-4 ✓)         |        |
```

---

## 5) CTO Review Checklist (before execution)
- [ ] Confirm the **exact virtual-mode startup command** and set `VIRTUAL_MODE_CMD`
      (or `--virtual-cmd`) to it.
- [ ] Confirm the fix is committed/branched and the working tree contains the
      corrected middleware (harness currently expects `server.py` to have the
      pure-ASGI middleware or equivalent; the current checkout still has
      `BaseHTTPMiddleware`).
- [ ] Confirm `/health` (add to `ENDPOINTS` if introduced by the fix).
- [ ] Confirm the admin credentials (default `admin/admin123`, no forced change
      in the current `dashboard_users.json`).
- [ ] Approve the HTML-vs-JSON handling for `/` (§2b.2) and the `/api/status`
      mapping for health (§2b.1).

## 6) How to Run (after CTO approval)
```bash
cd /home/zax/Biz/z-dot-team
harness/acceptance_verify_dashboard.sh                # defaults
# or with an explicit CTO-confirmed command:
harness/acceptance_verify_dashboard.sh --virtual-cmd "source venv/bin/activate && exec agent-company-ai dashboard --host 0.0.0.0 --port 8420"
```
Logs: `/tmp/aca-verify/virtual-mode.log`, `/tmp/aca-verify/normal-mode.log`.

## 7) Known Risks / Notes
- The harness **does not modify** application code, config, or `dashboard_users.json`;
  it only starts/stops the server and writes temp logs/cookies under `$LOG_DIR`.
- Port 8420 is force-freed before each run — safe for CI, but do not run while a
  real dashboard session is in use on that port.
- If the ASGI exception only appears under uvicorn's `--reload` or on the first
  request, the repeated-probe loop (5× per endpoint) plus the unauthenticated
  bug-path probe is designed to surface it deterministically.
