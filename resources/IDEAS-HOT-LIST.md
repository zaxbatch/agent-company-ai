# 💡 Z-DOT IDEAS HOT LIST — "keep these hot"
> Purpose: every idea from BossLady/Zerric (including "sleepy talk" — often the best ones)
> is captured here with status, so nothing evaporates. Updated live. Source of truth for the
> ideas section on the progress page + portal tasks.
> Rule: sleepy ideas get logged IMMEDIATELY. Status: 🔥 hot (captured) / 🏗 building / ✅ done / 🗄 parked / ❌ nixed.

## 🔥 NEW — capture queue (BossLady 2026-08-24, from pre-sleep convo with Zerric)
| # | Idea | Status | Owner | Notes |
|---|------|--------|-------|-------|
| 1 | **Doodle-making app** that posts straight to SnowSnakes | 🔥 captured | CTO | SnowSnakes already has "Add a Doodle" modal + /api — app could wrap it |
| 2 | **Comic-making app** that posts straight to SnowSnakes | 🔥 captured | CTO | Site has "Create a Comic" modal — builder would feed it |
| 3 | **Simple game builder** that posts straight to SnowSnakes | 🔥 captured | CTO | Site has "Submit a Game" — builder generates game code → POST /api/games |
| 4 | **Snitch mini-game (catch cheese, dodge the cat)** → SnowSnakes | ✅ approved (Seleena) | CTO/ClickClack | Promotes Snitch board game. Promo games ARE allowed on snowsnakes. |
| 5 | **Snitch trailer video** | ❌ nixed (BossLady) | — | Does NOT go on SnowSnakes (video ≠ game) |
| 6 | **Snow Beats ⬇ download** | ✅ done (game 97 → fixed 99) | CTO | Behind gated sign-in; fixed sandbox download via save-file-picker + popup fallback |
| 7 | **10 doodles/day for approval** | ✅ live | CTO | → resources/snowsnakes/doodles-comics-under-review/ + shown on tasks.zdotllc.com/progress |

## 🏗 BUILDING / APPROVED
| # | Idea | Status | Owner | Notes |
|---|------|--------|-------|-------|
| 8 | **Snitch online board game v1** | 🏗 prototype done, needs online layer | CTO | 4-player cap · sign-in = lead · 3 modes · first-to-finish wins + bonus (trust/help/points) |
| 9 | **Invite-a-player by link (live board)** | ✅ in v1 spec | CTO | zerric.xyz/snitch/?room=CODE → P2P PeerJS |
| 10 | **SDW soundtracks 6–8 songs each** | 🏗 5 new tracks rendered; need 6-8/tape | CTO | 2 soundtracks per episode (1 remix + 1 original) |
| 11 | **Cassette "switch tapes" = switch soundtracks** | ✅ live (8 tapes) | CTO | Drag-to-switch upgrade queued |
| 12 | **SnowSnakes = games only (promo games OK)** | ✅ policy | All | No episodes/trailers/media. Cassette player stays (cute). |
| 13 | **Progress page (private)** | ✅ live | CTO | https://tasks.zdotllc.com/progress — auth-gated, proof site + doodles + Snitch links |

## 🗄 PARKED / LATER
| # | Idea | Status | Notes |
|---|------|--------|-------|
| 14 | Predator tokens (cat/owl) in Snitch | 🗄 | Optional add-on from design |
| 15 | Public signup / self-serve / leaderboards | 🗄 | Post-MVP |
| 16 | Bizzy Bee SaaS | 🗄 | Separate future project (NOT Spread Da Word) |

## ⚠️ KEEPING THESE HOT = the workflow
1. New idea → add row here immediately (status 🔥)
2. Every morning: review hot list, move 🔥 → 🏗/✅/❌ as decided
3. Progress page auto-shows this list (build_proof_site.py reads it)
4. Portal tasks created for anything 🏗
