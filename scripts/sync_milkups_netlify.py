#!/usr/bin/env python3
"""Sync the milkups.netlify.app mirror to match the live milkups.zerric.xyz content.

Builds a static bundle (brand page + all 3 cuts + audio + qr assets) and deploys
it to the existing Netlify site via the direct-upload zip API.
"""
import io, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent.parent
SITE_ID = "4a780cec-282e-4d35-aa43-f77c70080554"   # netlify site "milkups"
LIVE = "https://milkups.zerric.xyz"
STAGE = Path("/tmp/milkups_netlify")

def token():
    creds = (ROOT / "communication" / "credentials.txt").read_text(errors="replace")
    m = re.search(r"(?im)^netlify\s*[:=]\s*(\S+)", creds)
    if not m: raise SystemExit("netlify token not found")
    return m.group(1).strip()

def build():
    if STAGE.exists(): shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True)
    src = ROOT / "content" / "milkups"

    # brand page
    shutil.copy(src / "index.html", STAGE / "index.html")
    # shared assets
    shutil.copytree(src / "assets", STAGE / "assets")

    # CUT 1 - full cut (album.html -> album/index.html)
    (STAGE / "album").mkdir()
    shutil.copy(src / "album.html", STAGE / "album" / "index.html")
    shutil.copytree(src / "audio", STAGE / "album" / "audio")
    shutil.copy(src / "TheShelvesRaisedUs-milkups-464737.zip",
                STAGE / "album" / "TheShelvesRaisedUs-milkups-464737.zip")

    # CUT 3 - tracker
    shutil.copytree(src / "tracker", STAGE / "tracker",
                    ignore=shutil.ignore_patterns("wav", "manifest.json"))

    # CUT 2 - banger cut: page from local, audio pulled from live
    v2 = STAGE / "album" / "v2"; (v2 / "audio").mkdir(parents=True); (v2 / "assets").mkdir()
    shutil.copy("/tmp/v2-index.html", v2 / "index.html")
    slugs = ["trap-cabnets","lofi-midnight","electro-neon","pop-radio",
             "country-fridge","funk-cookout","synthwave-retro","icy"]
    with httpx.Client(timeout=120, follow_redirects=True) as c:
        for s in slugs:
            r = c.get(f"{LIVE}/album/v2/audio/banger-{s}.mp3")
            r.raise_for_status()
            (v2 / "audio" / f"banger-{s}.mp3").write_bytes(r.content)
            print(f"  pulled banger-{s}.mp3 {len(r.content)}b")
        for a in ("qr-zdotllc-5.png", "qr-zdotllc.png"):
            r = c.get(f"{LIVE}/album/v2/assets/{a}")
            if r.status_code == 200: (v2 / "assets" / a).write_bytes(r.content)
    return STAGE

def zipit(stage):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p in sorted(stage.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(stage).as_posix())
    return buf.getvalue()

def main():
    stage = build()
    files = [p for p in stage.rglob("*") if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    print(f"bundle: {len(files)} files, {total/1e6:.1f} MB")
    data = zipit(stage)
    print(f"zip: {len(data)/1e6:.1f} MB")
    r = httpx.post(f"https://api.netlify.com/api/v1/sites/{SITE_ID}/deploys",
                   headers={"Authorization": f"Bearer {token()}",
                            "Content-Type": "application/zip"},
                   content=data, timeout=600)
    print("deploy status:", r.status_code)
    if r.status_code >= 300:
        print(r.text[:500]); return 1
    d = r.json()
    print("deploy id:", d.get("id"), "\nurl:", d.get("ssl_url") or d.get("url"), "\nstate:", d.get("state"))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
