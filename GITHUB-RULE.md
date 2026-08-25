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

## The one active known-issue
- `zaxbatch/agent-company-ai` (this repo) currently has NO write access for zdotllc → pushes from here are blocked until Zerric grants access or we push from the correct account. Escalate to BossLady/Zerric — do NOT work around by changing remotes.
