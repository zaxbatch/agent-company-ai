#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Mission Control — start the dashboard the RIGHT way, every time.
#
#   ./start.sh
#
# This script:
#   1. Creates/uses the local virtualenv
#   2. Installs agent-company-ai FROM THIS REPO (never PyPI)
#   3. Creates the default config from config.example.yaml if missing
#   4. Launches the authenticated Mission Control dashboard
# ─────────────────────────────────────────────────────────────
set -e

# ── 0. load secrets from .env (git-ignored) ──
if [ -f ".env" ]; then
  set -a; source .env; set +a
fi
cd "$(dirname "$0")"

# ── 1. virtualenv ────────────────────────────────────────────
if [ ! -d "venv" ]; then
  echo "→ Creating virtualenv..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

# ── 2. install THIS repo's package (fixes PyPI/pipx mix-ups) ─
VERSION=$(python -c "import importlib.metadata as m; print(m.version('agent-company-ai'))" 2>/dev/null || echo "none")
MODULE=$(python -c "import agent_company_ai.dashboard.server as s; print(s.__file__)" 2>/dev/null || echo "none")
REPO_ROOT="$(pwd)"
REPO_VERSION=$(grep -m1 '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')
if [ "$VERSION" != "$REPO_VERSION" ] || [[ "$MODULE" != *"$REPO_ROOT"* ]]; then
  echo "→ Installing agent-company-ai from THIS repo (was: $VERSION at $MODULE)..."
  pip install -e . --quiet
fi

# ── 3. default config (blank slate) ──────────────────────────
if [ ! -f ".agent-company-ai/default/config.yaml" ]; then
  echo "→ Creating default config from config.example.yaml"
  mkdir -p .agent-company-ai/default
  cp config.example.yaml .agent-company-ai/default/config.yaml
  echo "  ⚠ Edit .agent-company-ai/default/config.yaml and add your LLM API key."
fi

# ── 4. run Mission Control (auth enabled) ────────────────────
echo ""
echo "🚀 Starting Mission Control at http://0.0.0.0:8420"
echo "   Default login: admin / admin123  (forced change on first login)"
echo ""
exec agent-company-ai dashboard --host 0.0.0.0 --port 8420
