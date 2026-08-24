# SNITCH: RATS IN THE GRASS — Online v1 Build Spec

> Status: APPROVED scope (BossLady 2026-08-24) — "user signs in to play and I collect a lead."
> Design source: resources/snitch/GAME-DESIGN.md (canonical).

## The money loop this serves
Sign-in → lead captured (HubSpot) → play live with a friend → share → more sign-ins.

## Flow
## Game modes (v1)
1. **SOLO VS BOTS** — 1 human + up to 3 AI rats. Instant play, no invite needed.
   Best for lead capture ("sign in and play right now"). Bots are local AI (no P2P).
2. **PRIVATE (invite by link)** — host creates room -> room code + share link
   (zerric.xyz/snitch/?room=CODE) -> guest opens link, signs in, joins live board.
   P2P via PeerJS; host authoritative + must stay online.
3. **QUICK PLAY (random match)** — join an open room from a lobby registry
   (Netlify Blobs). Best-effort: matches against the first open room with a live host.
   If none open, offer "play vs bots" as fallback.

## Flow (all modes)
```
Sign-in screen (name + email)   <-- LEAD CAPTURE (every player, every mode)
  -> POST /api/lead (Netlify function; token server-side)
  -> HubSpot upsert by email (create if new) + Netlify Blobs log
  -> pick a rat -> start/join game
Play turn by turn: roll -> move -> scenario card -> snitch/trust decisions
```

## IN v1 (must work for first live game)
- Sign-in screen (name + email, NO password — lead-form friction, per CTO rec)
- Room code + share link (copy button; QR optional v1.1)
- 2–4 players (4-player cap, BossLady) — 5 rats to choose from
- Snake board: ~40 spaces across the 8 themed zones (Dumpster start → Rat King's Lair finish)
- Turn loop: roll dice → move → resolve space (scenario card auto-drawn for Sewer/Alley/Lake/Woods) → snitch/trust/cheese decisions
- Trust tokens + cheese tokens (tracked on board)
- Jail: roll 6 to escape; Lake: penalty
- Win: first to finish + bonus points for trust/cheese (scoring screen)
- Rat abilities IN (simple versions): Cheese Chaser +2 cheese, Sewer Scout reroll, Alley Catcher +1 trust on stay-silent, City Sneaker no-trust-loss steal, Woodland Explorer ignore 1 woods penalty
- P2P realtime via PeerJS (host authoritative; host must stay online — documented trade-off)
- Solo vs bots mode (local AI) — instant play, no peer needed
- Quick-play: open-room registry in Netlify Blobs + join-random; fallback to bots
- Bot AI: roll dice, make snitch/stay-silent choices, spend trust sometimes (simple strategy, beatable)
- Mobile-first, no app store, works on static hosting

## OUT (post-MVP)
- Predator tokens (cat/owl) — optional add-on from design
- Password/accounts, "resume my game", cross-device persistence
- Server-authoritative rooms (host can leave) — needs backend access we don't have
- Public self-serve leaderboards

## Technical pieces (deliverables)
1. `netlify/functions/lead.mjs` — POST /api/lead: validate email, HubSpot upsert (GET by email → POST/PATCH), log to Netlify Blobs, return ok. Mirrors proven tasks.mjs pattern.
3. Game page `public/snitch/index.html` — sign-in screen + board + PeerJS client + turn logic + bot AI module (bots.js).
4. Lobby registry: `netlify/functions/room.mjs` — open rooms list for quick-play (Blobs).
4. HubSpot: contacts tagged `snitch-game` source for funnel segmentation.

## Verified facts (2026-08-24)
- HubSpot token: GET by email / PATCH / POST / DELETE all verified working (batch upsert returns 400 — use per-contact flow).
- Netlify Blobs + functions pattern proven (tasks.mjs live on tasks.zdotllc.com).
- SnowSnakes has NO reusable register API (form-only) — we own lead capture.
- zerric.xyz FTP access NOT yet available; hosting decision pending (Netlify now vs zerric.xyz later).

## Open decisions (BossLady)
1. Password: NO in v1 (recommended) vs yes.
2. Hosting: Netlify URL now vs wait for zerric.xyz/snitch.
