#!/usr/bin/env python3
"""Deploy Bizzy-Bee-Solutions landing pages to Netlify.

Publishes every HTML file in the landing-pages directory to a live
Netlify static site and prints the public URLs.

Requirements
------------
* ``NETLIFY_AUTH_TOKEN`` environment variable set (Netlify Personal Access
  Token). Create one at https://app.netlify.com/user/applications#personal-access-tokens

Usage
-----
    NETLIFY_AUTH_TOKEN=nfp_xxxx scripts/deploy_netlify.py
    NETLIFY_AUTH_TOKEN=nfp_xxxx scripts/deploy_netlify.py --site-name bizzybee-landing
    scripts/deploy_netlify.py --dir .agent-company-ai/bizzy-bee-solutions/landing_pages

How it works
------------
1. Creates (or reuses) a Netlify site named ``--site-name`` (default
   ``bizzy-bee-solutions-landing``).
2. Bundles every HTML file in the directory into a ZIP (with a tiny
   ``index.html`` hub so the site root resolves instead of 404ing).
3. Uploads the ZIP via Netlify's direct-upload deploy API.
4. Prints the live site URL and each page's public URL.

Exit codes: 0 on success, 2 on missing token, 3 on API error.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import zipfile
from pathlib import Path

import httpx

API = "https://api.netlify.com/api/v1"
DEFAULT_SITE_NAME = "bizzy-bee-solutions-landing"
DEFAULT_DIR = Path(".agent-company-ai/bizzy-bee-solutions/landing_pages")

_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bizzy-Bee-Solutions — Free Resources</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0a0a0a; color: #e0e0e0; max-width: 720px; margin: 0 auto;
         padding: 48px 24px; line-height: 1.6; }
  h1 { color: #fff; }
  a { display: block; background: #1e293b; color: #38bdf8; text-decoration: none;
      padding: 16px 20px; border-radius: 8px; margin: 12px 0;
      border: 1px solid #334155; }
  a:hover { background: #1e3a5f; }
</style>
</head>
<body>
<h1>Free Resources from Bizzy-Bee-Solutions</h1>
<p>Pick a free guide below:</p>
<a href="/free-local-lead-machine-playbook.html">The Local Lead Machine Playbook (Free E-Book)</a>
<a href="/free-local-business-ebook.html">The Local Business Online Visibility Playbook (Free E-Book)</a>
<a href="/free-website-audit.html">Free Website &amp; Online Presence Audit</a>
</body>
</html>
"""


def _require_token() -> str:
    token = os.environ.get("NETLIFY_AUTH_TOKEN", "").strip()
    if not token:
        print(
            "ERROR: NETLIFY_AUTH_TOKEN is not set.\n"
            "  Get a token at https://app.netlify.com/user/applications#personal-access-tokens\n"
            "  then run:  NETLIFY_AUTH_TOKEN=nfp_xxx scripts/deploy_netlify.py",
            file=sys.stderr,
        )
        sys.exit(2)
    return token


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _find_site(client: httpx.Client, token: str, site_name: str) -> dict | None:
    """Look up an existing site by its name/subdomain."""
    page = 1
    while page <= 10:
        r = client.get(
            f"{API}/sites",
            params={"per_page": 100, "page": page},
            headers=_headers(token),
            timeout=30,
        )
        if r.status_code != 200:
            return None
        sites = r.json()
        if not sites:
            return None
        for s in sites:
            if s.get("name") == site_name or s.get("subdomain") == site_name:
                return s
        page += 1
    return None


def _get_or_create_site(client: httpx.Client, token: str, site_name: str) -> dict:
    """Create a new site or return an existing one with the same name."""
    r = client.post(
        f"{API}/sites",
        headers=_headers(token),
        json={"name": site_name, "force_ssl": True},
        timeout=30,
    )
    if r.status_code in (200, 201):
        return r.json()
    # Name collision or other error -> try to reuse existing site
    existing = _find_site(client, token, site_name)
    if existing:
        print(f"  Reusing existing site '{site_name}' ({existing['id']})")
        return existing
    print(f"ERROR: could not create site: {r.status_code} {r.text}", file=sys.stderr)
    sys.exit(3)


def _build_zip(html_dir: Path) -> bytes:
    """Bundle all HTML files + an index hub into a deployable ZIP."""
    buf = io.BytesIO()
    files = sorted(html_dir.glob("*.html"))
    if not files:
        print(f"ERROR: no HTML files found in {html_dir}", file=sys.stderr)
        sys.exit(3)
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        has_index = False
        for f in files:
            zf.writestr(f.name, f.read_text(encoding="utf-8"))
            if f.name == "index.html":
                has_index = True
        if not has_index:
            # only write the generic hub when the site has no real index.html
            zf.writestr("index.html", _INDEX_HTML)
    return buf.getvalue()


def deploy(site_name: str, html_dir: Path) -> None:
    token = _require_token()
    html_dir = html_dir.resolve()
    print(f"Deploying landing pages from: {html_dir}")
    print(f"Target Netlify site: {site_name}")

    with httpx.Client() as client:
        site = _get_or_create_site(client, token, site_name)
        site_id = site["id"]
        ssl_url = site.get("ssl_url") or site.get("url") or f"https://{site.get('subdomain','?')}"
        print(f"  Site ID: {site_id}")
        print(f"  Site URL: {ssl_url}")

        payload = _build_zip(html_dir)
        print(f"  Uploading ZIP bundle ({len(payload)} bytes)...")
        r = client.post(
            f"{API}/sites/{site_id}/deploys",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/zip",
            },
            content=payload,
            timeout=120,
        )
        if r.status_code not in (200, 201):
            print(f"ERROR: deploy failed: {r.status_code} {r.text}", file=sys.stderr)
            sys.exit(3)
        deploy_data = r.json()
        deploy_id = deploy_data.get("id", "?")
        print(f"  Deploy ID: {deploy_id}")

        # Resolve live URLs
        live_site = (
            deploy_data.get("ssl_url")
            or deploy_data.get("url")
            or ssl_url
        )
        print("\n=== LANDING PAGES PUBLISHED ===")
        print(f"Site root:   {live_site}")
        for f in sorted(html_dir.glob("*.html")):
            print(f"  {live_site}/{f.name}")
        print("\nNote: Netlify may take a few seconds for the deploy to go live.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--site-name", default=DEFAULT_SITE_NAME,
        help=f"Netlify site name (subdomain). Default: {DEFAULT_SITE_NAME}",
    )
    parser.add_argument(
        "--dir", type=Path, default=DEFAULT_DIR,
        help="Directory containing the landing-page HTML files.",
    )
    args = parser.parse_args()
    deploy(args.site_name, args.dir)


if __name__ == "__main__":
    main()
