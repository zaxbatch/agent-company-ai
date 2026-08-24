# Checklist Web Portal — Implementation Spec
Owner: NinjaNerd (CTO) · Implementer: ClickClack (Developer) · Reviewer: NinjaNerd
Deadline: end of day, 2026-08-24. Deliverable must be verified by CTO before it counts as done.

## Goal
A simple checklist web portal the whole team can open in a browser showing:
- every task
- who owns it (assignee)
- whether it is complete (status)
No build step, no external DB, no auth required (internal tool). Runs locally with uvicorn.

## Where it lives
- App: `src/agent_company_ai/checklist/server.py`
- Static UI: `src/agent_company_ai/checklist/static/index.html` (single file, inline CSS/JS)
- Data: `src/agent_company_ai/checklist/data/checklist.json` (seed data already provided)

## Data model (JSON)
Each task:
```json
{
  "id": "unique-string",
  "description": "human readable task",
  "assignee": "ClickClack",
  "status": "pending|assigned|in_progress|review|done|failed|cancelled",
  "priority": 0,
  "result": null,
  "blocker": "what is needed if the task cannot be completed (empty if none)",
  "created_at": "2026-08-23T00:00:00Z",
  "updated_at": "2026-08-23T00:00:00Z"
}
```
Statuses mirror `src/agent_company_ai/core/task.py` TaskStatus exactly. Keep in sync.

## API (FastAPI)
| Method | Path | Behaviour |
|---|---|---|
| GET | / | serves static/index.html |
| GET | /api/tasks | returns all tasks (JSON list) |
| POST | /api/tasks | body {description, assignee?, priority?} → creates task, returns it (201) |
| PATCH | /api/tasks/{id} | body {status?, assignee?, description?, result?, blocker?} → updates fields, sets updated_at |
| DELETE | /api/tasks/{id} | removes task (204) |

Rules:
- PATCH with status "done" should also accept optional result text.
- Empty description → 400. Unknown id → 404. Invalid status → 400.
- All writes persist to checklist.json atomically (write temp file, then os.replace).

## UI (single HTML page)
- Title: "Z-Dot Team Checklist"
- Table columns: Task | Assignee | Priority | Status | Blocker | Updated | Action
- Blocker cell: shows the blocker text; empty blocker shows a dash. Render blocker in amber if non-empty.
- Status shown as colored badge: done=green, failed=red, in_progress=blue, review=amber, pending/assigned=grey.
- Add-task form at top: description input, assignee input, priority select, Add button.
- Each row: "Mark Done" button (sets status done), "Reopen" button (sets status in_progress) for done items, "Delete" button.
- Assignee filter dropdown: All + each unique assignee. Filters rows.
- Status filter dropdown: All + each status.
- Footer line: total tasks, count done, count open.
- No external CDN dependencies. Plain HTML/CSS/JS. fetch() calls the API above.

## Acceptance criteria (must all pass)
1. `uvicorn src.agent_company_ai.checklist.server:app --port 8430` starts with no errors.
2. GET /api/tasks returns the seeded tasks (they must be present in the seed file).
3. POST /api/tasks creates a task that appears in GET /api/tasks and in checklist.json.
8. PATCH /api/tasks/{id} with {"blocker":"..."} persists the blocker and it renders in the UI.
4. PATCH /api/tasks/{id} with {"status":"done"} marks it done and updates updated_at.
5. DELETE /api/tasks/{id} removes it.
6. GET / serves the UI; UI renders seeded tasks with badges, add form works end to end in a browser.
7. No tests are required but if added, they run with `python -m pytest tests/test_checklist.py`.

## Definition of done for this task
Code merged into the repo, app starts, all acceptance criteria pass, CTO verifies live (starts server, hits endpoints, confirms UI serves). Mark the task DONE in the checklist only after CTO verification.

## Check-in loop (required)
- Each task has a `last_checked_at` field (ISO timestamp or null).
- The UI shows a "Check in" button in the header. Clicking it sets `last_checked_at` to now for ALL open tasks assigned to the current user.
- The user identifies themselves once via a name picker (stored in localStorage). No auth needed.
- A "Team check-in" panel in the header shows each assignee and their last check-in time, with a red warning if over 2 hours stale.
- PATCH /api/tasks/{id} accepts `last_checked_at`.
