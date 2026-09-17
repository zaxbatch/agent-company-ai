#!/usr/bin/env python3
"""Post a self-contained HTML game to SnowSnakes as the Z-Dot team account (zdot_team, id 85).

Contract (verified against scripts/post_batch_personas.py + live API):
  POST /api/games  multipart: title, description, icon, tags (COMMA-separated),
                              code (base64), code_encoding=base64
Tags MUST be a plain comma-separated string (a JSON string double-encodes and
produces the mangled-tag defect seen on games 96/97/99/100/122).

Verifies by read-back: the served `code` hash must equal the local file hash,
tags must come back as a clean list, and the author must be zdot_team.

Usage: venv/bin/python scripts/post_summit_snake.py <html> --title T --desc D --tags a,b,c [--dry-run]
Credential is read from communication/credentials.txt and never printed.
"""
from __future__ import annotations
import argparse, base64, hashlib, json, re, sys, urllib.error, urllib.request, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://snowsnakes.zerric.xyz/api"
CREDS = ROOT / "communication" / "credentials.txt"
ACCOUNT = "zdot_team"


def password(user=ACCOUNT):
    for line in CREDS.read_text().splitlines():
        if user in line:
            m = re.search(r"password:\s*([^\s|]+)", line)
            if m:
                return m.group(1)
    raise SystemExit(f"no credential for {user}")


def api(path, data=None, token=None, method="GET"):
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def login(user=ACCOUNT):
    st, res = api("/auth/login", {"username": user, "password": password(user)}, method="POST")
    tok = res.get("token") if isinstance(res, dict) else None
    if not tok:
        raise SystemExit(f"login failed for {user}: {st} {res}")
    return tok, (res.get("user") or {})


def post_game(tok, title, desc, icon, tags, code_bytes):
    b64 = base64.b64encode(code_bytes).decode()
    boundary = "----zdot" + uuid.uuid4().hex
    parts = {"title": title, "description": desc, "icon": icon,
             "tags": ",".join(tags), "code": b64, "code_encoding": "base64"}
    body = b""
    for k, v in parts.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n"
                 f"{v}\r\n").encode()
    body += f"--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{BASE}/games", data=body, method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                 "Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            raw = r.read().decode()
            return r.status, (json.loads(raw) if raw.strip() else None)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--title", required=True)
    ap.add_argument("--desc", required=True)
    ap.add_argument("--icon", default="\U0001f3d4\ufe0f")
    ap.add_argument("--tags", required=True, help="comma-separated")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    src = Path(a.html)
    code = src.read_bytes()
    local_sha = hashlib.sha256(code).hexdigest()
    tags = [t.strip() for t in a.tags.split(",") if t.strip()]
    print(f"file   : {src}  ({len(code)} bytes)")
    print(f"sha256 : {local_sha}")
    print(f"title  : {a.title}\nicon   : {a.icon}\ntags   : {tags}")
    if a.dry_run:
        print("[dry-run] not posting")
        return 0

    tok, user = login()
    print(f"logged in as {user.get('username')} (id {user.get('id')}) [credential not printed]")

    st, res = post_game(tok, a.title, a.desc, a.icon, tags, code)
    print(f"POST /api/games -> {st}")
    if not isinstance(res, dict) or not res.get("id"):
        print("FAILED:", res)
        return 1
    gid = res["id"]
    print(f"created game id={gid}")

    # ---- READ-BACK VERIFICATION (never trust the POST response alone) ----
    print("\n-- read-back verification --")
    st2, live = api(f"/games/{gid}")
    checks = []
    served = (live or {}).get("code") or ""
    served_sha = hashlib.sha256(served.encode()).hexdigest()
    checks.append(("served code sha == local sha", served_sha == local_sha,
                   f"local={local_sha[:16]} served={served_sha[:16]} len={len(served)}"))
    checks.append(("author is zdot_team", (live or {}).get("author_name") == ACCOUNT,
                   str((live or {}).get("author_name"))))
    lt = (live or {}).get("tags")
    clean = isinstance(lt, list) and all(re.fullmatch(r"[a-z0-9 \-]+", str(t)) for t in lt)
    checks.append(("tags clean list (no mangled JSON)", clean, json.dumps(lt)))
    checks.append(("title matches", (live or {}).get("title") == a.title, str((live or {}).get("title"))))
    checks.append(("has code", len(served) > 3000, f"{len(served)} chars"))

    # the public player page must render the game
    try:
        with urllib.request.urlopen(f"https://snowsnakes.zerric.xyz/games/{gid}", timeout=30) as r:
            checks.append(("public page HTTP 200", r.status == 200, str(r.status)))
    except Exception as e:
        checks.append(("public page HTTP 200", False, str(e)[:120]))

    for name, ok, extra in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}  ({extra})")
    out = ROOT / "content" / "snowsnakes" / "summit-snake-post.json"
    out.write_text(json.dumps({"id": gid, "url": f"https://snowsnakes.zerric.xyz/games/{gid}",
                               "title": a.title, "tags": lt, "author": ACCOUNT,
                               "local_sha256": local_sha, "served_sha256": served_sha,
                               "checks": [{"check": c, "pass": p, "detail": d} for c, p, d in checks]},
                              indent=2))
    print(f"\nrecord -> {out.relative_to(ROOT)}")
    return 0 if all(p for _, p, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
