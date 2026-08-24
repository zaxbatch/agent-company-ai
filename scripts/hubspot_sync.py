#!/usr/bin/env python3
"""HubSpot contact sync for SPREAD DA WORD outreach sprint (Phase 1, deliverable #1).

Reads contacts from .agent-company-ai/default/company.db (prospect_tool output)
and upserts them into HubSpot CRM by email. Uses the VERIFIED flow:
  GET  /crm/v3/objects/contacts/{email}?idProperty=email  -> exists?
  PATCH /crm/v3/objects/contacts/{id}                     -> update
  POST  /crm/v3/objects/contacts                          -> create
(Batch /upsert is currently returning 400 VALIDATION_ERROR on this token/account;
per-contact create/update is verified working 2026-08-24.)

Token: reads HUBSPOT_ACCESS_TOKEN from root .env. Never prints the token.

Usage:
  python3 scripts/hubspot_sync.py              # live upsert of all contacts with email
  python3 scripts/hubspot_sync.py --dry-run    # preview only (no API writes)
  python3 scripts/hubspot_sync.py --limit 5    # only the first 5 (by id)
  python3 scripts/hubspot_sync.py --verbose    # per-contact detail
  python3 scripts/hubspot_sync.py --verify     # print HubSpot total after sync

Exit codes: 0 ok, 2 config error, 3 API error.
"""
import argparse
import json
import re
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
DB_FILE = ROOT / ".agent-company-ai" / "default" / "company.db"
STATE_FILE = ROOT / "state" / "hubspot_sync.json"
HUBSPOT_API = "https://api.hubapi.com/crm/v3/objects/contacts"
VALID_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_token() -> str:
    if not ENV_FILE.exists():
        sys.exit("FATAL: .env not found at %s" % ENV_FILE)
    m = re.search(r"^HUBSPOT_ACCESS_TOKEN=(.+)$", ENV_FILE.read_text(), re.M)
    if not m:
        sys.exit("FATAL: HUBSPOT_ACCESS_TOKEN missing in .env")
    tok = m.group(1).strip().strip('"').strip("'")
    if not tok:
        sys.exit("FATAL: HUBSPOT_ACCESS_TOKEN is empty in .env")
    return tok


def fetch_contacts(limit: int | None):
    import sqlite3
    if not DB_FILE.exists():
        sys.exit("FATAL: company.db not found at %s" % DB_FILE)
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        "SELECT id, email, name, company, phone, status, source, tags "
        "FROM contacts WHERE email IS NOT NULL AND email != '' ORDER BY id"
    )
    rows = cur.fetchall()
    con.close()
    if limit:
        rows = rows[:limit]
    by_email: dict[str, dict] = {}
    for r in rows:
        email = r["email"].strip().lower()
        if not VALID_EMAIL.match(email):
            continue
        if email in by_email:
            continue
        by_email[email] = {
            "db_id": r["id"], "email": email,
            "name": (r["name"] or "").strip(), "company": (r["company"] or "").strip(),
            "phone": (r["phone"] or "").strip(), "status": (r["status"] or "").strip(),
            "source": (r["source"] or "").strip(), "tags": (r["tags"] or "").strip(),
        }
    return list(by_email.values())


def split_name(full: str):
    cleaned = re.sub(r"\s*\(.*?\)\s*", " ", full).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    parts = cleaned.split(" ", 1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    return first[:100], last[:100]


def props_for(c: dict) -> dict:
    first, last = split_name(c["name"])
    props = {"email": c["email"]}
    if first: props["firstname"] = first
    if last: props["lastname"] = last
    if c["company"]: props["company"] = c["company"][:255]
    if c["phone"]: props["phone"] = c["phone"][:50]
    return props


def _request(method: str, url: str, token: str, body: dict | None = None, retries: int = 2):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                raw = r.read() or b"{}"
                try:
                    return r.status, json.loads(raw)
                except Exception:
                    return r.status, {}
        except urllib.error.HTTPError as e:
            raw = e.read() or b"{}"
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {}  # HubSpot 404s come back as HTML — tolerate that
            if e.code == 429 and attempt < retries:
                time.sleep(2 * (attempt + 1))
                last = (e.code, parsed)
                continue
            return e.code, parsed
        except Exception as e:  # network blip
            last = (0, {"exception": str(e)})
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            return last
    return last


def upsert_contact(c: dict, token: str, verbose: bool):
    props = props_for(c)
    # 1) GET by email
    status, data = _request("GET", f"{HUBSPOT_API}/{c['email']}?idProperty=email", token)
    if status == 200:
        cid = data.get("id")
        s2, _ = _request("PATCH", f"{HUBSPOT_API}/{cid}", token, {"properties": props})
        if s2 == 200:
            if verbose: print(f"  ~ UPDATED {c['email']} (id {cid})")
            return "updated"
        return f"error:PATCH {s2}"
    if status == 404:
        s3, data3 = _request("POST", HUBSPOT_API, token, {"properties": props})
        if s3 in (200, 201):
            if verbose: print(f"  + CREATED {c['email']} (id {data3.get('id')})")
            return "created"
        return f"error:POST {s3} {data3}"
    return f"error:GET {status}"


def count_hubspot(token: str) -> int:
    """Contact count via search API (list endpoint has no total)."""
    try:
        s, data = _request("POST", HUBSPOT_API + "/search", token, {"limit": 1})
        return int(data.get("total") or 0) if s == 200 else -1
    except Exception:
        return -1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    token = load_token()
    contacts = fetch_contacts(args.limit)
    if not contacts:
        print("No syncable contacts (none with valid email). Nothing to do.")
        return
    print(f"Loaded {len(contacts)} deduped contact(s) with valid email from company.db")
    for c in contacts[: (len(contacts) if args.verbose else 5)]:
        print(f"  db#{c['db_id']:<3} {c['email']:<40} name={c['name'] or '-'!r:<30} company={c['company'] or '-'}")
    if not args.verbose and len(contacts) > 5:
        print(f"  ... and {len(contacts) - 5} more (use --verbose for all)")

    if args.dry_run:
        print("\nDRY RUN — no API calls made. Re-run without --dry-run to sync.")
        return

    created = updated = 0
    errors: list[str] = []
    for i, c in enumerate(contacts):
        try:
            r = upsert_contact(c, token, args.verbose)
        except Exception as e:
            r = f"exception:{e}"
        if r == "created": created += 1
        elif r == "updated": updated += 1
        else:
            errors.append(f"{c['email']}: {r}")
            print(f"  ! ERROR {c['email']}: {r}")
        time.sleep(0.25)  # gentle rate limit

    print(f"\nSYNC COMPLETE: {created} created, {updated} updated, {len(errors)} errored")
    if errors:
        print("Errors:")
        for e in errors:
            print("  -", e)

    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps({
        "last_run": datetime.now(timezone.utc).isoformat(),
        "loaded": len(contacts), "created": created, "updated": updated,
        "errored": len(errors), "dry_run": False,
    }, indent=2))
    print(f"State written to {STATE_FILE}")
    if args.verify:
        print(f"HubSpot contact total now: {count_hubspot(token)}")
    if errors:
        sys.exit(3)


if __name__ == "__main__":
    main()
