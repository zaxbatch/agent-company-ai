# MilkUps — Mixed-Engine Album Spec (tracker + LMMS)

Status: SPEC — NinjaNerd (CTO), 2026-09-13
Owner: ClickClack (build) · QA: lmms_qa.py + loudness gate · Creative: BossLady

## 1. Why
The live album "The Shelves Raised Us" (8 tracks) is all ONE production lineage
(SDW genre themes: Trap/Lofi/Electro/Pop/Country/Funk/Synthwave/Icy) — a single
voice and palette. Zero tracker material. Verified 2026-09-13.

## 2. Verified engine capability (measured, not assumed)
- Tracker: scripts/xm_lib.py authors real FastTracker II .xm from pure Python
  (delta-encoded 8-bit samples, patterns, instruments). scripts/phat_beat.py is
  the reference song. ffmpeg decodes .xm via libopenmpt (phat-fm.xm -> 52.93 s).
  No extra packages required.
- LMMS: `lmms render <proj.mmp> -o out.wav` works headless
  (snow-beats-song.mmp -> 44.35 s / 7.8 MB). "Not enough samples" warnings benign.

## 3. THE RISK: loudness spread (measured)
| source            | I (LUFS) | LRA |
|-------------------|----------|-----|
| tracker phat-fm   | -17.6    | 4.7 |
| LMMS snow-beats   | -16.1    | 1.5 |
| album 01-trap     | -20.8    | 3.1 |
| album 08-icy      | -24.1    | 3.2 |

The CURRENT album already spans 3.3 LU between just two tracks. Alternating
engines unmastered pushes it to ~8 LU — "variety" becomes a volume rollercoaster.
Mastering is MANDATORY, not optional.

Fix verified: `loudnorm=I=-14:TP=-1.0:LRA=9`
  tracker normalized -> -13.0 LUFS / -1.0 dBFS peak
  LMMS    normalized -> -13.7 LUFS / -1.0 dBFS peak   (0.7 LU apart)

## 4. Pipeline (per track)
1. Author: tracker -> .xm via xm_lib + song generator ; LMMS -> .mmp via lmms_*.py
2. Render: ffmpeg -i t.xm -c:a pcm_s16le t.wav  |  lmms render t.mmp -o t.wav
3. Master: ffmpeg -af "loudnorm=I=-14:TP=-1.0:LRA=9"  (uniform across ALL tracks)
4. Encode: MP3 320k CBR
5. Name: audio/NN-slug.mp3  (MUST match album.html TRACKS paths, relative)

## 5. Track plan (engine alternation for real variety)
Odd tracks = tracker (chip/PSG) · Even tracks = LMMS (Monstro/SID/Organic)
Optional 1-2 hybrids: tracker lead over LMMS rhythm.
Each track gets a distinct tempo AND genre so the variety is audible, not cosmetic.

## 6. Deploy targets (BOTH)
- domains/milkups.zerric.xyz/public_html/album/  (+ album/audio/)
- domains/zerric.xyz/public_html/milkups/album/
Update: album.html TRACKS array, tracklist.txt, TheShelvesRaisedUs-*.zip
REGENERATE the zip so the download matches the album.

## 7. CRITICAL pre-existing defect — fix during this build
content/milkups/audio/ does NOT exist in the repo, but the live album serves
/album/audio/*.mp3 and album.html uses RELATIVE paths (audio/01-...mp3).
=> A rebuild+deploy from the repo SILENTLY 404s all 8 tracks.
Album audio is currently deployment-only. Commit the audio (or a fetch script)
so the repo can reproduce a working album.

## 8. QA gate (all must pass)
- [ ] every track HTTP 200 with real bytes (not a 403/404 HTML page)
- [ ] integrated loudness within 1 LU of -14 across ALL tracks
- [ ] true peak <= -1.0 dBTP on every track
- [ ] zip contents == deployed audio (byte sizes match)
- [ ] album.html TRACKS paths resolve on BOTH docroots
- [ ] zip regenerated after final masters
