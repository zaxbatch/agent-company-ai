<?php
// Z-Dot Approval Gallery API
// items.json   = the review manifest (seeded by our builder, refreshable live)
// decisions.json = server-side decisions, shared by everyone
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

$DATA = __DIR__ . '/data';
if (!is_dir($DATA)) { @mkdir($DATA, 0775, true); }
$ITEMS = $DATA . '/items.json';
$DEC   = $DATA . '/decisions.json';

function read_json($p, $d) {
    if (!file_exists($p)) return $d;
    $r = json_decode(file_get_contents($p), true);
    return is_array($r) ? $r : $d;
}
function write_json($p, $v) {
    return file_put_contents($p,
        json_encode($v, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE),
        LOCK_EX) !== false;
}
function fetch($url) {
    $ctx = stream_context_create(['http' => ['timeout' => 12,
        'header' => "User-Agent: zdot-gallery\r\n"]]);
    $r = @file_get_contents($url, false, $ctx);
    return $r === false ? null : json_decode($r, true);
}

$action = isset($_GET['action']) ? $_GET['action'] : 'items';

if ($action === 'items') {
    echo json_encode(read_json($ITEMS, []));
    exit;
}

if ($action === 'decisions') {
    $d = read_json($DEC, []);
    echo $d ? json_encode($d, JSON_FORCE_OBJECT) : '{}';
    exit;
}

if ($action === 'decide') {
    $raw = file_get_contents('php://input');
    $in = json_decode($raw, true);
    if (!is_array($in) || empty($in['id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'need {id, decision, note, by}']);
        exit;
    }
    $id = preg_replace('/[^A-Za-z0-9._-]/', '', $in['id']);
    $dec = isset($in['decision']) ? $in['decision'] : null;
    $valid = ['approve', 'revise', 'reject', null, ''];
    if (!in_array($dec, $valid, true)) {
        http_response_code(400);
        echo json_encode(['error' => 'bad decision']);
        exit;
    }
    $store = read_json($DEC, []);
    if (!$dec) {
        unset($store[$id]);                       // clearing a decision
    } else {
        $store[$id] = [
            'decision' => $dec,
            'note'     => isset($in['note']) ? mb_substr(trim($in['note']), 0, 2000) : '',
            'by'       => isset($in['by'])   ? mb_substr(trim($in['by']), 0, 80)    : 'anon',
            'at'       => gmdate('c'),
        ];
    }
    if (!write_json($DEC, $store)) {
        http_response_code(500);
        echo json_encode(['error' => 'could not write decisions (data dir not writable?)']);
        exit;
    }
    echo json_encode(['ok' => true, 'count' => count($store)]);
    exit;
}

if ($action === 'refresh') {
    // server-side fetch: no CORS limits here, so the gallery can track the live site
    $items = read_json($ITEMS, []);
    $have  = [];
    $srcs  = [];
    foreach ($items as $it) {
        $have[$it['id']] = true;
        if (!empty($it['source'])) { $srcs[$it['source']] = true; }
    }
    $added = 0;

    $songs = fetch('https://snowsnakes.zerric.xyz/api/songs');
    if (is_array($songs)) {
        foreach ($songs as $s) {
            $id = 'ss-live-song-' . $s['id'];
            if (isset($have[$id]) || isset($srcs['ss:song:' . $s['id']])) continue;
            $items[] = [
                'id' => $id, 'category' => 'Published on SnowSnakes', 'kind' => 'audio',
                'title' => isset($s['title']) ? $s['title'] : 'song ' . $s['id'],
                'url' => $s['audio_url'],
                'meta' => 'song id ' . $s['id'] . ' · ' . (isset($s['author_name']) ? $s['author_name'] : '?')
                          . ' · ' . substr(isset($s['created_at']) ? $s['created_at'] : '', 0, 10),
                'proof' => 'Pulled live from the SnowSnakes API by the gallery refresh.',
            ];
            $have[$id] = true; $added++;
        }
    }
    $doodles = fetch('https://snowsnakes.zerric.xyz/api/doodles');
    if (is_array($doodles)) {
        foreach ($doodles as $d) {
            $id = 'ss-live-doodle-' . $d['id'];
            if (isset($have[$id]) || isset($srcs['ss:doodle:' . $d['id']])) continue;
            $items[] = [
                'id' => $id, 'category' => 'Art (doodles)', 'kind' => 'image',
                'title' => isset($d['title']) ? $d['title'] : 'doodle ' . $d['id'],
                'url' => $d['image_url'],
                'meta' => 'doodle id ' . $d['id'] . ' · '
                          . (isset($d['author_name']) ? $d['author_name'] : '?'),
                'proof' => 'Pulled live from the SnowSnakes API by the gallery refresh.',
            ];
            $have[$id] = true; $added++;
        }
    }
    write_json($ITEMS, $items);
    echo json_encode(['ok' => true, 'added' => $added, 'total' => count($items)]);
    exit;
}

http_response_code(404);
echo json_encode(['error' => 'unknown action']);
