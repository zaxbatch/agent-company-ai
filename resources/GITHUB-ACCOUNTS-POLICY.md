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

## NEW-REPO RULE (BossLady 2026-08-25) — which account for new projects
> **When starting ANY new app/project/repo, confirm the GitHub account FIRST. Default by domain:**

| New project is for… | GitHub account | Remote prefix |
|---------------------|----------------|---------------|
| zerric.xyz / snowsnakes / Spread Da Word / Snitch / cassettes / any personal-domain or playground app | **zaxbatch** | `git@github-zaxbatch:zaxbatch/REPO.git` |
| zdotllc.com / task portal / client SaaS / marketing / Stripe / CRM / anything Z-Dot business | **zdot (zdotllc)** | `git@github-zdot:zdotllc/REPO.git` |

**When in doubt, ASK BossLady/Zerric which account before creating the repo.** Default: if it's tied to
a domain, that domain's account owns it. Never guess on ambiguous projects (e.g. an app that touches both).
Create repos with the PAT (create via API) or `gh`, using the account whose key matches.

## SSH keys — one per account, wired by alias

| Key file | Account | Status (verified 2026-08-24) |
|----------|---------|------------------------------|
| `~/.ssh/id_ed25519` | zdotllc (comment zdotconnect@gmail.com) | ✅ authenticates as zdotllc |
| `~/.ssh/id_ed25519_zdotllc` | (zdotllc@email.com) | ❌ NOT registered on GitHub — do not use |
| `~/.ssh/id_ed25519_zaxbatch` | zaxbatch | ✅ VERIFIED 2026-08-25 — authenticates as zaxbatch ("Hi zaxbatch!") |

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

## NEW PROJECTS — which GitHub account? (decision rule)

**Ask first, push second.** Before creating a repo for any new project, confirm
with the owner (Zerric/BossLady) which account. Default rule below.

| New project serves… | GitHub account | Example |
|---------------------|----------------|---------|
| zerric.xyz / snowsnakes / personal-brand fun / Spread Da Word / Snitch / cassettes / community | **zaxbatch** | test123, agent-company-ai |
| Z-Dot LLC business / client SaaS / payments / CRM / marketing sites / B2B tools | **zdot (zdotllc)** | (future) |

**Confirmation protocol (never skip):**
1. When a new app/project is requested, ask: *"Which account — zaxbatch or zdot?"*
2. If it's a play/creative/community thing → zaxbatch (zerric.xyz).
3. If it's business/client/revenue → zdot (zdotllc).
4. Ambiguous (both) → ask Zerric directly. Never guess.

**Repo creation checklist:**
- [ ] Owner confirmed (zaxbatch or zdot)
- [ ] Created under the OWNING account via PAT (`ghp_*` in credentials)
- [ ] Cloned/pushed via matching alias (`git@github-zaxbatch:...` or `git@github-zdot:...`)
- [ ] Local `git config user.name/email` = owning account
- [ ] README says which project + which domain it serves

## NEW PROJECTS — which account? (confirmation rule, 2026-08-25)

**RULE: For every NEW app/project, confirm the GitHub account BEFORE creating a repo.**
No guessing. No "default to zaxbatch." Ask which account the project belongs to.

| Project type | Default account |
|--------------|-----------------|
| zerric.xyz / snowsnakes / personal / creative (Spread Da Word, Snitch, cassettes) | **zaxbatch** |
| Z-Dot business / client work / SaaS / payments / zdotllc.com | **zdot** (zdotllc) |

When a new app is proposed: log the project, ask "which git account?", record the answer
in the ideas log / project doc, then create the repo under the confirmed account.
