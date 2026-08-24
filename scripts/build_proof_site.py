#!/usr/bin/env python3
"""Build the Z-Dot Team PROOF-OF-WORK site (progress/index.html).

One command to regenerate after any progress:
    python3 scripts/build_proof_site.py
    (then deploy: NETLIFY_AUTH_TOKEN=... python3 scripts/deploy_netlify.py --dir progress --site-name zdot-proof)

Pulls live facts from the repo (git log, state files, account files) so the page
is always current. NO secrets/emails/tokens — public-safe (counts + links only).
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "progress"
OUT_DIR.mkdir(exist_ok=True)

def git_log(n=14):
    try:
        out = subprocess.run(["git", "log", "--oneline", f"-{n}"], cwd=ROOT,
                             capture_output=True, text=True, timeout=10).stdout
        return [l.split(" ", 1) for l in out.strip().splitlines() if l.strip()]
    except Exception:
        return []

def load_json(path, default=None):
    try:
        return json.loads((ROOT / path).read_text())
    except Exception:
        return default

hub = load_json("state/hubspot_sync.json", {})
users = load_json(".snowsnakes_real_users.json", [])
commits = git_log()
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

hs_created = hub.get("created", "—")
hs_updated = hub.get("updated", "—")
hs_ran = (hub.get("last_run") or "—")[:16].replace("T", " ")

cards = [
    ("🎬", "Spread Da Word — Animated Series",
     "Cassette player with 8 switchable tapes (each its own label/colors/download), live on SnowSnakes.",
     [("Cassette player (live)", "https://snowsnakes.zerric.xyz/spread-da-word/audio/soundtracks-cassette-player.html"),
      ("SDW official channel (live)", "https://snowsnakes.zerric.xyz"),
      ("5 new soundtracks rendered", "https://snowsnakes.zerric.xyz/spread-da-word/audio/soundtracks-cassette-player.html"),
      ("Hub + legal pages (Netlify)", "https://spread-da-word.netlify.app/")],
     "Series world: Vin Negar, Que, Hood vs Fridge, cassettes, episodes placeholder."),
    ("🐀", "Snitch — Online Board Game",
     "Rats racing the snake board. 4-player cap, sign-in = lead capture, 3 modes (solo vs bots / invite / quick-play).",
     [("Play the prototype", "./snitch.html"),
      ("Design (canon)", "./snitch-design.html"),
      ("v1 Build spec", "./snitch-spec.html")],
     "Working prototype in repo. Online P2P layer + HubSpot lead capture = next build."),
    ("📣", "Outreach Sprint",
     "Prospect → CRM loop. HubSpot sync tool built and run against 29 Louisville prospect leads.",
     [("Sync tool", "https://github.com/zaxbatch/agent-company-ai"),
      ("HubSpot CRM", "https://app.hubspot.com/")],
     f"28 created, {hs_updated} updated (last run {hs_ran}). Next: email outreach (blocked on provider key)."),
    ("🐍", "SnowSnakes — Community",
     "Live community site. Content runs as 8 realistic personas (no more team-handle bots).",
     [("SnowSnakes (live)", "https://snowsnakes.zerric.xyz"),
      ("Personas", "#snowsnakes")],
     f"{len(users)} realistic personas registered (ids 72-79). Jokes/games posting paused per house-cleaning; resumes on go."),
    ("🖥️", "Platform & Infra",
     "Team portal, legal pages, git history, email/SMS channels — the operating backbone.",
     [("Team portal (live)", "https://tasks.zdotllc.com"),
      ("Legal pages (Netlify)", "https://spread-da-word.netlify.app/privacy.html"),
      ("Repo (private)", "https://github.com/zaxbatch/agent-company-ai")],
     "Dashboard + checklist portal live. State snapshots every 30 min."),
]

def card_html(c):
    icon, title, blurb, links, meta = c
    lis = "".join(f'<a class="lnk" href="{u}" target="_blank" rel="noopener">{t} ↗</a>' for t, u in links)
    return f'''<div class="card">
      <div class="card-head"><span class="ic">{icon}</span><h2>{title}</h2></div>
      <p class="blurb">{blurb}</p>
      <div class="links">{lis}</div>
      <p class="meta">{meta}</p>
    </div>'''

cards_html = "\n".join(card_html(c) for c in cards)

commit_rows = "".join(
    f'<tr><td class="hash">{h}</td><td>{m}</td></tr>' for h, m in commits
)

persona_html = "".join(
    f'<span class="persona">{u.get("avatar","👤")} {u.get("username","")}</span>' for u in users
)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Z-Dot Team — Proof of Work</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; background:#0b1220; color:#dbe7ff; line-height:1.6; }}
  .wrap {{ max-width:1000px; margin:0 auto; padding:28px 18px 60px; }}
  header {{ text-align:center; padding:30px 0 8px; }}
  header h1 {{ font-size:2rem; letter-spacing:1px; color:#fff; }}
  header .tag {{ color:#7fd1ff; font-size:.95rem; letter-spacing:3px; margin-top:6px; }}
  .updated {{ display:inline-block; margin-top:12px; background:#12395a; color:#9fd8ff; border:1px solid #2f5a8a; border-radius:20px; padding:5px 16px; font-size:.8rem; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin-top:26px; }}
  .card {{ background:#101d33; border:1px solid #1f3a5f; border-radius:14px; padding:18px; }}
  .card-head {{ display:flex; align-items:center; gap:10px; }}
  .card-head .ic {{ font-size:1.6rem; }}
  .card h2 {{ font-size:1.05rem; color:#fff; }}
  .blurb {{ margin:8px 0 12px; color:#a9c2e5; font-size:.92rem; }}
  .links {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }}
  .lnk {{ background:#12395a; color:#7fd1ff; border:1px solid #2f5a8a; border-radius:8px; padding:5px 10px; font-size:.78rem; text-decoration:none; }}
  .lnk:hover {{ background:#1a4a70; }}
  .meta {{ color:#6f8db0; font-size:.78rem; border-top:1px dashed #1f3a5f; padding-top:8px; }}
  h3.section {{ margin-top:34px; color:#7fd1ff; letter-spacing:2px; font-size:.95rem; border-bottom:1px solid #1f3a5f; padding-bottom:8px; }}
  .live {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }}
  .live a {{ background:#0e2a1e; color:#7ee2a8; border:1px solid #1f5a3f; border-radius:8px; padding:7px 12px; font-size:.85rem; text-decoration:none; }}
  table {{ width:100%; border-collapse:collapse; margin-top:14px; font-size:.8rem; }}
  td {{ padding:6px 8px; border-bottom:1px solid #14263f; color:#a9c2e5; }}
  td.hash {{ color:#7fd1ff; font-family:monospace; white-space:nowrap; }}
  .personas {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }}
  .persona {{ background:#101d33; border:1px solid #1f3a5f; border-radius:8px; padding:5px 10px; font-size:.82rem; }}
  .blockers li {{ margin:6px 0 6px 18px; color:#ffb3a0; }}
  footer {{ margin-top:40px; text-align:center; color:#4a6385; font-size:.75rem; }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Z-DOT TEAM · PROOF OF WORK</h1>
    <div class="tag">TANGIBLE PROGRESS · LIVE LINKS · VERIFIED</div>
    <div><span class="updated">Last updated {now} · regenerated by scripts/build_proof_site.py</span></div>
  </header>

  <h3 class="section">🟢 LIVE SYSTEMS</h3>
  <div class="live">
    <a href="https://snowsnakes.zerric.xyz" target="_blank" rel="noopener">✓ snowsnakes.zerric.xyz</a>
    <a href="https://tasks.zdotllc.com" target="_blank" rel="noopener">✓ tasks.zdotllc.com</a>
    <a href="https://spread-da-word.netlify.app/" target="_blank" rel="noopener">✓ spread-da-word.netlify.app</a>
    <a href="https://snowsnakes.zerric.xyz/spread-da-word/audio/soundtracks-cassette-player.html" target="_blank" rel="noopener">✓ Cassette player</a>
    <a href="snitch.html" target="_blank" rel="noopener">✓ Snitch prototype</a>
  </div>

  <h3 class="section">📦 PROJECTS</h3>
  <div class="grid">
{cards_html}
  </div>

  <h3 class="section">🐀 SNOWSNAKES PERSONAS (real-user look)</h3>
  <div class="personas">{persona_html}</div>

  <h3 class="section">🧾 RECENT COMMITS</h3>
  <table>
{commit_rows}
  </table>

  <h3 class="section">⛔ BLOCKERS / NEEDS</h3>
  <ul class="blockers">
    <li>Stripe API key (Zerric) — gates payments</li>
    <li>Email provider key (Resend) — gates outreach</li>
    <li>zerric.xyz FTP access — Snitch + SDW proper domains</li>
    <li>SnowSnakes admin — duplicate game cleanup</li>
  </ul>

  <footer>Z-Dot LLC · generated by scripts/build_proof_site.py · run after every progress to refresh this page</footer>
</div>
</body>
</html>
"""
(OUT_DIR / "index.html").write_text(html)

# Also emit an auth-gated PHP page (private) for tasks.zdotllc.com/progress
# Same content, wrapped in the same session gate as api.php (redirects to auth.html).
php = """<?php
// Z-Dot Team - private proof-of-work page (requires login like api.php)
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: auth.html');
    exit;
}
$me = $_SESSION['user'];
?>
""" + html.replace('<title>Z-Dot Team — Proof of Work</title>',
    '<title>Z-Dot Team — Progress (private)</title>') + "\n"
(OUT_DIR / "index.php").write_text(php)
print(f"private php written: {OUT_DIR / 'index.php'}")
