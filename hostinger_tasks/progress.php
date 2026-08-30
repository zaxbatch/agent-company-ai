<?php
// Z-Dot Team — LIVE PROGRESS (dynamic, real-time task dashboard)
// Auth-gated (same session as api.php). Task data is rendered client-side from
// the live API (api.php?action=list) at load time and auto-refreshed every 30s
// via polling (MVP). The subscription is isolated behind subscribe(cb) so it can
// be swapped to SSE/WebSocket without touching the render code.
// Legacy proof-of-work content is preserved below in the archive section.
session_start();
if (!isset($_SESSION['user'])) {
    header('Location: auth.html');
    exit;
}
$me = $_SESSION['user'];

function esc($s){ return htmlspecialchars((string)$s, ENT_QUOTES, 'UTF-8'); }
$who = esc($me['username'] ?? ($me['member'] ?? 'team'));
?>
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Z-Dot Team — Live Progress</title>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif; background:#0b1220; color:#dbe7ff; line-height:1.55; }
  .wrap { max-width:1100px; margin:0 auto; padding:28px 18px 60px; }
  header { text-align:center; padding:20px 0 6px; }
  header h1 { font-size:1.8rem; color:#fff; letter-spacing:1px; }
  header .tag { color:#7fd1ff; font-size:.85rem; letter-spacing:3px; margin-top:6px; }
  .nav { margin-top:14px; text-align:center; }
  .nav a { background:#1565c0; color:#fff; text-decoration:none; padding:8px 16px; border-radius:8px; font-size:.85rem; }
  .nav a:hover { background:#1a6fd8; }
  .livebar { display:flex; flex-wrap:wrap; gap:10px; justify-content:center; align-items:center; margin-top:16px; }
  .pill { border-radius:20px; padding:5px 14px; font-size:.78rem; border:1px solid; }
  .pill.poll { background:#12395a; color:#9fd8ff; border-color:#2f5a8a; }
  .pill.poll .dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:#37d67a; margin-right:6px; animation:pulse 2s infinite; }
  .pill.poll.err .dot { background:#ff5f56; animation:none; }
  .pill.counts { background:#0e2a1e; color:#7ee2a8; border-color:#1f5a3f; }
  .pill.counts b { color:#fff; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
  h3.section { margin-top:30px; color:#7fd1ff; letter-spacing:2px; font-size:.95rem; border-bottom:1px solid #1f3a5f; padding-bottom:8px; }
  h3.section .hint { color:#6f8db0; font-size:.7rem; letter-spacing:1px; font-weight:normal; }
  .grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:14px; margin-top:16px; }
  .card { background:#101d33; border:1px solid #1f3a5f; border-radius:14px; padding:14px 16px; display:flex; flex-direction:column; gap:8px; transition:border-color .3s; }
  .card.flash { animation:flashbg 1.6s ease-out; border-color:#7fd1ff; }
  @keyframes flashbg { 0% { background:#1d3a63; } 100% { background:#101d33; } }
  .card-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }
  .card h2 { font-size:.92rem; color:#fff; font-weight:600; }
  .card .desc { font-size:.85rem; color:#a9c2e5; }
  .badge { font-size:.68rem; font-weight:700; letter-spacing:1.2px; padding:3px 10px; border-radius:20px; white-space:nowrap; border:1px solid; }
  .st-pending   { background:#1c2433; color:#9fb3cc; border-color:#33405a; }
  .st-assigned  { background:#0e2a2e; color:#6fd8e8; border-color:#1f5a62; }
  .st-in_progress{ background:#12395a; color:#7fd1ff; border-color:#2f5a8a; }
  .st-review    { background:#2a1f3a; color:#c9a7ff; border-color:#5a3f8a; }
  .st-done      { background:#0e2a1e; color:#7ee2a8; border-color:#1f5a3f; }
  .st-failed    { background:#2a1212; color:#ffb3a0; border-color:#5a2f2f; }
  .st-cancelled { background:#171d27; color:#7d8aa3; border-color:#2e3747; }
  .st-other     { background:#241f14; color:#e8d9a7; border-color:#5a4a2f; }
  .meta { display:flex; flex-wrap:wrap; gap:5px 12px; font-size:.72rem; color:#6f8db0; border-top:1px dashed #1f3a5f; padding-top:8px; }
  .meta span b { color:#9fd8ff; font-weight:600; }
  .meta .ts { cursor:help; border-bottom:1px dotted #2f5a8a; }
  .prio { display:inline-block; padding:1px 7px; border-radius:8px; background:#241f14; border:1px solid #5a4a2f; color:#e8d9a7; font-size:.7rem; }
  .loading { color:#6f8db0; text-align:center; padding:40px 0; font-size:.9rem; }
  .errbox { color:#ffb3a0; text-align:center; padding:30px; font-size:.9rem; }
  details.archive { margin-top:34px; background:#0d1626; border:1px solid #1a2c47; border-radius:14px; padding:12px 16px; }
  details.archive summary { color:#7fd1ff; cursor:pointer; font-size:.85rem; letter-spacing:1px; user-select:none; }
  details.archive .inner { margin-top:10px; }
  /* legacy proof-of-work styles (kept for the archive section) */
  .card .card-head .ic { font-size:1.4rem; }
  .card h2 { margin:0; }
  .blurb { margin:4px 0 8px; color:#a9c2e5; font-size:.88rem; }
  .links { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }
  .lnk { background:#12395a; color:#7fd1ff; border:1px solid #2f5a8a; border-radius:8px; padding:5px 10px; font-size:.76rem; text-decoration:none; }
  .lnk:hover { background:#1a4a70; }
  .meta { font-size:.76rem; }
  .live { display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
  .live a { background:#0e2a1e; color:#7ee2a8; border:1px solid #1f5a3f; border-radius:8px; padding:7px 12px; font-size:.85rem; text-decoration:none; }
  table { width:100%; border-collapse:collapse; margin-top:14px; font-size:.78rem; }
  td { padding:5px 8px; border-bottom:1px solid #14263f; color:#a9c2e5; }
  td.hash { color:#7fd1ff; font-family:monospace; white-space:nowrap; }
  .personas { display:flex; flex-wrap:wrap; gap:8px; margin-top:14px; }
  .persona { background:#101d33; border:1px solid #1f3a5f; border-radius:8px; padding:5px 10px; font-size:.8rem; }
  .blockers li { margin:6px 0 6px 18px; color:#ffb3a0; }
  footer { margin-top:34px; text-align:center; color:#4a6385; font-size:.75rem; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Z-DOT TEAM · LIVE PROGRESS</h1>
    <div class="tag">REAL-TIME TASK DASHBOARD · PRIVATE · TEAM ONLY</div>
    <div class="nav"><a href="index.html">← Back to Task Dashboard</a></div>
    <div class="livebar">
      <span class="pill poll" id="poll-indicator"><span class="dot"></span><span id="poll-text">connecting…</span></span>
      <span class="pill counts" id="counts"></span>
      <span class="pill counts" style="background:#12395a;border-color:#2f5a8a;color:#9fd8ff;">🔒 <?php echo $who; ?></span>
    </div>
  </header>

  <h3 class="section">📋 LIVE TASK PROGRESS <span class="hint">— auto-refreshes every 30s · no page reload</span></h3>
  <div id="task-grid" class="grid"><div class="loading">Loading live task data from API…</div></div>
  <div id="grid-error" class="errbox" style="display:none"></div>

  <details class="archive">
    <summary>🗂 Proof-of-work archive (static snapshot — LIVE SYSTEMS / PROJECTS / PERSONAS / COMMITS / BLOCKERS)</summary>
    <div class="inner">
