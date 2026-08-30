<?php
/**
 * Z-Dot Doodle Gallery — API
 * Auth-gated (reuses the session established by auth.php).
 * Storage:    doodle-data.json   (same dir, JSON with LOCK_EX)
 * Media:      doodle_media/*.svg (auto-scanned, nothing to register)
 * Actions:    list | set_status | comment | delete_comment | reset | export
 * Security:   session auth + session-bound CSRF token on every mutation.
 * Owner:      NinjaNerd (CTO) · built 2026-08-30
 */
session_start();
header('Content-Type: application/json; charset=utf-8');
header('X-Content-Type-Options: nosniff');

if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => 'not logged in']);
    exit;
}
$me = $_SESSION['user'];
$member = trim((string)($me['member'] ?? $me['username'] ?? 'team'));
$is_zerric = ($member === 'Zerric');

$DATA_FILE = __DIR__ . '/doodle-data.json';
$MEDIA_DIR = __DIR__ . '/doodle_media';
$STATUSES  = ['pending', 'approved', 'needs_changes', 'rejected'];
$MAX_COMMENT_LEN = 2000;

// ── helpers ──────────────────────────────────────────────────────────────
function fail($msg, $code = 400) {
    http_response_code($code);
    echo json_encode(['error' => $msg]);
    exit;
}
function respond($data, $code = 200) {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_SLASHES);
    exit;
}
function now_iso() {
    return gmdate('Y-m-d\TH:i:s\Z');
}
function load_data() {
    global $DATA_FILE;
    if (!file_exists($DATA_FILE)) return ['doodles' => [], 'updated' => null];
    $raw = @file_get_contents($DATA_FILE);
    $d = json_decode($raw, true);
    return is_array($d) ? $d : ['doodles' => [], 'updated' => null];
}
function save_data($data) {
    global $DATA_FILE;
    $data['updated'] = now_iso();
    @file_put_contents($DATA_FILE, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
}
function scan_doodles() {
    global $MEDIA_DIR;
    $out = [];
    foreach (glob($MEDIA_DIR . '/*.svg') as $p) {
        $out[] = basename($p);
    }
    sort($out, SORT_STRING);
    return $out;
}
/** Derive a readable title from the filename. */
function title_from_file($f) {
    $base = preg_replace('/\.svg$/i', '', $f);
    $parts = preg_split('/[-_]+/', $base);
    if (($parts[0] ?? '') === 'doodle') array_shift($parts);
    $date = ''; $seq = '';
    foreach ($parts as $i => $p) {
        if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $p)) { $date = $p; unset($parts[$i]); }
    }
    $nums = array_values(array_filter($parts, fn($p) => preg_match('/^\d{1,3}$/', $p)));
    foreach ($nums as $n) {
        $k = array_search($n, $parts, true);
        if ($k !== false) unset($parts[$k]);
    }
    $seq = $nums ? ' #' . $nums[0] : '';
    $words = array_map(fn($w) => ucfirst(strtolower($w)), $parts);
    $title = implode(' ', $words);
    if ($title === '') $title = 'Untitled doodle';
    if ($date) $title .= ' · ' . $date;
    return $title . $seq;
}
function valid_doodle($id, $files) {
    return is_string($id) && preg_match('/^[\w\-\.]+\.svg$/i', $id) && in_array($id, $files, true);
}
function sanitize_text($t) {
    $t = (string)$t;
    $t = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F]/u', '', $t);   // control chars
    $t = trim($t);
    $t = mb_substr($t, 0, $GLOBALS['MAX_COMMENT_LEN']);
    return $t;
}

// CSRF token lives in the session; issued with every list response.
if (empty($_SESSION['csrf'])) {
    $_SESSION['csrf'] = bin2hex(random_bytes(16));
}

$action = $_GET['action'] ?? '';
$input  = json_decode(file_get_contents('php://input'), true) ?: [];

$mutating = in_array($action, ['set_status', 'comment', 'delete_comment', 'reset'], true);
if ($mutating) {
    $token = $_SERVER['HTTP_X_CSRF_TOKEN'] ?? '';
    if ($token === '' || !hash_equals($_SESSION['csrf'], $token)) {
        fail('Invalid CSRF token', 403);
    }
}

// ── actions ──────────────────────────────────────────────────────────────
if ($action === 'list') {
    $files  = scan_doodles();
    $data   = load_data();
    $items  = [];
    foreach ($files as $f) {
        $rec = $data['doodles'][$f] ?? ['status' => 'pending', 'comments' => [], 'history' => []];
        $items[] = [
            'file'     => $f,
            'title'    => title_from_file($f),
            'status'   => in_array($rec['status'] ?? '', $STATUSES, true) ? $rec['status'] : 'pending',
            'comments' => array_values($rec['comments'] ?? []),
            'history'  => array_slice(array_values($rec['history'] ?? []), -8),
        ];
    }
    respond([
        'csrf'      => $_SESSION['csrf'],
        'member'    => $member,
        'is_zerric' => $is_zerric,
        'doodles'   => $items,
        'updated'   => $data['updated'] ?? null,
        'server_time' => now_iso(),
    ]);
}

if ($action === 'set_status') {
    $id     = basename((string)($input['id'] ?? ''));
    $status = (string)($input['status'] ?? '');
    $files  = scan_doodles();
    if (!valid_doodle($id, $files)) fail('Unknown doodle', 404);
    if (!in_array($status, $STATUSES, true)) fail('Invalid status', 422);
    $data = load_data();
    $rec = &$data['doodles'][$id];
    if (!is_array($rec)) $rec = ['status' => 'pending', 'comments' => [], 'history' => []];
    $rec['status'] = $status;
    $rec['history'][] = ['who' => $member, 'action' => 'status→' . $status, 'ts' => now_iso()];
    save_data($data);
    respond(['ok' => true, 'id' => $id, 'status' => $status]);
}

if ($action === 'comment') {
    $id   = basename((string)($input['id'] ?? ''));
    $text = sanitize_text($input['text'] ?? '');
    $files = scan_doodles();
    if (!valid_doodle($id, $files)) fail('Unknown doodle', 404);
    if ($text === '') fail('Comment cannot be empty');
    $data = load_data();
    $rec = &$data['doodles'][$id];
    if (!is_array($rec)) $rec = ['status' => 'pending', 'comments' => [], 'history' => []];
    $comment = ['author' => $member, 'text' => $text, 'ts' => now_iso()];
    $rec['comments'][] = $comment;
    $rec['history'][] = ['who' => $member, 'action' => 'commented', 'ts' => now_iso()];
    save_data($data);
    respond(['ok' => true, 'id' => $id, 'comment' => $comment]);
}

if ($action === 'delete_comment') {
    $id  = basename((string)($input['id'] ?? ''));
    $idx = (int)($input['idx'] ?? -1);
    $files = scan_doodles();
    if (!valid_doodle($id, $files)) fail('Unknown doodle', 404);
    $data = load_data();
    $rec = &$data['doodles'][$id];
    if (!is_array($rec) || !isset($rec['comments'][$idx])) fail('Comment not found', 404);
    $c = $rec['comments'][$idx];
    // author can delete their own; Zerric can delete anything
    if (!($c['author'] === $member || $is_zerric)) fail('Not allowed', 403);
    array_splice($rec['comments'], $idx, 1);
    $rec['history'][] = ['who' => $member, 'action' => 'deleted comment', 'ts' => now_iso()];
    save_data($data);
    respond(['ok' => true, 'id' => $id]);
}

if ($action === 'reset') {
    $id = basename((string)($input['id'] ?? ''));
    $files = scan_doodles();
    if (!valid_doodle($id, $files)) fail('Unknown doodle', 404);
    $data = load_data();
    if (isset($data['doodles'][$id])) {
        unset($data['doodles'][$id]);   // back to pristine pending + no comments
    }
    save_data($data);
    respond(['ok' => true, 'id' => $id, 'status' => 'pending']);
}

if ($action === 'export') {
    $files = scan_doodles();
    $data  = load_data();
    $lines = [];
    $lines[] = '# Z-Dot Doodle Review Notes';
    $lines[] = '# Generated ' . now_iso() . ' UTC';
    $lines[] = '# Status legend: pending / approved / needs_changes / rejected';
    $lines[] = '';
    foreach ($files as $f) {
        $rec = $data['doodles'][$f] ?? ['status' => 'pending', 'comments' => [], 'history' => []];
        $status = in_array($rec['status'] ?? '', $STATUSES, true) ? $rec['status'] : 'pending';
        $lines[] = '## ' . title_from_file($f) . '  [' . $status . ']';
        $lines[] = 'File: ' . $f;
        $comments = $rec['comments'] ?? [];
        if (!$comments) {
            $lines[] = 'No notes.';
        } else {
            foreach ($comments as $c) {
                $t = str_replace(["\r\n", "\r", "\n"], ' ', $c['text']);
                $lines[] = '- (' . $c['author'] . ' @ ' . substr($c['ts'], 0, 16) . ') ' . $t;
            }
        }
        $lines[] = '';
    }
    header('Content-Type: text/plain; charset=utf-8');
    header('Content-Disposition: attachment; filename="doodle-review-notes.md"');
    header('X-Content-Type-Options: nosniff');
    echo implode("\n", $lines);
    exit;
}

fail('unknown action: ' . $action, 404);
