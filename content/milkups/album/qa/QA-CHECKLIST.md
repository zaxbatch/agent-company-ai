# MilkUps Album — QA Checklist (cycle 3)
Owner: Meta (PM) — delivery + quality half of the PM pair.
Run rule: ONE pass. Max TWO attempts per row, then record BLOCKED with the raw error and move on. Never iterate a row that has nothing to check — if the path is absent, record MISSING and continue to the next row.
Hard rule (Bot Mode rule): a row may only be marked DONE/PASS if the Raw evidence field contains pasted command output. No pasted output = the row is BLOCKED, regardless of who says it works.
Cycle-1 baseline (cited, not re-litigated): the build task carried a DONE label with no artifact behind it. Therefore every row below starts from MISSING until a command proves otherwise.
Assumption recorded: LMMS .mmp is an *uncompressed XML* project file (the compressed sibling is .mmpz). xmllint is therefore a valid test for .mpp/.mmp here. MilkyTracker .mmp is binary — if the header is not `<?xml`, row B2 becomes N/A-binary, not FAIL.

| ID | Artifact path | Exact test command | Expected result | Status | Raw evidence (paste output) |
|----|---------------|--------------------|-----------------|--------|------------------------------|
| A1 | album-manifest.json | `python3 -m json.tool content/milkups/album/album-manifest.json >/dev/null; echo EXIT=$?` | EXIT=0 (valid JSON) | — | — |
| A1b | album-manifest.json | `python3 -c "import json;d=json.load(open('content/milkups/album/album-manifest.json'));print(len(d.get('tracks',[])))"` | prints `5` | — | — |
| A1c | manifest vs disk | set-compare manifest track filenames against `ls -1 content/milkups/album/modules/*.xm` basenames | both directions empty diff | — | — |
| B1 | modules/*.xm count | `ls -1 content/milkups/album/modules/*.xm \| wc -l` | `5` | — | — |
| B2 | modules/*.xm loadable | `for f in content/milkups/album/modules/*.xm; do xmp --load-only "$f"; echo "$f -> EXIT=$?"; done` | silent, EXIT=0 for all 5 | — | — |
| B2b | xmp availability | `which xmp \|\| echo XMP-MISSING` | if XMP-MISSING, row B2 = BLOCKED (tool absent). Do NOT install. | — | — |
| B2c | module format sanity | `file content/milkups/album/modules/*.xm` | reports Extended Module / FastTracker II | — | — |
| C1 | projects/*.mmp count | `ls -1 content/milkups/album/projects/*.mmp \| wc -l` | `5` | — | — |
| C2 | projects/*.mmp well-formed | `for f in content/milkups/album/projects/*.mmp; do xmllint --noout "$f"; echo "$f -> EXIT=$?"; done` | silent, EXIT=0 for all 5 | — | — |
| C2b | non-XML guard | `head -c 8 <file> \| od -c` | starts `<?xml`; else record N/A-binary + hexdump | — | — |
| D1 | renders/ file count | `ls -1 content/milkups/album/renders/ \| wc -l` | `5` | — | — |
| D2 | render is real audio | `for f in content/milkups/album/renders/*; do echo "== $f"; ffprobe -v error -show_entries format=duration,size,bit_rate,format_name -of default=nw=1 "$f"; echo "EXIT=$?"; done` | EXIT=0, duration>0s, size>100000 bytes | — | — |
| D2b | render not a stub | `find content/milkups/album/renders -size -100k -type f` | empty output (no 0-byte or 44-byte header-only stubs) | — | — |
| E1 | README.md | `test -s content/milkups/album/README.md; echo EXIT=$?; wc -c content/milkups/album/README.md` | EXIT=0, non-zero byte count, contains credits + licence + playback instructions | — | — |
| E2 | TRACKLIST.md | `cat content/milkups/album/TRACKLIST.md`; compare titles to manifest | 5 numbered tracks, titles == manifest titles exactly | — | — |
| F1 | gtm/RELEASE-PLAN.md | `test -s .../gtm/RELEASE-PLAN.md; echo EXIT=$?` + read for: release date, channel list, art asset path, sender milkups@zerric.xyz | all present | — | — |
| F1b | domain policy on GTM | `grep -nE "zdotllc\.com\|zdot-dummy\.com" content/milkups/album/gtm/RELEASE-PLAN.md` | no @zdotllc.com for play content; no dummy domain in a live plan | — | — |
| G1 | sales/MONETIZATION.md | `test -s .../sales/MONETIZATION.md; echo EXIT=$?` + read for price points, platforms, revenue split, named owner | all present | — | — |
| H1 | finance/BUDGET.md | `test -s .../finance/BUDGET.md; echo EXIT=$?` + read for cost lines, total, break-even units | present | — | — |
| H1b | budget arithmetic | recompute: sum(line items) == stated total | exact match to the cent | — | — |
| I1 | cross-doc consistency | compare track count + titles across manifest, TRACKLIST.md, release plan, monetization, budget | identical everywhere | — | — |
| J1 | directory integrity | `find content/milkups/album -type f -size 0; find content/milkups/album -name "*.tmp"` | both empty | — | — |
| J2 | version control | `git status --short content/milkups/album`; `git log -1 --format='%h %ad %s' -- content/milkups/album` | files tracked, latest commit shown | — | — |

Release gate: NO row in B, C, D, I may be BLOCKED or FAIL at release time. Rows E–H may ship as PARTIAL only with BossLady's written acceptance, since they are GTM/commercial docs, not the album itself.
