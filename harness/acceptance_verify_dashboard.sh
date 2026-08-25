#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# acceptance_verify_dashboard.sh
# Acceptance verification harness — VIRTUAL-MODE dashboard fix
#   Bug under test : "Exception in ASGI application" (FastAPI/Starlette
#                    BaseHTTPMiddleware JSONResponse dispatch path)
#   Acceptance     : AC-1 virtual-mode clean start (owner's exact command)
#                    AC-2 no ASGI exception at startup or after ANY request
#                    AC-3 all key endpoints → HTTP 200 + valid JSON
#                    AC-4 normal (non-virtual) mode — no regression
#   Owner          : NinjaNerd (CTO) — review this spec BEFORE running.
#   Status         : READY-TO-RUN (NOT yet executed — CTO still finalizing fix)
#
#   USAGE:
#     ./acceptance_verify_dashboard.sh [--virtual-cmd "CMD"] [--normal-cmd "CMD"]
#         --virtual-cmd  override the owner's VIRTUAL-mode startup command
#         --normal-cmd   override the NORMAL-mode startup command
#     Environment overrides: VIRTUAL_MODE_CMD, NORMAL_MODE_CMD, BASE_URL,
#                            PORT, LOG_DIR, ADMIN_USER, ADMIN_PASS
#
#   Exit code: 0 = ALL PASS · 1 = any FAIL · 2 = harness/usage error
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

# ── Config (single source of truth — EDIT/OVERRIDE as needed) ────────────────
PORT="${PORT:-8420}"
BASE_URL="${BASE_URL:-http://127.0.0.1:${PORT}}"
LOG_DIR="${LOG_DIR:-/tmp/aca-verify}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-admin123}"
ASGI_PATTERN="Exception in ASGI application"
READY_TIMEOUT="${READY_TIMEOUT:-60}"          # seconds to wait for server up
REPEAT_PER_ENDPOINT="${REPEAT_PER_ENDPOINT:-5}" # repeated requests per endpoint

# ── 1) OWNER'S EXACT VIRTUAL-MODE STARTUP COMMAND (AC-1) ─────────────────────
# Default mirrors start.sh (the repo's canonical launcher): create/activate the
# venv, install this repo, then launch the authenticated Mission Control
# dashboard on 0.0.0.0:8420 (matches .agent-company-ai/default/config.yaml).
# ⚠ CTO REVIEW: the PM tracker references a CTO-confirmed "acceptance command";
#   if it differs from the default below, pass --virtual-cmd or set
#   VIRTUAL_MODE_CMD to the EXACT owner command before running.
DEFAULT_VIRTUAL_CMD='source venv/bin/activate && exec agent-company-ai dashboard --host 0.0.0.0 --port '"${PORT}"
VIRTUAL_MODE_CMD="${VIRTUAL_MODE_CMD:-$DEFAULT_VIRTUAL_CMD}"

# ── NORMAL (non-virtual) MODE — README-documented command (AC-4) ─────────────
# Standard documented launch:  agent-company-ai dashboard --port 8420
DEFAULT_NORMAL_CMD="agent-company-ai dashboard --host 127.0.0.1 --port ${PORT}"
NORMAL_MODE_CMD="${NORMAL_MODE_CMD:-$DEFAULT_NORMAL_CMD}"

# ── 2) KEY DASHBOARD ENDPOINTS (verified against src/.../dashboard/server.py) ─
#    format: "METHOD|PATH|EXPECT_HTTP|EXPECT_BODY|LABEL"
#    EXPECT_BODY: json  → assert HTTP code AND valid JSON (python -m json.tool)
#                 html  → assert HTTP code AND non-empty text/html body
ENDPOINTS=(
  "GET|/api/status|200|json|health (status)"
  "GET|/api/agents|200|json|primary data: agents"
  "GET|/api/tasks|200|json|primary data: tasks"
  "GET|/api/cost|200|json|primary data: cost"
  "GET|/api/org-chart|200|json|primary data: org-chart"
)
# Dashboard index page (HTML by design — see spec §2 for the JSON note).
INDEX_ENDPOINT="GET|/|200|html|dashboard index"

# Unauthenticated API probe — exercises the EXACT buggy dispatch path
# (BaseHTTPMiddleware returning JSONResponse for /api/* without a session).
# Expected: HTTP 401 + valid JSON {"error":"Unauthorized"} + NO ASGI exception.
BUG_PROBE="GET|/api/status|401|json|BUG-PATH probe (no session)"

mkdir -p "$LOG_DIR"
VIRTUAL_LOG="$LOG_DIR/virtual-mode.log"
NORMAL_LOG="$LOG_DIR/normal-mode.log"
COOKIE_JAR="$LOG_DIR/cookies.txt"

# ── helpers ──────────────────────────────────────────────────────────────────
PASS=0; FAIL=0; declare -a RESULTS=()
_summary_row() { # label | result | detail
  RESULTS+=("$1|$2|$3")
  if [ "$2" = "PASS" ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi
}

_log()  { printf '[harness] %s\n' "$*"; }
_fail() { printf '[harness] ERROR: %s\n' "$*" >&2; exit 2; }

command -v curl  >/dev/null || _fail "curl is required"
command -v python3 >/dev/null || _fail "python3 is required (for json.tool)"

_kill_port() { # kill anything already bound to $PORT
  local pids
  pids=$( (lsof -ti tcp:"$PORT" 2>/dev/null || true) )
  if [ -n "$pids" ]; then kill $pids 2>/dev/null || true; sleep 1; fi
}

_wait_ready() { # $1 = logfile
  local log="$1" i
  for i in $(seq 1 "$READY_TIMEOUT"); do
    # /login is auth-free → any HTTP code (200/3xx) means uvicorn is serving.
    code=$(curl -s -o /dev/null -m 2 -w "%{http_code}" "$BASE_URL/login" 2>/dev/null || echo 000)
    if [ "$code" != "000" ]; then
      sleep 1
      return 0
    fi
    sleep 1
  done
  return 1
}

_start_server() { # $1 = cmd  $2 = logfile  $3 = label
  local cmd="$1" log="$2" label="$3"
  _kill_port
  : > "$log"
  _log "Starting [$label] — command: $cmd"
  _log "  logfile: $log"
  bash -c "$cmd" >"$log" 2>&1 &
  SERVER_PID=$!
  if ! _wait_ready "$log"; then
    _log "SERVER FAILED TO START in ${READY_TIMEOUT}s — log tail:"
    tail -40 "$log" >&2 || true
    _summary_row "$label: startup (AC-1)" "FAIL" "server not ready"
    return 1
  fi
  _log "Server is up (PID $SERVER_PID)."
  _assert_no_asgi "$log" "$label: startup log scan (AC-2)"
  return 0
}

_stop_server() {
  if [ -n "${SERVER_PID:-}" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
    SERVER_PID=""
  fi
  _kill_port
}

_assert_no_asgi() { # $1 = logfile  $2 = label
  local log="$1" label="$2"
  if grep -q "$ASGI_PATTERN" "$log" 2>/dev/null; then
    _summary_row "$label" "FAIL" "found: $ASGI_PATTERN"
    return 1
  fi
  _summary_row "$label" "PASS" "no ASGI exception"
  return 0
}

_login() { # $1 = cookiejar ; returns 0 on session acquired
  local jar="$1" code
  code=$(curl -s -o /dev/null -w "%{http_code}" -c "$jar" \
      -d "username=${ADMIN_USER}&password=${ADMIN_PASS}" \
      "$BASE_URL/login")
  # 303 = auth OK (redirect to /). 200 can occur if already-authed page shown.
  [ "$code" = "303" ] || [ "$code" = "200" ]
}

_probe() { # $1 = method $2 = path $3 = expect_http $4 = expect_body \
           # $5 = label $6 = logfile [$7 = cookiejar (optional)]
  local method="$1" path="$2" exp_http="$3" exp_body="$4" label="$5" log="$6"
  local jar="${7:-}" body_file="$LOG_DIR/body.tmp" code body_ok=0 result="FAIL" detail=""
  local curl_args=(-s -o "$body_file" -w "%{http_code}" -m 30 -X "$method")
  [ -n "$jar" ] && curl_args+=(-b "$jar")

  code=$(curl "${curl_args[@]}" "$BASE_URL$path")

  # HTTP code check
  if [ "$code" != "$exp_http" ]; then
    detail="HTTP ${code} (expected ${exp_http})"
    _summary_row "$label" "FAIL" "$detail"
    _assert_no_asgi "$log" "$label: post-request log scan (AC-2)" >/dev/null
    return 1
  fi

  # Body check
  if [ "$exp_body" = "json" ]; then
    if python3 -m json.tool "$body_file" >/dev/null 2>&1; then
      body_ok=1
    else
      detail="body is NOT valid JSON"
    fi
  else # html
    if grep -qi "text/html" <<<"$(head -c 200 "$body_file")" 2>/dev/null \
       || [ -s "$body_file" ]; then
      body_ok=1
    else
      detail="body empty / not HTML"
    fi
  fi

  if [ "$body_ok" = "1" ]; then
    result="PASS"
    detail="HTTP ${code} + valid ${exp_body}"
  else
    detail="HTTP ${code} but ${detail:-body check failed}"
  fi
  _summary_row "$label" "$result" "$detail"
  _assert_no_asgi "$log" "$label: post-request log scan (AC-2)" >/dev/null
  [ "$result" = "PASS" ]
}

_run_mode() { # $1 = mode label (virtual/normal) $2 = start cmd $3 = logfile
  local mode="$1" cmd="$2" log="$3" jar="$LOG_DIR/${mode}-cookies.txt"
  _log "══════════════════════════════════════════════════════════"
  _log "MODE: ${mode^^}  (AC-1/AC-2/AC-3 for virtual; AC-4 for normal)"
  _log "══════════════════════════════════════════════════════════"

  _start_server "$cmd" "$log" "$mode" || return 1

  # ── login (session for authed endpoint checks) ──
  rm -f "$jar"
  if _login "$jar"; then
    _summary_row "$mode: login (admin session)" "PASS" "session cookie acquired"
  else
    _summary_row "$mode: login (admin session)" "FAIL" "could not authenticate"
    _stop_server
    return 1
  fi

  # ── dashboard index (HTML page — 200 + non-empty body) ──
  IFS='|' read -r m p e b l <<< "$INDEX_ENDPOINT"
  _probe "$m" "$p" "$e" "$b" "$mode: $l" "$log" "$jar"

  # ── primary data/API endpoints (200 + valid JSON) — repeated ×N ──
  local rep
  for rep in $(seq 1 "$REPEAT_PER_ENDPOINT"); do
    for row in "${ENDPOINTS[@]}"; do
      IFS='|' read -r m p e b l <<< "$row"
      _probe "$m" "$p" "$e" "$b" "$mode: $l" "$log" "$jar"
    done
  done

  # ── BUG-PATH probe: unauthenticated /api/* → 401 JSON, NO ASGI exception ──
  IFS='|' read -r m p e b l <<< "$BUG_PROBE"
  _probe "$m" "$p" "$e" "$b" "$mode: $l" "$log"  # no cookie jar on purpose

  # ── final full-log scan ──
  _assert_no_asgi "$log" "$mode: final log scan (AC-2)"
  _stop_server
}

# ── CLI arg parsing ──────────────────────────────────────────────────────────
while [ $# -gt 0 ]; do
  case "$1" in
    --virtual-cmd) VIRTUAL_MODE_CMD="$2"; shift 2;;
    --normal-cmd)  NORMAL_MODE_CMD="$2";  shift 2;;
    *) _fail "unknown argument: $1";;
  esac
done

# ── main ─────────────────────────────────────────────────────────────────────
_log "Acceptance verification harness — virtual-mode dashboard fix"
_log "BASE_URL=$BASE_URL  PORT=$PORT  LOG_DIR=$LOG_DIR"
_log "VIRTUAL_MODE_CMD=$VIRTUAL_MODE_CMD"
_log "NORMAL_MODE_CMD =$NORMAL_MODE_CMD"
_log "Endpoints under test:"
for row in "${ENDPOINTS[@]}"; do
  IFS='|' read -r m p e b l <<< "$row"
  _log "   $m $p  → expect ${e} + ${b}  ($l)"
done

_run_mode "virtual" "$VIRTUAL_MODE_CMD" "$VIRTUAL_LOG"
_run_mode "normal"  "$NORMAL_MODE_CMD"  "$NORMAL_LOG"

# ── PASS/FAIL summary table ──────────────────────────────────────────────────
_log ""
_log "══════════════════════════ SUMMARY ══════════════════════════"
printf '%-58s | %-5s | %s\n' "Check" "RESULT" "Detail"
printf '%s\n' "------------------------------------------------------------+-------+------------------------------------"
for row in "${RESULTS[@]}"; do
  IFS='|' read -r label result detail <<< "$row"
  printf '%-58s | %-5s | %s\n' "$label" "$result" "$detail"
done
printf '%s\n' "------------------------------------------------------------+-------+------------------------------------"
printf 'TOTAL: %d PASS, %d FAIL\n' "$PASS" "$FAIL"
if [ "$FAIL" -eq 0 ]; then
  _log "VERDICT: ALL PASS ✔  (AC-1 ✓ AC-2 ✓ AC-3 ✓ AC-4 ✓)"
  exit 0
else
  _log "VERDICT: FAILURES PRESENT ✘ — see rows marked FAIL; block owner sign-off."
  exit 1
fi
