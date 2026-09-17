#!/usr/bin/env python3
"""agent_console.py — a privileged console for agents (email, SMS, shell).

WHY
---
Zerric, 2026-09-17: "give BossLady email, shell, and sms privileges."

BossLady's own report: "I can't send email or SMS from here, and I can't write
files. No channel, no shell." Directives were dying in chat.

WHAT "SHELL" MEANS HERE — read this before using it
--------------------------------------------------
This is NOT unrestricted root and it is not a raw shell. It is a bounded console:
each privilege is a NAMED CAPABILITY bound to a specific, reviewed command, and
the grant is per-agent in config/agent_privileges.json. Arbitrary command strings
are never executed. Everything is written to logs/agent_audit.log with the agent,
the capability, the exact command and the exit code.

That matters: an agent that could run any string could also delete the archive,
read credentials, or force-push the repo. If unrestricted shell is genuinely
needed, that is a harness change owned by whoever runs the agent runtime — not
something a peer script can safely hand out.

Usage:
  python3 scripts/agent_console.py --as BossLady caps
  python3 scripts/agent_console.py --as BossLady run status
  python3 scripts/agent_console.py --as BossLady run inventory
  python3 scripts/agent_console.py --as BossLady email --to zerric "message"
  python3 scripts/agent_console.py --as BossLady sms "message"
  python3 scripts/agent_console.py --as BossLady write TEAM-STATE.md "text"
  python3 scripts/agent_console.py --as BossLady audit --tail 20
"""
from __future__ import annotations
import argparse, fnmatch, json, os, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = ROOT / "config" / "agent_privileges.json"
AUDIT = ROOT / "logs" / "agent_audit.log"
VENV = ROOT / "venv" / "bin" / "python"

# A capability maps to ONE reviewed command. No agent-supplied strings.
CAPS = {
    "status":    ("company + system status summary", ["bash", "-lc",
                  "echo '--- git ---'; git log --oneline -5; echo; "
                  "echo '--- cron ---'; crontab -l | grep -v '^#'; echo; "
                  "echo '--- disk ---'; df -h / | tail -1"]),
    "jobs":      ("scheduled jobs", ["bash", "-lc", "crontab -l"]),
    "inventory": ("MilkUps audio inventory", [str(VENV), "scripts/milkups_inventory.py"]),
    "report":    ("recent TEAM-STATE activity", ["bash", "-lc",
                  "tail -40 TEAM-STATE.md"]),
    "logs":      ("recent audit + job logs", ["bash", "-lc",
                  "tail -20 logs/agent_audit.log 2>/dev/null; "
                  "tail -10 /tmp/outbox_flush.log 2>/dev/null"]),
    "queue":     ("outbound message queue", [str(VENV), "scripts/agent_outbox.py", "status"]),
}


def _config():
    return json.loads(CFG.read_text())


def _grant(agent):
    return _config()["agents"].get(agent)


def audit(agent, action, detail, result=""):
    AUDIT.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with AUDIT.open("a", encoding="utf-8") as f:
        f.write(f"{ts} | {agent:<10} | {action:<10} | {detail[:160]} | {result[:80]}\n")


def _denied(agent, text):
    for pat in _config().get("denied_always", []):
        if pat.lower() in text.lower():
            audit(agent, "DENIED", f"{pat} in: {text[:60]}", "blocked")
            raise SystemExit(f"blocked: pattern not permitted ({pat})")


def _can(agent, key, cap=None):
    g = _grant(agent)
    if not g:
        audit(agent, "DENIED", f"no grant for {agent}", "blocked")
        raise SystemExit(f"agent {agent!r} has no grants in {CFG.name}")
    if not g.get(key):
        audit(agent, "DENIED", f"{key} not granted", "blocked")
        raise SystemExit(f"{agent!r} lacks the {key} privilege")
    if cap is not None:
        caps = g.get("capabilities", [])
        if "*" not in caps and cap not in caps:
            audit(agent, "DENIED", f"capability {cap}", "blocked")
            raise SystemExit(f"{agent!r} lacks capability {cap!r} (has: {', '.join(caps)})")
    return g


def _may_write(g, path):
    rel = str(path).lstrip("./")
    for pat in g.get("write", []):
        if pat == "**" or fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(rel, pat.rstrip("/*") + "/*") \
           or rel == pat.rstrip("/*"):
            return True
    return False


def cmd_caps(a):
    g = _grant(a.agent)
    if not g:
        raise SystemExit(f"no grants for {a.agent!r}")
    print(f"{a.agent} ({g.get('role','?')}) — granted {g.get('granted')} by {g.get('granted_by')}")
    print(f"  email : {g.get('email')}")
    print(f"  sms   : {g.get('sms')}")
    print(f"  shell : {g.get('shell')}")
    print(f"  write : {', '.join(g.get('write', []))}")
    print(f"  caps  : {', '.join(g.get('capabilities', []))}")


def cmd_run(a):
    g = _can(a.agent, "shell", a.capability)
    if a.capability not in CAPS:
        raise SystemExit(f"unknown capability {a.capability!r}. Try: {', '.join(CAPS)}")
    desc, cmd = CAPS[a.capability]
    _denied(a.agent, " ".join(cmd))
    print(f"# {a.capability}: {desc}")
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    audit(a.agent, "run", f"{a.capability}: {' '.join(cmd)[:90]}", f"exit {r.returncode}")
    sys.stdout.write(r.stdout)
    if r.returncode != 0 and r.stderr:
        sys.stderr.write(r.stderr)
    print(f"\n[exit {r.returncode}]")


def cmd_email(a):
    _can(a.agent, "email")
    _denied(a.agent, a.body)
    body = a.body
    subj = a.subject or body.splitlines()[0][:70]
    out = subprocess.run([str(VENV), "scripts/agent_outbox.py", "send",
                          "--to", a.to, "--subject", subj, body],
                         cwd=ROOT, capture_output=True, text=True, timeout=90)
    audit(a.agent, "email", f"to={a.to} subj={subj[:60]}", f"exit {out.returncode}")
    sys.stdout.write(out.stdout or out.stderr)


def cmd_sms(a):
    _can(a.agent, "sms")
    _denied(a.agent, a.body)
    out = subprocess.run([str(VENV), "scripts/agent_outbox.py", "send",
                          "--to", a.to, "--sms", "--subject", "SMS", a.body],
                         cwd=ROOT, capture_output=True, text=True, timeout=90)
    audit(a.agent, "sms", f"to={a.to} len={len(a.body)}", f"exit {out.returncode}")
    sys.stdout.write(out.stdout or out.stderr)


def cmd_write(a):
    g = _can(a.agent, "shell")
    p = (ROOT / a.path).resolve()
    if not str(p).startswith(str(ROOT)):
        raise SystemExit("path escapes the repo")
    rel = str(p.relative_to(ROOT))
    if not _may_write(g, rel):
        audit(a.agent, "DENIED", f"write {rel}", "blocked")
        raise SystemExit(f"{a.agent!r} may not write {rel} (allowed: {', '.join(g.get('write', []))})")
    _denied(a.agent, a.content)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(a.content)
    audit(a.agent, "write", rel, f"{len(a.content)} bytes")
    print(f"wrote {rel} ({len(a.content)} bytes)")


def cmd_audit(a):
    if not AUDIT.exists():
        print("(no audit log yet)")
        return
    lines = AUDIT.read_text(encoding="utf-8", errors="replace").splitlines()
    for ln in lines[-a.tail:]:
        print(ln)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--as", dest="agent", required=True)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("caps"); c.set_defaults(func=cmd_caps)
    r = sub.add_parser("run"); r.add_argument("capability"); r.set_defaults(func=cmd_run)
    e = sub.add_parser("email"); e.add_argument("--to", default="boss")
    e.add_argument("--subject"); e.add_argument("body"); e.set_defaults(func=cmd_email)
    s = sub.add_parser("sms"); s.add_argument("--to", default="boss")
    s.add_argument("body"); s.set_defaults(func=cmd_sms)
    w = sub.add_parser("write"); w.add_argument("path"); w.add_argument("content")
    w.set_defaults(func=cmd_write)
    au = sub.add_parser("audit"); au.add_argument("--tail", type=int, default=20)
    au.set_defaults(func=cmd_audit)
    a = ap.parse_args()
    a.func(a)


if __name__ == "__main__":
    main()
