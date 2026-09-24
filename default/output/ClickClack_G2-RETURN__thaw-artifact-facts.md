G2 RETURN — RAW VALUES ONLY.
Instrument: shell + curl. No browser, no touchscreen, no phone exist in this workspace.
Fetched: 2026-09-24T02:47:10Z.
Written twice, identical bytes: default/output/ClickClack_G2-RETURN__thaw-artifact-facts.md (repo root) | default/output/ClickClack_G2-RETURN__thaw-artifact-facts.md (agent-visible workspace root .agent-company-ai/). No email sent. No other location written.

1. THAW GAME FILE PATH ON DISK
NOTHING TO VERIFY YET

2. THAW GAME FILE BYTE SIZE
NOTHING TO VERIFY YET

3. EXTERNAL NETWORK REFERENCES IN THE THAW FILE
NOTHING TO VERIFY YET

4. THAW GAME ID
NOTHING TO VERIFY YET

5. THAW LAUNCH URL
NOTHING TO VERIFY YET

6. THAW CORE VERB — WHAT THE THUMB DOES
NOTHING TO VERIFY YET

7. ITEMS THAT DO NOT EXIST
1, 2, 3, 4, 5, 6 = NOTHING TO VERIFY YET. Nothing built to fill the gap this turn.

=====================================================================
RAW EVIDENCE
=====================================================================

--- 1. FILE EXISTENCE (literal shell output) ---
$ ls -la content/snowsnakes/games/thaw.html
ls: cannot access 'content/snowsnakes/games/thaw.html': No such file or directory
$ ls -la content/snowsnakes/games.json
ls: cannot access 'content/snowsnakes/games.json': No such file or directory
$ [ -e content/snowsnakes/games/thaw.html ] -> ABSENT
$ [ -e content/snowsnakes/games.json ] -> ABSENT
$ [ -e content/games/thaw.html ] -> ABSENT
$ [ -e .agent-company-ai/content/snowsnakes/games/thaw.html ] -> ABSENT
$ find . -name '*thaw*.html' -not -path './.git/*' | wc -l
0

$ find . -iname '*thaw*' (excluding .git/, venv/) -> 2 files, both MilkUps Album 2 audio, neither a game:
./content/milkups/album2/06-thaw.mp3
./content/milkups/album2/06-thaw.wav
bare bytes: 06-thaw.mp3 = 2602466 | 06-thaw.wav = 9557716

$ git ls-files | grep -i thaw
content/milkups/album2/06-thaw.mp3
content/milkups/album2/06-thaw.wav
(no .html, no game file, never tracked)

$ git log --all --oneline --diff-filter=A -- '*thaw*'
60ca540ff state: snapshot 2026-09-17T03:45:01Z [skip ci]
$ git show --stat 60ca540ff -- '*thaw*'
 content/milkups/album2/06-thaw.mp3 | Bin 0 -> 2602466 bytes
 content/milkups/album2/06-thaw.wav | Bin 0 -> 9557716 bytes
(that is the only 'thaw*' path ever added in all history — audio, not a game)

$ git check-ignore -v content/snowsnakes/games/thaw.html content/snowsnakes/games.json
(no output) -> NOT gitignored -> genuinely absent, not merely hidden

$ git ls-files content/snowsnakes/games
content/snowsnakes/games/_qa/frostbite-dash-http.png
content/snowsnakes/games/_qa/frostbite-dash-mobile.png
content/snowsnakes/games/_qa/live-122-mobile.png
content/snowsnakes/games/_qa/live-123-mobile.png
content/snowsnakes/games/_qa/snow-cone-catch-http.png
content/snowsnakes/games/_qa/snow-cone-catch-mobile.png
content/snowsnakes/games/_qa/snow-cone-catch-play.png
content/snowsnakes/games/dice-drop.html
content/snowsnakes/games/frostbite-dash.html
content/snowsnakes/games/snow-cone-catch.html
(no thaw)

--- 2. NEAREST EXISTING GAME FILES AND THEIR BYTE SIZES (bare numbers) ---
content/snowsnakes/games/dice-drop.html = 31002
content/snowsnakes/games/frostbite-dash.html = 10107
content/snowsnakes/games/snow-cone-catch.html = 10026
content/snowsnakes/itch/games/ = 19 .html files, none named thaw
content/games/ = fridge-standoff.html (6121), snitch-rat-run.html (6764)
resources/games/ = family-food-truck.html (7850), food-truck-frenzy.html (8331)
Every "games" directory on disk searched. THAW file byte size = NOTHING TO VERIFY YET.
Budget stated by QA = 500KB. Target stated in the frozen brief = < 60KB. Neither can be checked: no file.

--- 3. EXTERNAL NETWORK REFERENCE COUNT ---
THAW file does not exist -> count impossible -> NOTHING TO VERIFY YET.
Counts are given instead for the nearest EXISTING published game file, content/snowsnakes/games/dice-drop.html (id 124), same instrument:
  src= occurrences: 0
  href= occurrences: 1
  fetch( occurrences: 0
  XMLHttpRequest occurrences: 0
  url( occurrences: 0
  off-file absolute src/href targets (https?: or // in a src/href attribute): [] -> 0
  fetch("...") literal URLs: [] -> 0
  => 0 references pointing off-file. This is the 124 file, NOT a THAW file. It does not satisfy the THAW requirement.

--- 4. GAME ID — LIVE INDEX, CHECKED THIS TURN ---
$ curl https://snowsnakes.zerric.xyz/api/games
HTTP 200 | content-type: application/json; charset=utf-8 | bytes 13717 | entries 20
ids and titles served, raw: 124 DICE DROP | 123 SNOW CONE CATCH | 122 FROSTBITE DASH | 120 SnowSnake | 115 FRIDGE STANDOFF | 100 SNITCH RUN — Catch Cheese, Dodge the Cat | 99 SNOW BEATS 2 — loop download (fixed) | 97 SNOW BEATS — loop download | 96 FOOD TRUCK FRENZY | 94 Spread Da Word - Soundtracks (Cassette Player) | 91 Hood vs Fridge | 85 Beat Maker Pad | 83 SNOW SNAKE RUSH | 81 VIN NEGAR BOTTLE FLIP | 80 SNOWBALL BLITZ | 79 Iceberg Hopper | 78 Snowball Fight | 76 Snow Snake | 70 UFO Hunter | 23 T
max id = 124
entries containing 'thaw' in title+description = 0 (False)
THAW GAME ID = NOTHING TO VERIFY YET. No id is reserved for THAW.

$ curl https://snowsnakes.zerric.xyz/api/games/124
{"id":124,"title":"DICE DROP","description":"Dice Tetris. Stack falling dice and clear rows, then chase the bonuses: ...","icon":"🎲","tags":["puzzle","mobile","touch","dice","arcade","8-bit"],"author_id":85,"type":"user","votes":0,"plays":3,"file_count":0,"created_at":"2026-09-20T04:18:29.751Z",...,"author_name":"zdot_team"}
124 = DICE DROP. Pre-existing. Not THAW. Its published verb is stack.
$ curl https://snowsnakes.zerric.xyz/api/games/125
HTTP 404 | bytes 21 | {"error":"Not found"}
125 does not exist -> no next-id reservation for THAW.
$ curl https://snowsnakes.zerric.xyz/api/games/thaw
HTTP 500
$ curl https://snowsnakes.zerric.xyz/games/thaw
HTTP 200 | bytes 896 | content-type text/html; charset=UTF-8
  occurrences of 'thaw' in that body = 0
  diff /tmp/gt.html /tmp/g124.html -> IDENTICAL BYTES: /games/thaw == /games/124
  => that 200 is the SPA catch-all shell (896 bytes), not a game record. It is not evidence of a THAW artifact.

--- 5. LAUNCH URL ---
THAW LAUNCH URL = NOTHING TO VERIFY YET.
No /api/games/<id> record, no id, no file. The one candidate string, https://snowsnakes.zerric.xyz/games/thaw, returns the 896-byte catch-all shell identical to /games/124 and contains the word 'thaw' zero times. It is not a launch URL for a game.

--- 6. CORE VERB + RESKIN RULING ---
THAW CORE VERB = NOTHING TO VERIFY YET (no file exists to read).
RAW QUOTE, source .agent-company-ai/default/output/task-a2edeab323a4/bosslady.md lines 12-13:
  "- **THAW** — *"Tap a tile to rotate it 90° — route one continuous stream from the summit spring to
    the valley gate before your taps run out."* Core verb: **route**."
RAW QUOTE, source .agent-company-ai/default/output/task-a2edeab323a4/TEAM-STATE.md §0.2 lines 35-38:
  "- **Core verb: `route`.** Single input, tap-to-rotate. Distinct from DICE DROP (`stack`/clear,
    game id 124) and SUMMIT SNAKES (`climb`/aim, ids 71/72). No game in our catalog rotates tiles.
    **New mechanic, not new art.**"
RULE APPLIED, PLAINLY: the verb written down for THAW is `route` (tap-to-rotate), which is neither `stack` nor `climb`. On paper that is NOT a reskin of DICE DROP (124) or SUMMIT SNAKES (71/72). But there is no file, so no code exists to confirm the verb, and the reskin gate can be neither passed nor failed this turn. NOTHING TO VERIFY YET.

IDS 71/72 REFERENCED AS SUMMIT SNAKES DO NOT RESOLVE LIVE THIS TURN:
$ curl .../api/games/71 -> HTTP 404 | {"error":"Not found"}
$ curl .../api/games/72 -> HTTP 404 | {"error":"Not found"}
$ curl .../api/games/70 -> HTTP 200 | UFO Hunter
$ curl .../api/games/76 -> HTTP 200 | Snow Snake
live catalog holds 70 and 76, not 71/72. Raw fact, flagged, not resolved.

--- PLACEHOLDER SCAN (required by hard rules) ---
THAW file does not exist -> it contains no placeholder asset, no fake play button, no "coming soon" text. There is nothing to scan.
Live index scanned as the substitute: 20 entries, word-boundary regex \b(coming soon|placeholder|lorem|todo|fake|wip|tbd)\b -> 0 hits.
Earlier substring hit 'wip' at id 122 FROSTBITE DASH was a false positive: the word is "swipe" in its description. Word-boundary count = 0.
THAW spec name in the program spec: $ grep -ci 'thaw' .agent-company-ai/content/snowsnakes/DAILY-GAME--program-spec.md = 0. THAW is not named in the daily-game program spec at all.

--- LPT / REAL-ESTATE CHECK (hard rule) ---
Word-boundary scan \b(real estate|mls|brokerage|realtor|listing agent)\b across content/snowsnakes/games, content/snowsnakes/itch/games, content/games = 0 files.
Substring 'mls' hits in content/snowsnakes/itch/games/spread-da-word-soundtracks-cassette-play.html are base64 audio payload (sample context "AvG6ZdMlsZIpJKT"); word-boundary count = 0. False positive.
No LPT/real-estate content in any game file. Z-Dot and LPT not mixed.

--- INSTRUMENT LIMIT, STATED SO IT IS NOT MISREAD ---
No browser, no phone, no touchscreen in this workspace. Nothing here is a play test. Every value above is a filesystem read or an HTTP response code and byte count. A real device remains the only instrument for G4, and it has not been used because there is no artifact to point it at.
