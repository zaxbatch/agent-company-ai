# SnowSnakes Content Automation — Team Guide

**Goal:** jokes + games run in the background so the team focuses on bigger goals.
Do NOT paste daily jokes in the team chat — the bot handles it.

## Jokes (daily, automated)
- Script: `scripts/post_daily_jokes.py`
- Posts ~20 ORIGINAL dad jokes/day, setup + punchline (flip-card format), random varied topics.
- Rotates across the 8 team accounts (ClickClack_, TedBear, mark, seleena, manny, meta, jasmine, trevor).
- Tracks used jokes in `.agent-company-ai/joke_state.json` so nothing repeats within ~3 days.
- Scheduled: cron `0 9 * * *` (daily 09:00). Log: `/tmp/snowsnakes_jokes.log`
- Manual run: `./venv/bin/python scripts/post_daily_jokes.py` (add `--dry-run` to preview).

## Format rules (IMPORTANT)
- Jokes are FLIP CARDS: `content` = setup, `punchline` = answer ("Click to reveal").
- A joke with an empty punchline is WRONG — it breaks the card. Always include both.
- Topics must be RANDOM and varied — not all food truck / pumpkin / snow snake.

## Games
- Post freely when you build one (1-3/day max). No need to announce in chat.
- Upload via games API: multipart with title/description/icon/tags + base64 `code` + `code_encoding=base64`.

## Reach Zerric
- Email: `python3 scripts/send_email.py --to "zdotconnect@gmail.com" --subject "..." --body "..."` (see resources/EMAIL-SETUP.md)
- Instant (SMS): email to `5022995252@tmomail.net` (T-Mobile email-to-SMS gateway).
