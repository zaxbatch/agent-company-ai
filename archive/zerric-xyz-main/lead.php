<?php
// ZDOT lead capture -> HubSpot CRM (server-side, token never exposed to browser)
header('Content-Type: application/json');

// HubSpot token stored server-side (NOT in git, NOT in frontend JS)
$HUBSPOT_TOKEN = getenv('HUBSPOT_ACCESS_TOKEN');
if (!$HUBSPOT_TOKEN && file_exists(__DIR__ . '/hubspot_token.php')) {
    $HUBSPOT_TOKEN = include __DIR__ . '/hubspot_token.php';
}
if (!$HUBSPOT_TOKEN) {
    http_response_code(500);
    echo json_encode(['ok' => false, 'error' => 'CRM not configured']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'POST only']);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$name = trim($input['name'] ?? '');
$email = trim($input['email'] ?? '');
$source = trim($input['source'] ?? 'website');

if (!$email || !filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['ok' => false, 'error' => 'Valid email required']);
    exit;
}

$first = '';
$last = '';
if ($name) {
    $parts = preg_split('/\s+/', $name);
    $first = $parts[0];
    $last = count($parts) > 1 ? implode(' ', array_slice($parts, 1)) : '';
}

$payload = json_encode([
    'properties' => [
        'email' => $email,
        'firstname' => $first ?: 'Lead',
        'lastname' => $last,
        'hs_lead_status' => 'NEW',
        'zdot_source' => $source,
    ],
]);

$ch = curl_init('https://api.hubapi.com/crm/v3/objects/contacts');
curl_setopt_array($ch, [
    CURLOPT_POST => true,
    CURLOPT_POSTFIELDS => $payload,
    CURLOPT_HTTPHEADER => [
        'Content-Type: application/json',
        'Authorization: Bearer ' . $HUBSPOT_TOKEN,
    ],
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 15,
]);
$resp = curl_exec($ch);
$code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($code >= 200 && $code < 300) {
    http_response_code(200);
    echo json_encode(['ok' => true]);
} else {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => 'CRM write failed']);
}
