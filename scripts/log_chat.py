#!/usr/bin/env python3
"""Append a chat message to the persistent team chat log (CHAT-LOG.md).

Usage:
  python3 scripts/log_chat.py "speaker" "message"
Appends a timestamped entry. Safe: never reads/writes secrets; plain text only.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent / "state" / "CHAT-LOG.md"

def main():
    if len(sys.argv) < 3:
        print("usage: log_chat.py <speaker> <message>")
        sys.exit(1)
    speaker = sys.argv[1]
    msg = " ".join(sys.argv[2:])
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    LOG.parent.mkdir(exist_ok=True)
    if not LOG.exists():
        LOG.write_text("# Z-Dot Team Chat Log (persistent memory)\n\n> Every chat message is appended here so nothing is lost.\n\n")
    with LOG.open("a") as f:
        f.write(f"### {ts} — {speaker}\n{msg}\n\n")
    print(f"logged to {LOG}")

if __name__ == "__main__":
    main()
