<?php
// Z-Dot Team Checklist - Authentication backend (PHP, shared hosting)
// Session-based. First login uses the SHARED TEAM CODE; user then creates
// their own account bound to a real team member.
session_start();

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

$USERS_FILE = __DIR__ . '/users.json';
// Shared team code for first login (set to the same value as FTP password)
$TEAM_CODE = 'zDotcode#5';
$TEAM_MEMBERS = ['Zerric','BossLady','Manny','ClickClack','NinjaNerd','Seleena','Mark','Meta'];

function load_users($file) {
    if (!file_exists($file)) return ['users' => [], 'team_code_used' => false];
    $raw = @file_get_contents($file);
    $d = json_decode($raw, true);
    return is_array($d) ? $d : ['users' => [], 'team_code_used' => false];
}
function save_users($file, $data) {
    @file_put_contents($file, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES), LOCK_EX);
}
function hash_pw($pw) { return password_hash($pw, PASSWORD_DEFAULT); }

function log_event($msg) {
    $log = __DIR__ . '/access.log';
    $line = gmdate('Y-m-d\TH:i:s\Z') . ' ' . $msg . "\n";
    @file_put_contents($log, $line, FILE_APPEND | LOCK_EX);
}

function fail($msg, $code = 400) { http_response_code($code); echo json_encode(['error' => $msg]); exit; }

$action = $_GET['action'] ?? '';
$input = json_decode(file_get_contents('php://input'), true) ?: [];

if ($action === 'me') {
    if (!isset($_SESSION['user'])) { http_response_code(401); echo json_encode(['error' => 'not logged in']); exit; }
    echo json_encode(['user' => $_SESSION['user']]); exit;
}

if ($action === 'logout') {
    $_SESSION = [];
    session_destroy();
    echo json_encode(['ok' => true]); exit;
}

// First-login: validate shared team code, return list of team members to pick from
if ($action === 'validate_team_code') {
    $code = $input['code'] ?? '';
    if (!hash_equals($TEAM_CODE, $code)) fail('Invalid team code', 401);
    // Return members who don't already have an account
    $data = load_users($USERS_FILE);
    $taken = array_column($data['users'], 'member');
    $available = array_values(array_diff($TEAM_MEMBERS, $taken));
    echo json_encode(['available' => $available]); exit;
}

// Create account: requires valid team code + member + username + password
if ($action === 'register') {
    $code = $input['code'] ?? '';
    if (!hash_equals($TEAM_CODE, $code)) fail('Invalid team code', 401);
    $member = $input['member'] ?? '';
    $username = trim($input['username'] ?? '');
    $password = $input['password'] ?? '';
    if (!in_array($member, $TEAM_MEMBERS)) fail('Unknown team member');
    if ($username === '') fail('Username is required');
    if (strlen($password) < 6) fail('Password must be at least 6 characters');
    $data = load_users($USERS_FILE);
    foreach ($data['users'] as $u) {
        if ($u['member'] === $member) fail('That team member already has an account');
        if (strtolower($u['username']) === strtolower($username)) fail('That username is taken');
    }
    $data['users'][] = [
        'username' => $username,
        'member' => $member,
        'pw_hash' => hash_pw($password),
        'created_at' => gmdate('Y-m-d\TH:i:s\Z'),
    ];
    save_users($USERS_FILE, $data);
    $_SESSION['user'] = ['username' => $username, 'member' => $member];
    log_event('REGISTER username=' . $username . ' member=' . $member . ' ip=' . ($_SERVER['REMOTE_ADDR'] ?? '?'));
    echo json_encode(['user' => $_SESSION['user']]); exit;
}

// Login with personal account
if ($action === 'login') {
    $username = trim($input['username'] ?? '');
    $password = $input['password'] ?? '';
    $data = load_users($USERS_FILE);
    foreach ($data['users'] as $u) {
        if (strtolower($u['username']) === strtolower($username) && password_verify($password, $u['pw_hash'])) {
            $_SESSION['user'] = ['username' => $u['username'], 'member' => $u['member']];
            log_event('LOGIN username=' . $u['username'] . ' member=' . $u['member'] . ' ip=' . ($_SERVER['REMOTE_ADDR'] ?? '?'));
            echo json_encode(['user' => $_SESSION['user']]); exit;
        }
    }
    fail('Invalid username or password', 401);
}

// Change own password (requires valid session + current password)
if ($action === 'change_password') {
    if (!isset($_SESSION['user'])) fail('not logged in', 401);
    $username = $_SESSION['user']['username'];
    $current = $input['current_password'] ?? '';
    $new = $input['new_password'] ?? '';
    if (strlen($new) < 6) fail('New password must be at least 6 characters');
    $data = load_users($USERS_FILE);
    foreach ($data['users'] as &$u) {
        if (strtolower($u['username']) === strtolower($username)) {
            if (!password_verify($current, $u['pw_hash'])) fail('Current password is incorrect', 401);
            $u['pw_hash'] = hash_pw($new);
            $u['updated_at'] = gmdate('Y-m-d\TH:i:s\Z');
            save_users($USERS_FILE, $data);
            log_event('PASSWORD_CHANGE username=' . $username . ' ip=' . ($_SERVER['REMOTE_ADDR'] ?? '?'));
            echo json_encode(['ok' => true, 'message' => 'Password changed']); exit;
        }
    }
    fail('User not found', 404);
}

fail('unknown action: ' . $action, 404);
