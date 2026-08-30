#!/usr/bin/env python3
"""
state_snapshot.py — Continuity snapshot: captures team state so a reboot never
loses memory. Safe for git: excludes sensitive columns (emails, keys, bodies).

Usage:  python3 scripts/state_snapshot.py
Output: state-backup/state-<timestamp>.json  (+ pushes to git if --commit)
"""
import json, sqlite3, sys, os, re
from datetime import datetime, timezone

DB = ".agent-company-ai/default/company.db"
OUT_DIR = "state-backup"
SENSITIVE = {"email","password","api_key","token","secret","address","keystore_path","tx_hash","to_address","from_address","body","body_text","body_html","keystore","private"}

def mask_val(v, col):
    if col in SENSITIVE or (isinstance(v, str) and re.search(r'(?i)(password|api_key|secret|token|sk_live|sk_test|pat-|@gmail|@proton)', v)):
        return "***"
    return v

def dump_table(cur, tbl):
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tbl})").fetchall()]
    rows = []
    for r in cur.execute(f"SELECT * FROM {tbl}").fetchall():
        row = {}
        for c, v in zip(cols, r):
            row[c] = mask_val(v, c)
        rows.append(row)
    return {"table": tbl, "count": len(rows), "rows": rows}

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": "Sanitized continuity snapshot. Sensitive fields masked (***). "
                "Restore: this JSON documents what was in flight so work can resume after any disruption.",
        "tables": {t: dump_table(cur, t) for t in tables},
    }
    con.close()
    os.makedirs(OUT_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = f"{OUT_DIR}/state-{ts}.json"
    with open(path, "w") as f:
        json.dump(state, f, indent=1, default=str)
    print("snapshot written:", path, "| tables:", len(tables))
    # keep only last 20 snapshots (files only — never remove subdirs like offboarding-evidence)
    snaps = sorted(os.listdir(OUT_DIR))
    for old in snaps[:-20]:
        full = os.path.join(OUT_DIR, old)
        if os.path.isfile(full):
            os.remove(full)
            print("pruned:", old)
        else:
            print("skipped (dir, kept):", old)
    if "--commit" in sys.argv:
        os.system(f"git add {OUT_DIR} && git commit -q -m 'state snapshot {ts} [skip ci]' && git push -q origin main 2>&1 | tail -1")
        print("committed + pushed")

if __name__ == "__main__":
    main()
