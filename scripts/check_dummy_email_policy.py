#!/usr/bin/env python3
"""
check_dummy_email_policy.py — CI guardrail for the Z-Dot email-domain policy
============================================================================
POLICY (BossLady directive, 2026-08-30): @zdotllc.com is the REAL company
email domain. Dummy/test/placeholder addresses MUST use @zdot-dummy.com.

This checker scans tracked source files and fails if it finds an email
address on @zdotllc.com that is NOT one of the provisioned, real business
mailboxes (see ALLOWLIST). That catches test fixtures, seed data, smoke-test
args, doc examples and placeholder addresses that reuse the company domain.

Usage:
    python3 scripts/check_dummy_email_policy.py [--files FILE...]   # default: git ls-files

Exit codes:
    0  clean — no policy violations
    1  violations found (CI fails)
    2  environment error (not a git repo / git unavailable)

Note: files in HISTORICAL/ARTIFACT paths (state snapshots, DB backups,
agent output logs, CHAT-LOG) are intentionally skipped — they are immutable
records of what happened, not places where new addresses are introduced.
"""
from __future__ import annotations

import re
import subprocess
import sys

EMAIL_RE = re.compile(r"([A-Za-z0-9._%+-]+)@zdotllc\.com", re.IGNORECASE)

# Real provisioned mailboxes on zdotllc.com (verified against
# communication/credentials.txt + CHAT-LOG). Any other local-part is a
# dummy/test/placeholder violation.
ALLOWLIST_LOCALPARTS = {
    "zerric", "bosslady", "bots", "info", "sales", "support",
    "ceo", "team",
    "ninjanerd", "clickclack", "mark", "meta", "manny", "seleena",
}

# Immutable history / binary artifacts — never rewritten, never scanned.
SKIP_PREFIXES = (
    "state/",
    "state-backup/",
    "backups-",
    "logs/",
    ".agent-company-ai/",
    "archive/",
)
SKIP_SUFFIXES = (".db", ".db.bak", ".db.bak-", ".pyc", ".pdf", ".wav", ".mp3", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip", ".gz", ".woff", ".woff2")

# Only these text formats are scanned. Binary/media assets (audio, images,
# fonts, archives) are skipped so the check stays fast on this repo.
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".mjs", ".sh", ".php", ".json", ".yaml", ".yml",
    ".toml", ".md", ".html", ".htm", ".css", ".cfg", ".ini", ".txt",
    ".svg", ".xml", ".csv", ".env", ".conf", ".sql",
}
SKIP_FILES = {"communication/credentials.txt", "CHANGELOG.md"}


def tracked_files() -> list[str]:
    """Return the list of git-tracked files (respects .gitignore)."""
    try:
        out = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return []
    return [ln for ln in out.stdout.splitlines() if ln.strip()]


def skip(path: str) -> bool:
    if path in SKIP_FILES:
        return True
    if any(path.startswith(p) for p in SKIP_PREFIXES):
        return True
    if any(path.endswith(s) for s in SKIP_SUFFIXES):
        return True
    return False


def scan_file(path: str) -> list[str]:
    """Return violation strings for a single file."""
    import os
    if os.path.splitext(path)[1].lower() not in TEXT_EXTENSIONS:
        return []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    violations = []
    for m in EMAIL_RE.finditer(text):
        local = m.group(1).lower()
        if local in ALLOWLIST_LOCALPARTS:
            continue
        # context snippet (the line)
        line_no = text.count("\n", 0, m.start()) + 1
        line = text.splitlines()[line_no - 1].strip()[:160]
        violations.append(f"  {path}:{line_no}: {m.group(0)}  <- {line}")
    return violations


def main(argv: list[str]) -> int:
    if "--files" in argv:
        i = argv.index("--files")
        files = [f for f in argv[i + 1:] if not f.startswith("--")]
    else:
        files = tracked_files()
        if not files:
            print("ERROR: could not enumerate git-tracked files (not a git repo?)")
            return 2

    all_violations: list[str] = []
    for f in files:
        if skip(f):
            continue
        all_violations.extend(scan_file(f))

    if all_violations:
        print("EMAIL-DOMAIN POLICY VIOLATIONS (dummy/test/placeholder on @zdotllc.com):")
        print("\n".join(all_violations))
        print("\nFIX: use @zdot-dummy.com for dummy/test/placeholder addresses.")
        print("     Real business mailboxes are allowlisted — see scripts/check_dummy_email_policy.py")
        return 1

    print("EMAIL-DOMAIN POLICY: OK — no non-allowlisted @zdotllc.com emails in tracked source.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
