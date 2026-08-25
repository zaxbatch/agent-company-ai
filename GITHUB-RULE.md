# GitHub Two-Account Rule (Z-Dot Team)
> Purpose: never push to the wrong repo/account. Two GitHub accounts exist; they are NEVER interchangeable.

## The two accounts (HARD SEPARATION)
| Account | Belongs to | Used for | SSH key |
|---|---|---|---|
| **zaxbatch** | zerric.xyz + SnowSnakes + agent-company-ai (this repo) | The playground: SnowSnakes, Spread Da Word, experiments | `~/.ssh/id_ed25519` |
| **zdotllc** | zdotllc.com (BossLady's business) | Z-Dot LLC business repos, client work, marketing/sales | `~/.ssh/id_ed25519_zdotllc` |

## The rule
1. **One repo = one account.** Check the remote BEFORE pushing: `git remote -v`.
   - `git@github.com:zaxbatch/*` → zaxbatch key
   - `git@github.com:zdotllc/*` → zdotllc key
2. **Never** mix keys/repos. If you're in a repo and the remote's owner ≠ the key you'd use, STOP.
3. **Repo-local git config is REQUIRED** per checkout (never global):
   ```
   git config user.name  "zaxbatch"   # or "zdotllc"
   git config user.email "sneakjunkmail@gmail.com"  # zaxbatch's email
   # zdotllc email: use the one tied to the zdotllc account
   ```
   Set it once per repo. `git config --global` is forbidden for user identity.
4. **SSH key selection** is automatic by filename, but only if `~/.ssh/config` maps hosts:
   ```
   # ~/.ssh/config (optional but recommended)
   Host github.com
     IdentityFile ~/.ssh/id_ed25519          # zaxbatch (default)
   Host github-zdotllc
     HostName github.com
     IdentityFile ~/.ssh/id_ed25519_zdotllc  # zdotllc
   ```
   Then zdotllc repos use remote `git@github-zdotllc:zdotllc/REPO.git` so the right key is picked.
5. **Before ANY push:** `git remote -v` (confirm owner) + `git config user.email` (confirm identity). Two checks, 2 seconds, zero mixups.
6. **Secrets:** never commit .env / credentials.txt / config.yaml / tokens to ANY repo (either account). Check `git diff` before every push.

## CURRENT REALITY (2026-08-25 — verified)
- **This machine's DEFAULT key (`~/.ssh/id_ed25519`) = zdotllc account** (ssh -T says "Hi zdotllc!").
  `~/.ssh/id_ed25519_zdotllc` = also zdotllc. NO zaxbatch private key exists on this machine.
- **zaxbatch key is NOT here.** BossLady added only the zaxbatch key FINGERPRINT (SHA256:WyqUu9ep…) to credentials.txt —
  a fingerprint does NOT authenticate. We need the actual private key OR a new key registered to zaxbatch.
- **How to fix (safe, no key travel):** 1) generate new key locally: `ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_zaxbatch -C "zaxbatch@github"`
  2) Zerric adds the .pub to github.com/settings/ssh (zaxbatch account)
  3) add ~/.ssh/config alias `github-zaxbatch` -> IdentityFile ~/.ssh/id_ed25519_zaxbatch
  4) point this repo's remote at `git@github-zaxbatch:zaxbatch/agent-company-ai.git`
- **NEVER paste a private key into credentials.txt/chat/email.** Fingerprint ≠ key.
