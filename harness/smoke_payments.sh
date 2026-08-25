#!/usr/bin/env bash
# INC-2026-08-25-001 — smoke test: payments (one command, logs HTTP status + body)
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f ".env" ]; then set -a; source .env; set +a; fi
mkdir -p logs/inc-2026-08-25-001
exec ./venv/bin/python harness/smoke_tool.py payments --log "logs/inc-2026-08-25-001/baseline-payments.log"
