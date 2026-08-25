#!/usr/bin/env bash
# Instant chat logger — append a message to CHAT-LOG.md the moment it happens.
# Usage: ./scripts/log_chat.sh "Speaker" "Message text"
cd "$(dirname "$0")/.."
python3 scripts/log_chat.py "$1" "$2"
