# MilkUps site — deployment notes

The live site is milkups.netlify.app (Netlify site id 4a780cec-282e-4d35-aa43-f77c70080554).

IMPORTANT: `content/milkups/index.html` is the canonical homepage source. Before
2026-09-17 the live homepage had no versioned source in the repo — it existed only
on the host, so edits could not be reviewed or rolled back. The copy here is now
kept in sync with what is deployed.

Collections live under these paths and are all reachable (verified 200):

| path | what |
|---|---|
| /tracker/ | album-v3 tracker cut, 8 tracks |
| /cold-cuts/ | 6 genres |
| /album2/ | 6 new genres ("Cold Open") |
| /lmms-cut/ | first LMMS-authored render |
| /album/ and /album/v2/ | v1 sets |
| /inventory/ | audio inventory (7 collections, 47 tracks) |

Do not upload to the zerric.xyz FTP path for milkups — that tree is NOT the live
docroot; uploads persist there but 404 publicly (verified past the CDN). Netlify is
the working rail.
