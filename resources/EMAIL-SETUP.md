# Email from ez@zerric.xyz — Team Guide

**Channel to reach Zerric:** email works and is verified. For instant text, use the
T-Mobile SMS gateway (below).

## Account
- Sender: ez@zerric.xyz (Hostinger mail on zerric.xyz domain)
- IMAP: imap.hostinger.com:993 (SSL) — username ez@zerric.xyz
- SMTP: smtp.hostinger.com:465 (SSL) — username ez@zerric.xyz
- Password: stored in `communication/credentials.txt` (git-ignored, DO NOT commit/paste)
- Thunderbird profile `bz60b9tj.default-default` already has this account configured.

## Send via script (recommended for agents)
```bash
python3 scripts/send_email.py \
  --to "zdotconnect@gmail.com" \
  --subject "Subject here" \
  --body "Message body"
```
The script reads the password from `communication/credentials.txt` automatically.
Add `--from-name "Your Name"` to sign it so Zerric knows who to reply to.

## Send via Thunderbird
1. Open Thunderbird (profile is already set up).
2. Click Write / New Message. It sends from ez@zerric.xyz.
3. Compose and Send. (GUI click needed — agents can't click it; script is preferred.)

## Reach Zerric's phone (T-Mobile email-to-SMS)
T-Mobile lets you email a phone number as a text: `5022995252@tmomail.net`.
Send from ez@zerric.xyz to that address and it lands on his phone as an SMS.
Keep messages short and start with a recognized word (TEST, PING, etc.) if the
gateway requires it.

## Rules
- Never commit credentials. Never paste the password in chat/email/tickets.
- Always put who you are in the body so Zerric knows which team member to reply to.
- This is a business channel — no spam, no client info without need.
