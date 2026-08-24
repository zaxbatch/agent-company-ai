<?php
// Z-Dot Team — "See what we're working on" (PRIVATE, auth-gated)
// Serves the team proof-of-work page. Requires login session (same gate as api.php).
// Content is rendered server-side from proof.json — NO public iframe, NOT public.
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: auth.html');
    exit;
}
$me = $_SESSION['user'];
$json = @file_get_contents(__DIR__ . '/proof.json');
$data = $json ? json_decode($json, true) : null;
if (!$data) { $data = ['updated'=>'unknown','live'=>[],'projects'=>[],'commits'=>[],'personas'=>[],'blockers'=>[]]; }

function esc($s){ return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }

$live = '';
foreach ($data['live'] as $l) {
    $live .= '<a href="' . esc($l['url']) . '" target="_blank" rel="noopener">✓ ' . esc($l['name']) . '</a>';
}
$cards = '';
foreach ($data['projects'] as $c) {
    $links = '';
    foreach ($c['links'] as $ln) {
        $links .= '<a class="lnk" href="' . esc($ln[1]) . '" target="_blank" rel="noopener">' . esc($ln[0]) . ' ↗</a>';
    }
    $cards .= '<div class="card"><div class="card-head"><span class="ic">' . esc($c['icon']) . '</span><h2>' . esc($c['title']) . '</h2></div>' .
              '<p class="blurb">' . esc($c['blurb']) . '</p><div class="links">' . $links . '</div>' .
              '<p class="meta">' . esc($c['meta']) . '</p></div>';
}
$commits = '';
foreach ($data['commits'] as $cm) {
    $commits .= '<tr><td class="hash">' . esc($cm[0]) . '</td><td>' . esc($cm[1]) . '</td></tr>';
}
$personas = '';
foreach ($data['personas'] as $p) {
    $personas .= '<span class="persona">' . esc($p['avatar']) . ' ' . esc($p['username']) . '</span>';
}
$blockers = '';
foreach ($data['blockers'] as $b) { $blockers .= '<li>' . esc($b) . '</li>'; }
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Z-Dot Team — Progress (Private)</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; background:#0b1220; color:#dbe7ff; line-height:1.6; }
  .wrap { max-width:1000px; margin:0 auto; padding:28px 18px 60px; }
  header { text-align:center; padding:24px 0 8px; }
  header h1 { font-size:1.8rem; color:#fff; }
  header .tag { color:#7fd1ff; font-size:.9rem; letter-spacing:3px; margin-top:6px; }
  .updated { display:inline-block; margin-top:12px; background:#12395a; color:#9fd8ff; border:1px solid #2f5a8a; border-radius:20px; padding:5px 16px; font-size:.8rem; }
  .priv { display:inline-block; margin-top:12px; margin-left:8px; background:#2a1212; color:#ffb3a0; border:1px solid #5a2f2f; border-radius:20px; padding:5px 14px; font-size:.75rem; }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin-top:26px; }
  .card { background:#101d33; border:1px solid #1f3a5f; border-radius:14px; padding:18px; }
  .card-head { display:flex; align-items:center; gap:10px; }
  .card-head .ic { font-size:1.6rem; }
  .card h2 { font-size:1.05rem; color:#fff; }
  .blurb { margin:8px 0 12px; color:#a9c2e5; font-size:.92rem; }
  .links { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:12px; }
  .lnk { background:#12395a; color:#7fd1ff; border:1px solid #2f5a8a; border-radius:8px; padding:5px 10px; font-size:.78rem; text-decoration:none; }
  .lnk:hover { background:#1a4a70; }
  .meta { color:#6f8db0; font-size:.78rem; border-top:1px dashed #1f3a5f; padding-top:8px; }
  h3.section { margin-top:34px; color:#7fd1ff; letter-spacing:2px; font-size:.95rem; border-bottom:1px solid #1f3a5f; padding-bottom:8px; }
  .live { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
  .live a { background:#0e2a1e; color:#7ee2a8; border:1px solid #1f5a3f; border-radius:8px; padding:7px 12px; font-size:.85rem; text-decoration:none; }
  table { width:100%; border-collapse:collapse; margin-top:14px; font-size:.8rem; }
  td { padding:6px 8px; border-bottom:1px solid #14263f; color:#a9c2e5; }
  td.hash { color:#7fd1ff; font-family:monospace; white-space:nowrap; }
  .personas { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
  .persona { background:#101d33; border:1px solid #1f3a5f; border-radius:8px; padding:5px 10px; font-size:.82rem; }
  .blockers li { margin:6px 0 6px 18px; color:#ffb3a0; }
  .nav { margin-top:18px; text-align:center; }
  .nav a { background:#1565c0; color:#fff; text-decoration:none; padding:8px 16px; border-radius:8px; font-size:.85rem; }
  footer { margin-top:40px; text-align:center; color:#4a6385; font-size:.75rem; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Z-DOT TEAM · PROOF OF WORK</h1>
    <div class="tag">TANGIBLE PROGRESS · PRIVATE · TEAM ONLY</div>
    <div>
      <span class="updated">Last updated <?php echo esc($data['updated']); ?></span>
      <span class="priv">🔒 Private — logged in as <?php echo esc($me['username'] ?? 'team'); ?></span>
    </div>
    <div class="nav"><a href="index.html">← Back to Task Dashboard</a></div>
  </header>

  <h3 class="section">🟢 LIVE SYSTEMS</h3>
  <div class="live"><?php echo $live ?: '<p style="color:#6f8db0">—</p>'; ?></div>

  <h3 class="section">📦 PROJECTS</h3>
  <div class="grid"><?php echo $cards ?: '<p style="color:#6f8db0">—</p>'; ?></div>

  <h3 class="section">🐀 SNOWSNAKES PERSONAS (real-user look)</h3>
  <div class="personas"><?php echo $personas ?: '<p style="color:#6f8db0">—</p>'; ?></div>

  <h3 class="section">🧾 RECENT COMMITS</h3>
  <table><?php echo $commits ?: '<tr><td>—</td></tr>'; ?></table>

  <h3 class="section">⛔ BLOCKERS / NEEDS</h3>
  <ul class="blockers"><?php echo $blockers ?: '<li>—</li>'; ?></ul>

  <footer>Z-Dot LLC · generated by scripts/build_proof_site.py · private at tasks.zdotllc.com/progress</footer>
</div>
</body>
</html>
