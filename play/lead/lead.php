<?php
/**
 * Z-Dot lead capture -> own list (JSONL) + HubSpot CRM.
 * Token stays server-side; never reaches the browser.
 *
 * POST JSON: { email, name?, source?, page? }
 * Returns:   { ok: true, stored: bool, crm: "created"|"exists"|"error" }
 *
 * Idempotent: a repeat email updates rather than duplicating.
 * No email is ever logged to the response (privacy + no leaking).
 */
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

const DATA_DIR   = __DIR__ . '/data';
const LEADS_FILE = DATA_DIR . '/leads.jsonl';

function fail(int $code, string $msg): void {
    http_response_code($code);
    echo json_encode(['ok' => false, 'error' => $msg]);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') fail(405, 'POST only');

$raw = file_get_contents('php://input');
$in  = json_decode($raw, true);
if (!is_array($in)) { parse_str($raw, $in); }              // tolerate form posts

$email = strtolower(trim($in['email'] ?? ''));
if ($email === '' || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    fail(400, 'A valid email address is required.');
}
if (strlen($email) > 254) fail(400, 'Email too long.');

// honeypot — bots fill hidden fields, humans do not
if (!empty($in['website'])) { echo json_encode(['ok' => true, 'stored' => false, 'crm' => 'skipped']); exit; }

$name   = trim(substr($in['name']   ?? '', 0, 120));
$source = trim(substr($in['source'] ?? 'play', 0, 60));
$page   = trim(substr($in['page']   ?? '', 0, 200));

if (!is_dir(DATA_DIR)) { @mkdir(DATA_DIR, 0755, true); }

// ---- 1) own the list first: append locally, so CRM trouble never loses a lead
$stored = false;
$row = json_encode([
    'ts'     => gmdate('c'),
    'email'  => $email,
    'name'   => $name,
    'source' => $source,
    'page'   => $page,
    'ip'     => $_SERVER['REMOTE_ADDR'] ?? '',
    'ua'     => substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 200),
], JSON_UNESCAPED_SLASHES);
if ($row !== false && file_exists(LEADS_FILE)) {
    // only append if this email is not already recorded
    $seen = false;
    foreach (file(LEADS_FILE, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $j = json_decode($line, true);
        if (is_array($j) && ($j['email'] ?? '') === $email) { $seen = true; break; }
    }
    if (!$seen) { $stored = (bool)@file_put_contents(LEADS_FILE, $row . "\n", FILE_APPEND | LOCK_EX); }
} else {
    $stored = (bool)@file_put_contents(LEADS_FILE, $row . "\n", FILE_APPEND | LOCK_EX);
}

// ---- 2) push to HubSpot (best effort; a failure here does not fail the request)
$crm = 'skipped';
$token = getenv('HUBSPOT_ACCESS_TOKEN') ?: '';
if ($token === '' && file_exists(__DIR__ . '/hubspot_token.php')) {
    $token = trim((string)@include __DIR__ . '/hubspot_token.php');
}
if ($token !== '') {
    $parts = $name !== '' ? preg_split('/\s+/', $name) : [];
    $props = [
        'email'     => $email,
        'firstname' => $parts[0] ?? 'Play',
        'lastname'  => isset($parts[1]) ? implode(' ', array_slice($parts, 1)) : '',
        'hs_lead_status' => 'NEW',
        'zdot_source'    => $source,
    ];
    // create; a 409 means it already exists -> treat as success
    $ch = curl_init('https://api.hubapi.com/crm/v3/objects/contacts');
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => json_encode(['properties' => $props]),
        CURLOPT_HTTPHEADER => ['Content-Type: application/json',
                               'Authorization: Bearer ' . $token],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 15,
    ]);
    $resp = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    if ($code >= 200 && $code < 300)      { $crm = 'created'; }
    elseif ($code === 409)                { $crm = 'exists';  }
    else                                  { $crm = 'error';   }
}

echo json_encode(['ok' => true, 'stored' => $stored, 'crm' => $crm]);
