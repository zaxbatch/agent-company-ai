# SNITCH: RATS IN THE GRASS — Canonical Game Design

> Source: BossLady (Zerric/Z-Dot), 2026-08-24. This is the authoritative design for the
> game, originally outlined as a physical board game.
> **Universe note:** SNITCH is a STANDALONE board game — NOT part of the Spread Da Word animated series.
> Spread Da Word = the animated series (separate project). Keep them fully separate. The online boardgame (zerric.xyz/snitch)
> implements this design. Any deviation must be flagged and approved.

## Game Title
**Snitch: Rats in the Grass** — plays on the "snake in the grass" idea + rat theme.

## Board Design — The Pathway
The pathway is a **snake in the grass** winding through different scenes. The snake's body
forms the spaces; its head sits at the finish (or the dumpster, depending on direction).
Scales double as spaces — some blank, some with special actions (Decision, Event, etc.).

### Key Locations (in path order)
| # | Location | Theme/Visual | Mechanic |
|---|----------|--------------|----------|
| 1 | **Start: The Dumpster** | Giant overflowing dumpster, trash bags, food scraps | "Start your journey from the dumpster. Will you snitch or survive?" |
| 2 | **Sewer** | Dark tunnels, pipes, grates, dripping water, glowing green slime | Draw a card: take the shortcut OR get stuck / lose a turn |
| 3 | **Alleys** | Narrow gritty streets, trash cans, graffiti, rats in shadows | Decision space: avoid danger or snitch on other rats |
| 4 | **City Life** | Bright, bustling, humans, food stalls | Steal food for points, risk losing trust if caught |
| 5 | **Woods** | Trees, roots, hiding spots, predators | Event space: escape predators or find hidden treasure |
| 6 | **Lake** | Murky water, fish lurking, dock/lily pads | Penalty: "sleep with the fishes" — lose turn or go back |
| 7 | **Jail** | Rat trap / cage, cheese bait | Roll to escape (6) or lose a turn / points |
| 8 | **Finish: Rat King's Lair** | Trash throne, giant cheese wheel | Final decision: share the cheese (trust + bonus) or take it all (max points, lose trust) |

## Player Pieces — The Rats
Each player picks a unique rat (personality drives attachment). 5 rats total.

| Rat | Look | Ability |
|-----|------|---------|
| Cheese Chaser | Holds a cheese wedge | Starts with +2 cheese tokens |
| Sewer Scout | Flashlight | Reroll dice in the Sewer |
| Alley Catcher | Tiny hat | +1 Trust when choosing "stay silent" |
| City Sneaker | Backpack | Steals food without losing trust |
| Woodland Explorer | Leaf umbrella | Ignores one Woods penalty per game |

Each rat has a catchphrase (e.g., Cheese Chaser: "I'd snitch for a slice.").

## Core Mechanics
1. **Snitching** — snitch on another rat: move ahead 3 spaces, gain points, lose 1 Trust Token
2. **Trust Tokens** — spend to skip penalties, gain bonuses, win tiebreaks
3. **Sleep with the Fishes** — land on Lake → draw penalty card (lose a turn / go back 2)
4. **Jail** — roll a 6 to escape; otherwise lose a turn
5. **Rat King's Lair** — final space: "Share the cheese (gain Trust + bonus) or take it all (max points, lose Trust)"

## Scenario Cards (web = auto-drawn)
- **Sewer**: "You find a shortcut! Move ahead 2 — but another rat might follow. Let them (+1 Trust) or block them (+2 points, −1 Trust)"
- **Alley**: "You see another rat stealing food. Snitch (+3 points, −1 Trust) or stay silent (+1 Trust)"
- **Lake**: "You fall in! Roll 1-3: lose a turn. Roll 4-6: swim to safety."

## Winning (LOCKED — BossLady 2026-08-24)
The first rat to reach the finish line **wins the game**. Bonus points are awarded for:
1. **High trust** — bonus per Trust Token held at the end
2. **Helping other rats** — bonus per help/"let them follow" action
3. **Collecting the most points along the way** — bonus for highest points collected
Results screen shows placement + bonus breakdown + "Top Rat" (highest combined score incl. bonuses).

## Optional Add-Ons (NOT in v1)
1. Rat abilities (each rat has unique ability) — *partially IN v1 (see V1-SPEC)*
2. Predator tokens (cat/owl moving around the board, adding tension)
3. Cheese Tokens economy (collect cheese for bonus points / special actions)
