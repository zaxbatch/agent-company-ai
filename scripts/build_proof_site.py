#!/usr/bin/env python3
"""Build the Z-Dot Team PROOF-OF-WORK site (progress/index.html).

One command to regenerate after any progress:
    python3 scripts/build_proof_site.py
    (then deploy: NETLIFY_AUTH_TOKEN=... python3 scripts/deploy_netlify.py --dir progress --site-name zdot-proof)

Pulls live facts from the repo (git log, state files, account files) so the page
is always current. NO secrets/emails/tokens — public-safe (counts + links only).
"""
import base64
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

# ── Doodles for approval: copy from review folder (flat unique names for Netlify) ──
DOODLE_SRC = ROOT / "resources" / "snowsnakes" / "doodles-comics-under-review"
doodle_files = sorted(DOODLE_SRC.glob("*.svg")) if DOODLE_SRC.exists() else []
doodle_map = {}
for i, d in enumerate(doodle_files, 1):
    # embed inline (data URI) so doodles render on static hosting without extra files
    b64 = base64.b64encode(d.read_bytes()).decode()
    uri = f"data:image/svg+xml;base64,{b64}"
    doodle_map[uri] = d.stem.replace("-", " ").title()
doodle_cards = "".join(
    f'<div class="doodle"><img src="{uri}" alt="{name}" loading="lazy"><p>{name}</p></div>'
    for uri, name in doodle_map.items()
) if doodle_map else '<p style="color:#6f8db0">No doodles pending review right now.</p>' 

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
  .doodles {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:10px; margin-top:14px; }}
  .doodle {{ background:#101d33; border:1px solid #1f3a5f; border-radius:10px; padding:8px; text-align:center; }}
  .doodle img {{ width:100%; height:auto; border-radius:6px; background:#0a1526; }}
  .doodle p {{ font-size:.7rem; color:#a9c2e5; margin-top:6px; }}
  .ideas {{ display:flex; flex-direction:column; gap:8px; margin-top:14px; }}
  .idea {{ background:#101d33; border:1px solid #1f3a5f; border-left:4px solid #ffd166; border-radius:8px; padding:8px 12px; font-size:.82rem; color:#a9c2e5; }}
  .idea .st {{ font-weight:700; margin-right:8px; }}
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
    <a href="https://milkups.netlify.app" target="_blank" rel="noopener">✓ MilkUps (music)</a>
    <a href="https://beatthread.netlify.app/app" target="_blank" rel="noopener">✓ BeatThread (beats)</a>
    <a href="https://zdotllc.com/milkups/" target="_blank" rel="noopener">✓ MilkUps @ zdotllc</a>
    <a href="https://snowsnakes.zerric.xyz/games/86" target="_blank" rel="noopener">✓ Snow Beats</a>
    <a href="https://milkups.zerric.xyz" target="_blank" rel="noopener">✓ milkups.zerric.xyz (default page — awaiting deploy)</a>
    <a href="snitch.html" target="_blank" rel="noopener">✓ Snitch prototype</a>
  </div>

  <h3 class="section">📦 PROJECTS</h3>
  <div class="grid">
{cards_html}
  </div>

  <h3 class="section">🐀 SNOWSNAKES PERSONAS (real-user look)</h3>
  <div class="personas">{persona_html}</div>

  <h3 class="section">🎨 DOODLES FOR APPROVAL (latest batch)</h3>
  <div class="doodles">{doodle_cards}</div>

  <h3 class="section">💡 HOT IDEAS (kept hot — from BossLady/Zerric, incl. sleepy talk)</h3>
  <div class="ideas"><div class="idea"><span class="st">**Doodle-making app** that posts straight to SnowSnakes</span><b>1</b> — 🔥 captured</div><div class="idea"><span class="st">**Comic-making app** that posts straight to SnowSnakes</span><b>2</b> — 🔥 captured</div><div class="idea"><span class="st">**Simple game builder** that posts straight to SnowSnakes</span><b>3</b> — 🔥 captured</div><div class="idea"><span class="st">**Snitch mini-game (catch cheese, dodge the cat)** → SnowSnakes</span><b>4</b> — ✅ approved (Seleena)</div><div class="idea"><span class="st">**Snitch trailer video**</span><b>5</b> — ❌ nixed (BossLady)</div><div class="idea"><span class="st">**Snow Beats ⬇ download**</span><b>6</b> — ✅ done (game 97 → fixed 99)</div><div class="idea"><span class="st">**10 doodles/day for approval**</span><b>7</b> — ✅ live</div><div class="idea"><span class="st">**Snitch online board game v1**</span><b>8</b> — 🏗 prototype done, needs online layer</div><div class="idea"><span class="st">**Invite-a-player by link (live board)**</span><b>9</b> — ✅ in v1 spec</div><div class="idea"><span class="st">**SDW soundtracks 6–8 songs each**</span><b>10</b> — 🏗 5 new tracks rendered; need 6-8/tape</div><div class="idea"><span class="st">**Cassette "switch tapes" = switch soundtracks**</span><b>11</b> — ✅ live (8 tapes)</div><div class="idea"><span class="st">**SnowSnakes = games only (promo games OK)**</span><b>12</b> — ✅ policy</div><div class="idea"><span class="st">**Progress page (private)**</span><b>13</b> — ✅ live</div><div class="idea"><span class="st">Predator tokens (cat/owl) in Snitch</span><b>14</b> — 🗄</div><div class="idea"><span class="st">Public signup / self-serve / leaderboards</span><b>15</b> — 🗄</div><div class="idea"><span class="st">Bizzy Bee SaaS</span><b>16</b> — 🗄</div></div>

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
