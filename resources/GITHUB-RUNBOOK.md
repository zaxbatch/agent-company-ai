# GitHub Runbook (Z-Dot Team) — updated 2026-08-25
> Quick reference for the two-account setup. Full policy: resources/GITHUB-ACCOUNTS-POLICY.md + GITHUB-RULE.md.

## Accounts & keys (verified)
| GitHub | Key | SSH alias | Repos |
|--------|-----|-----------|-------|
| zaxbatch | ~/.ssh/id_ed25519_zaxbatch | git@github-zaxbatch: | zerric.xyz ecosystem (snowsnakes, SDW, Snitch) |
| zdotllc | ~/.ssh/id_ed25519 | git@github-zdot: | business (zdotllc.com, client work) |

## PAT
- In communication/credentials.txt (ghp_…, git-ignored). Scopes: repo, workflow. Used for repo creation + gh CLI.

## Daily commands
- Who am I on SSH: `ssh -T git@github.com` (default = zdotllc) or `ssh -i ~/.ssh/id_ed25519_zaxbatch -T git@github.com`
- Clone zaxbatch repo: `git clone git@github-zaxbatch:zaxbatch/REPO.git`
- New repo (create on GitHub): use PAT via API, then `git remote add origin git@github-zaxbatch:zaxbatch/REPO.git`

## Push checklist (before ANY push)
1. `git remote -v` — owner matches the account
2. `git config user.email` — identity correct (repo-local, never global)
3. `git diff` — no secrets (.env, credentials, keys)
4. `git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectsize) %(rest)' | awk '$1=="blob" && $2>50000000'` — no >50MB blobs in history (GitHub limit 100MB)

## History fix (if a big file is in history — done 2026-08-25 for venv/)
```
FILTER_BRANCH_SQUELCH_WARNING=1 git filter-branch --index-filter 'git rm -r --cached --ignore-unmatch <path>' --prune-empty -- --all
git for-each-ref --format='%(refname)' refs/original | xargs -r -n1 git update-ref -d
git push --force origin main
```

## STATUS 2026-08-25
- zaxbatch/agent-company-ai: history CLEAN (venv purged), push WORKS (verified d96b059..d507205 dry-run).
  If a teammate's clone still shows venv, they're on stale history → `git fetch --all && git reset --hard origin/main` or fresh clone.
- test123: created + pushed (key verification done).
