# Z-Dot Team Checklist - How to Use

Everyone checks this list regularly. This is how we track tasks, who owns them, and what's blocking them.

## Where it lives
- Portal app (code): src/agent_company_ai/checklist/
- Task data (single source of truth): src/agent_company_ai/checklist/data/checklist.json
- Implementation spec: tasks/CHECKLIST-PORTAL-SPEC.md
- How to run locally: uvicorn src.agent_company_ai.checklist.server:app --port 8430

## Fields on every task
- Description, Assignee, Priority, Status, Blocker (what's needed if it can't be completed), Updated, Result

## Rules for the team
0. CHECK REGULARLY - the list is live and changes often. Check it frequently, not just at session start.
1. Check the portal regularly throughout the day - work sessions stay active, so check in often, not just at session start.
2. If a task is blocked, the blocker field must say what's needed and who can unblock it.
3. Update status as you work: pending -> assigned -> in_progress -> done (or failed, with a reason).
4. Nothing is marked done until the reviewer verifies it. Reviewers are listed on the task.
5. Manny (PM) owns keeping this list current and synced with the other PM.
