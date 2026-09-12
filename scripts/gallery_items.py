#!/usr/bin/env python3
"""The review/approval manifest.

Every asset shown in the approval gallery is declared here with its real public
URL and, where known, the verification that backs it. Keeping this as data means
the gallery is regenerated from facts rather than hand-edited HTML.

Each item:
  id        stable key (used as the localStorage key for the decision)
  category  gallery section
  title     display name
  kind      image | audio | video | link
  url       public asset
  meta      short line of facts
  proof     the verification we actually ran (not a claim)
"""
from __future__ import annotations

RAW = "https://raw.githubusercontent.com/zaxbatch/agent-company-ai/main"
BLOB = "https://github.com/zaxbatch/agent-company-ai/blob/main"
CLOUD = "https://res.cloudinary.com/r6natkse"

ITEMS = [
    # ---------------- MilkUps album material ----------------
    dict(id="mu-phat-fm", category="Music (instrumentals)", kind="audio",
         title="PHAT FM (unreleased origin)",
         url=f"{CLOUD}/video/upload/v1789196352/snowsnakes/wlpubtnc65fopy74qwjg.mp3",
         meta="53.0s · F minor · 145 BPM · MilkyTracker · now live on SnowSnakes as song 13",
         proof="XM v1.04 authored from scratch; ffmpeg/libopenmpt renders 53.03s. "
               "Low-end 71.9% of energy (30-120Hz), sub 51.1% (30-60Hz) vs ~18%/1% "
               "on earlier beats. 0 clipped, peak -2.78 dBFS. All 5 QA checks PASS."),
    dict(id="mu-snowbeats-song", source="ss:song:12", category="Music (instrumentals)", kind="audio",
         title="Snow Beats Session — Boombap 92 (unreleased origin)",
         url=f"{CLOUD}/video/upload/v1789192997/snowsnakes/q3ukowtgv28ycewbnfgx.mp3",
         meta="44.3s · D minor · 92 BPM · drums from our Snow Beats game",
         proof="Drum stem correlates 0.798 with the Snow Beats boombap preset loop across "
               "all 4 repeats — the game's audio, not a rerecording. Completed in LMMS with "
               "Monstro/Organic/SID presets. Lead re-levelled 52->100 after being buried at "
               "-39.7 dBFS."),
    dict(id="mu-16bar", category="Music (instrumentals)", kind="audio",
         title="16-Bar Instrumental (128 BPM)",
         url=f"{RAW}/content/experiments/lmms/beat-16bar.mp3",
         meta="31.9s · A minor · 128 BPM · spec-driven LMMS render",
         proof="Section range 1.32x; break section removes the kick entirely. "
               "Tempo error 0.31%, peak -1.36 dBFS, 0 clipped.",
         extra=[("LMMS project", f"{BLOB}/content/experiments/lmms/beat-16bar.mmp"),
                ("JSON spec", f"{RAW}/content/experiments/lmms/beat-16bar.spec.json")]),

    # ---------------- Video ----------------
    dict(id="vid-sdw-trailer", category="Video", kind="video",
         title="Spread Da Word — Trailer",
         url=f"{CLOUD}/video/upload/v1789196356/snowsnakes/tso4zb2i8k6arhjhxdvi.mp4",
         meta="30.0s · 1920x1080 · 24fps · all 7 characters · cut to the 128 BPM beat",
         proof="64 beats at 128 BPM = 30.0s = exactly 720 frames at 24fps, so every cut "
               "lands on a beat. Character art keyed off its dark plate; per-card push-in, "
               "accent wash, name slam, letterbox, white-flash cuts.",
         extra=[("Spread Da Word", "https://spreaddaword.zerric.xyz/"),
                ("MilkUps", "https://milkups.zerric.xyz/"),
                ("SDW soundtracks", "https://milkups.zerric.xyz/album/")]),

    # ---------------- Art ----------------
    dict(id="art-snowbeats", source="ss:doodle:12", category="Art (doodles)", kind="image",
         title="Snow Beats — Too Cold To Stop",
         url=f"{CLOUD}/image/upload/v1789189096/snowsnakes/zexfbpptegpkcu5eugwk.png",
         meta="700x900 PNG · live on SnowSnakes as doodle id 12",
         proof="Posted as zdot_team; GET /api/doodles returns id 12 with this image_url."),
    dict(id="art-family", source="ss:doodle:4", category="Art (doodles)", kind="image",
         title="The Family — Spread Da Word",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_family.png",
         meta="900x800 PNG · SDW roster group shot", proof="Live on snowsnakes doodle id 4."),
    dict(id="art-vin", source="ss:doodle:5", category="Art (doodles)", kind="image",
         title="Vin Negar — The Realest",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_vin.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 5."),
    dict(id="art-q", source="ss:doodle:6", category="Art (doodles)", kind="image",
         title="Q — The Hype Man",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_q.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 6."),
    dict(id="art-manny", source="ss:doodle:7", category="Art (doodles)", kind="image",
         title="Manny 'Da Man' Ayes",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_manny.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 7."),
    dict(id="art-miracle", source="ss:doodle:8", category="Art (doodles)", kind="image",
         title="Miracle Ayes",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_miracle.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 8."),
    dict(id="art-tom", source="ss:doodle:9", category="Art (doodles)", kind="image",
         title="Tom — 32oz Redneck Patriarch",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_tom.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 9."),
    dict(id="art-jr", source="ss:doodle:10", category="Art (doodles)", kind="image",
         title="Tom Jr. — 14oz Optimist",
         url="https://spreaddaword.zerric.xyz/doodles/sdw_char_jr.png",
         meta="800x600 PNG · SDW character", proof="Live on snowsnakes doodle id 10."),

    # ---------------- Published on SnowSnakes ----------------
    dict(id="ss-song-12", source="ss:song:12", category="Published on SnowSnakes", kind="audio",
         title="Snow Beats Session — Boombap 92 (published)",
         url=f"{CLOUD}/video/upload/v1789192997/snowsnakes/q3ukowtgv28ycewbnfgx.mp3",
         meta="song id 12 · posted as sam_rivera · @zdot-dummy.com persona",
         proof="GET /api/songs/12 -> 200, author_name sam_rivera, cover attached, "
               "audio content-type audio/mpeg.", extra=[("SnowSnakes songs", "https://snowsnakes.zerric.xyz/songs")]),
    dict(id="ss-song-11", source="ss:song:11", category="Published on SnowSnakes", kind="audio",
         title="16-Bar Instrumental (published)",
         url=f"{CLOUD}/video/upload/v1789188481/snowsnakes/jdwchf1ilmnrfqccpxuj.mp3",
         meta="song id 11 · posted as zdot_team · SUPERSEDED by song 14 (persona)",
         proof="GET /api/songs/11 -> 200, author_name zdot_team, cover attached. Zerric asked for persona accounts, so this was reposted as nia_brooks (song 14). Song 11 is a duplicate and needs an admin delete.",
         extra=[("SnowSnakes songs", "https://snowsnakes.zerric.xyz/songs")]),
    dict(id="ss-doodle-12", source="ss:doodle:12", category="Published on SnowSnakes", kind="image",
         title="Snow Beats doodle (published)",
         url=f"{CLOUD}/image/upload/v1789189096/snowsnakes/zexfbpptegpkcu5eugwk.png",
         meta="doodle id 12 · posted as zdot_team",
         proof="GET /api/doodles returns id 12.", extra=[("SnowSnakes doodles", "https://snowsnakes.zerric.xyz/doodles")]),

    # ---------------- Superseded ----------------
    dict(id="old-8bar", category="Superseded", kind="audio",
         title="8-Bar Demo (v1)",
         url=f"{RAW}/content/experiments/lmms/beat-8bar.mp3",
         meta="16.9s · A minor · 128 BPM · REJECTED: longer version only",
         proof="KNOWN FLAW: arrangement contrast only -1.0%, so it is one groove rather "
               "than a build (adding transient hits barely moves RMS). Superseded by the "
               "16-bar version.", extra=[("LMMS project", f"{BLOB}/content/experiments/lmms/beat-8bar.mmp")]),
]

CATEGORY_ORDER = ["Music (instrumentals)", "Video", "Art (doodles)",
                  "Published on SnowSnakes", "Superseded"]
