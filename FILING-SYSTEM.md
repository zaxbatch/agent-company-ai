# 📁 Z-Dot Team — Filing System (BossLady's Flow Guide)

Two businesses, one filing system. The rule that makes everything safe:
**Z-Dot and LPT Realty never mix.** Different branding, different rules.

---

## 1. The Big Picture

```
z-dot-team/
├── clients/           Z-Dot: per-client folders (proposals, deliverables, notes)
├── marketing/         Z-Dot: marketing material — ready to send, no approval needed
├── landing-pages/     Z-Dot: landing page drafts & builds
├── proposals/         Z-Dot: active proposals
├── resources/         Z-Dot: templates, reference docs, reusable assets
├── archive/           Z-Dot: completed projects (moved here, never deleted)
│
├── LPT/               🔒 LPT REALTY — every file needs Zerric's approval
│   ├── under-review/      ⏳ drafts WAITING for Zerric (check here first)
│   ├── marketing/         ✅ approved marketing
│   ├── landing-pages/     ✅ approved landing pages
│   ├── property-management/ ✅ approved property mgmt files
│   ├── resources/         ✅ approved docs & templates
│   └── archive/           ✅ delivered / superseded
│
└── FILING-SYSTEM.md   ← you are here
```

---

## 2. How Files Move (The Flow)

### Z-Dot work (fast lane)
`created → saved in the right folder → send freely`
No approval gate. Just keep clients in `clients/` and completed work in `archive/`.

### LPT Realty work (approval gate) — 3 steps
1. **DRAFT** — agent saves file as `[DRAFT] topic-v1` in `LPT/under-review/`
2. **REVIEW** — Zerric reviews:
   - ✅ Approved → moved to the correct LPT subfolder, `[DRAFT]` removed
   - 🔁 Changes → agent revises (v2, v3...) and returns it to `under-review/`
3. **DONE** — delivered/superseded → moved to `LPT/archive/`

**Nothing from LPT/ is ever sent or published until Zerric says go.**

---

## 3. Client Tagging
- Clients are tagged **#zdot**, **#lpt**, or **#both**.
- #both clients → ask Zerric which business context applies to each interaction.
- Client folders live in `clients/` for Z-Dot work; LPT client files live under `LPT/`.

---

## 4. What Does NOT Go in This System
- `src/`, `tests/`, `scripts/`, `harness/`, `ssl/` → engineering code, keep as-is
- `communication/` → internal ops + credentials. **Sensitive — don't move or share.**
- `bugs/` → bug reports for the agent software, not business filing

---

## 5. Status Prefixes (at a glance)
| Prefix      | Meaning                              |
|-------------|--------------------------------------|
| `[DRAFT]`   | Not approved — in `LPT/under-review/` |
| *(no prefix)* | Approved & filed in the correct subfolder |
| in `archive/` | Delivered / superseded              |

---

## 6. Naming Convention
`[STATUS] topic - vN.ext`  →  e.g. `[DRAFT] spring-open-house-flyer-v2.pdf`

Version numbers are mandatory for LPT drafts so feedback maps to a specific revision.

---

## 7. Who Does What
- **Agents** create drafts & file them → `LPT/under-review/` (or Z-Dot folders)
- **Zerric** reviews & approves all LPT content — final authority
- **BossLady** oversees the flow, asks for anything unclear
- **CTO (me)** keeps the structure working, specs changes, enforces rules

---

## 8. Quick Status Check

Run `python scripts/filing_status.py` anytime to see:
- what is waiting in LPT/under-review (pending Zerric)
- what is approved in each LPT subfolder
- Z-Dot folder contents
- any drafts that ended up outside under-review (violations)

If it reports a violation, move the file back into under-review before doing anything else with it.
