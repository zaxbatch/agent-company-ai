# GitHub Accounts & Keys — Policy (Z-Dot Team)

> Rule: **one account per domain. Keys never cross. Identity set per-repo, never global.**
> Created 2026-08-24 (Zerric directive). Violations cause wrong-author commits + auth confusion.

## The two accounts

| GitHub account | Owns | Domains / projects |
|----------------|------|--------------------|
| **zaxbatch** | zerric.xyz + snowsnakes + personal-domain projects | snowsnakes.zerric.xyz, zerric.xyz, Spread Da Word, Snitch, cassettes |
| **zdot** (zdotllc) | Z-Dot LLC business | zdotllc.com, task portal, client SaaS, marketing sites, Stripe/payments, CRM |

**Test which account a key is:**
```bash
ssh -T git@github.com          # → "Hi <account>!"
```

## SSH keys — one per account, wired by alias

| Key file | Account | Status (verified 2026-08-24) |
|----------|---------|------------------------------|
| `~/.ssh/id_ed25519` | zdotllc (comment zdotconnect@gmail.com) | ✅ authenticates as zdotllc |
| `~/.ssh/id_ed25519_zdotllc` | (zdotllc@email.com) | ❌ NOT registered on GitHub — do not use |
| `~/.ssh/id_ed25519_zaxbatch` | zaxbatch | ❌ MISSING — create + register on zaxbatch account |

**~/.ssh/config — alias per account (the rule that prevents confusion):**
```
# Z-DOT (zdotllc) — business
Host github-zdot
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519
  IdentitiesOnly yes

# ZAXBATCH — zerric.xyz / snowsnakes
Host github-zaxbatch
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_zaxbatch
  IdentitiesOnly yes
```

## Remote URL convention (the hard rule)

| Repo type | Remote URL |
|-----------|-----------|
| zaxbatch (zerric.xyz) | `git@github-zaxbatch:zaxbatch/<repo>.git` |
| zdot (zdotllc) | `git@github-zdot:zdotllc/<repo>.git` |

NEVER use plain `git@github.com:...` when both accounts exist on the machine —
it always picks the default key (currently zdotllc), so zaxbatch pushes would
authenticate as the wrong account.

## Identity — per repo, never global

```bash
# inside each repo, AFTER cloning:
git config user.name "zaxbatch"        # or "zdotllc"
git config user.email "zaxbatch@users.noreply.github.com"   # GitHub noreply
# NEVER: git config --global user.name
```

Verify before pushing:
```bash
git config user.name   # must match the repo's owning account
git remote -v          # must use the matching alias
```

## Tokens / secrets — never shared

- **Never** put a GitHub token (`ghp_*`, `github_pat_*`) in `.env`, `credentials.txt`, or any shared file.
- HTTPS tokens: one per account, scoped to that account's repos, stored only in the account owner's credential store (git-ignored).
- SSH keys stay in `~/.ssh/`, `chmod 600`, never copied into repos or chat.

## When adding a new repo

1. Decide owner by domain: zerric.xyz/snowsnakes → zaxbatch; zdotllc/client → zdot.
2. Create repo under the OWNING account.
3. Clone with the matching alias URL.
4. Set local `user.name` + `user.email` to the owning account.
5. Push, verify `git log` author matches the owner.

## Current cleanup needed (2026-08-24)

- [ ] Create + register `id_ed25519_zaxbatch` on zaxbatch GitHub (Zerric) — currently missing.
- [ ] Remove/retire `id_ed25519_zdotllc` (unregistered, confusing name) — or register it if intended.
- [ ] This repo `agent-company-ai` lives under zaxbatch but currently pushes as zdotllc (collaborator). Align: either add zdotllc as collaborator intentionally (fine) OR switch to zaxbatch key when created.
