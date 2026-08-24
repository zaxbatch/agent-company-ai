# SNITCH: RATS IN THE GRASS — Online v1 Build Spec

> Status: APPROVED scope (BossLady 2026-08-24) — "user signs in to play and I collect a lead."
> Design source: resources/snitch/GAME-DESIGN.md (canonical).

## The money loop this serves
Sign-in → lead captured (HubSpot) → play live with a friend → share → more sign-ins.

## Flow
```
Host creates game -> gets room code + invite link (zerric.xyz/snitch/?room=CODE)
Guest opens link -> SIGN IN screen (name + email)   <-- LEAD CAPTURE (every player)
  -> POST /api/lead (Netlify function; token server-side)
  -> HubSpot upsert by email (create if new) + Netlify Blobs log
  -> pick a rat -> join live board
Play live, turn by turn: roll -> move -> scenario card -> snitch/trust decisions
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
- Mobile-first, no app store, works on static hosting

## OUT (post-MVP)
- Predator tokens (cat/owl) — optional add-on from design
- Password/accounts, "resume my game", cross-device persistence
- Server-authoritative rooms (host can leave) — needs backend access we don't have
- Public self-serve leaderboards

## Technical pieces (deliverables)
1. `netlify/functions/lead.mjs` — POST /api/lead: validate email, HubSpot upsert (GET by email → POST/PATCH), log to Netlify Blobs, return ok. Mirrors proven tasks.mjs pattern.
2. `netlify/functions/room.mjs` — optional: room code registry in Blobs (host picks code; guest resolves to host peer id via PeerJS).
3. Game page `public/snitch/index.html` — sign-in screen + board + PeerJS client + turn logic.
4. HubSpot: contacts tagged `snitch-game` source for funnel segmentation.

## Verified facts (2026-08-24)
- HubSpot token: GET by email / PATCH / POST / DELETE all verified working (batch upsert returns 400 — use per-contact flow).
- Netlify Blobs + functions pattern proven (tasks.mjs live on tasks.zdotllc.com).
- SnowSnakes has NO reusable register API (form-only) — we own lead capture.
- zerric.xyz FTP access NOT yet available; hosting decision pending (Netlify now vs zerric.xyz later).

## Open decisions (BossLady)
1. Password: NO in v1 (recommended) vs yes.
2. Hosting: Netlify URL now vs wait for zerric.xyz/snitch.
