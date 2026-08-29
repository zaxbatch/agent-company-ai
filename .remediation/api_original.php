<?php
// Z-Dot Team Checklist API - PHP backend (requires login via auth.php session)
// Usage: api.php?action=list|create|update|delete
session_start();
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PATCH, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

// Auth required for all task mutations; list is public-ish but require login too for consistency
if (!isset($_SESSION['user'])) {
    http_response_code(401);
    echo json_encode(['error' => 'not logged in']); exit;
}
$me = $_SESSION['user'];

$DATA_FILE = __DIR__ . '/tasks.json';
$VALID = ['pending','assigned','in_progress','review','done','failed','cancelled'];

function load_tasks($file) {
    if (!file_exists($file)) return [];
    $raw = @file_get_contents($file);
    $d = json_decode($raw, true);
    return is_array($d) ? $d : [];
}
function save_tasks($file, $tasks) {
    @file_put_contents($file, json_encode($tasks, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
}
function now_iso() { return gmdate('Y-m-d\TH:i:s\Z'); }
function fail($msg, $code = 400) { http_response_code($code); echo json_encode(['error' => $msg]); exit; }

$tasks = load_tasks($DATA_FILE);
$action = $_GET['action'] ?? 'list';
$input = json_decode(file_get_contents('php://input'), true) ?: [];

if ($action === 'list') { echo json_encode($tasks); exit; }

if ($action === 'create') {
    $desc = trim($input['description'] ?? '');
    if ($desc === '') fail('description is required');
    $t = [
        'id' => substr(bin2hex(random_bytes(6)), 0, 12),
        'description' => $desc,
        'assignee' => $input['assignee'] ?? null,
        'priority' => isset($input['priority']) ? (int)$input['priority'] : 0,
        'status' => !empty($input['assignee']) ? 'assigned' : 'pending',
        'result' => null,
        'blocker' => $input['blocker'] ?? null,
        'created_at' => now_iso(),
        'updated_at' => now_iso(),
        'last_checked_at' => null,
        'created_by' => $me['member'],
    ];
    $tasks[] = $t;
    save_tasks($DATA_FILE, $tasks);
    http_response_code(201);
    echo json_encode($t); exit;
}

if ($action === 'update' || $action === 'delete') {
    $id = $input['id'] ?? $_GET['id'] ?? null;
    if (!$id) fail('id is required');
    $idx = null;
    foreach ($tasks as $i => $t) { if ($t['id'] === $id) { $idx = $i; break; } }
    if ($idx === null) fail('no task with id ' . $id, 404);

    if ($action === 'delete') {
        array_splice($tasks, $idx, 1);
        save_tasks($DATA_FILE, $tasks);
        http_response_code(204); exit;
    }
    $t = $tasks[$idx];
    if (isset($input['status'])) {
        if (!in_array($input['status'], $VALID)) fail('invalid status: ' . $input['status']);
        $t['status'] = $input['status'];
    }
    if (isset($input['assignee'])) $t['assignee'] = $input['assignee'];
    if (isset($input['description'])) {
        $d = trim($input['description']);
        if ($d === '') fail('description cannot be empty');
        $t['description'] = $d;
    }
    if (isset($input['result'])) $t['result'] = $input['result'];
    if (isset($input['blocker'])) $t['blocker'] = $input['blocker'];
    if (isset($input['last_checked_at'])) $t['last_checked_at'] = $input['last_checked_at'];
    $t['updated_at'] = now_iso();
    $t['updated_by'] = $me['member'];
    $tasks[$idx] = $t;
    save_tasks($DATA_FILE, $tasks);
    echo json_encode($t); exit;
}

fail('unknown action: ' . $action, 404);
