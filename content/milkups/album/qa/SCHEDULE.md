# MilkUps Album — Schedule, Cycle 3
Anchor: D0 = first working day of cycle 3 (target Mon 1 Sep 2026). All dates are D+N and shift 1:1 if D0 moves. Owner authority: BossLady is CREATIVE DIRECTOR (Zerric's approval to green-light MilkUps decisions); Zerric is EDITOR and holds the final pass; PM (Meta) owns the QA gate and the schedule.

| # | Workstream | Owner | Deliverable | Depends on | Start | Due | Acceptance gate |
|---|-----------|-------|-------------|-----------|-------|-----|-----------------|
| M1 | Module composition | CTO | 5 × .xm modules | — | D1 | D4 | 5 files, each `xmp --load-only` EXIT=0 |
| M2 | LMMS projects | Developer (under CTO) | 5 × .mmp | M1 | D3 | D6 | `xmllint --noout` EXIT=0 ×5 |
| M3 | Renders | CTO | 5 × audio renders | M2 | D5 | D7 | ffprobe: duration>0, size>100 KB, no stubs |
| M4 | Manifest + README + tracklist | Developer | album-manifest.json, README.md, TRACKLIST.md | M1 (titles), M3 (durations) | D4 | D8 | json.tool EXIT=0; track count == 5; cross-doc title match |
| M5 | GTM | Marketer | gtm/RELEASE-PLAN.md | M4; BossLady creative sign-off | D6 | D9 | date, channels, art path, sender milkups@zerric.xyz; no @zdotllc.com |
| M6 | Monetization | Sales | sales/MONETIZATION.md | M5 (channels) | D7 | D10 | price points, split, named owner |
| M7 | Budget | Finance | finance/BUDGET.md | M3 (render/hosting), M6 (prices) | D8 | D11 | line items sum to stated total; break-even units |
| M8 | QA GATE | Meta (PM) | QA-REPORT.md verdicts with pasted evidence | M1–M7 | D11 (pre-wire from D8) | D12 | every B/C/D/I row PASS with pasted output; zero BLOCKED |
| M9 | Final editorial pass | Zerric (EDITOR) via BossLady (CREATIVE DIRECTOR) | written approval to ship | M8 all-PASS | D12 | D13 | explicit approval; Z-Dot/LPT separation confirmed |
| M10 | Release | Marketer | live posts + send from milkups@zerric.xyz | M9 | D13 | D14 | post URLs + send log recorded |

## Critical path
M1 → M2 → M3 → M4 → M8 → M9 → M10.

- M5, M6, M7 run in parallel and feed M8. They are the schedule's real risk: M5 slipping past D9 drags M6, M7 and then M8 with it (float = 0).
- The build chain M1→M2→M3 is the binding constraint, and it has consumed zero of its four days because no build artifacts exist. Current completion: 0%.
- Any single day lost in M1 costs one day on M10. There is no slack anywhere on this path.

## Escalations
1. CTO: name the .xm/.mmp build owner and confirm the D1 start. Without that confirmation the D14 release date is not real.
2. Marketer: do not begin M5 copy until M4 freezes final track titles — otherwise the GTM doc is rewritten twice.
3. Zerric/BossLady: M9 is a hard gate; nothing ships on a PARTIAL QA report.
