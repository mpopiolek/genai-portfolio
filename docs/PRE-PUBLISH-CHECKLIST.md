# Pre-Publication Checklist

Human-verifiable gate before the first **public** `git push` to GitHub.

Complete every item. Check boxes when done. Keep this file in the repo as documentation — do not commit secrets or rotation tokens here.

---

## 1. Secrets & git hygiene

- [ ] No `.env` files committed (only `.env.example` templates)
  ```powershell
  git ls-files "*.env" | Select-String -NotMatch "\.env\.example"
  # Expected: empty output
  ```
- [ ] Gitleaks / pre-commit secret scan clean on full repo
  ```powershell
  python -m pre_commit run gitleaks --all-files
  ```
- [ ] Manual grep for known leaked patterns (spot-check)
  ```powershell
  rg -i "sk-or-v1|30d39e8c|BARBAKAN|hub\.ag3nts\.org|Zofia2026" apps/ packages/
  # Expected: no matches in committed source
  ```
- [ ] No `*.log`, audio captures, or session dumps in git history for this branch
- [ ] `.gitignore` covers Python artifacts, `.venv/`, `logs/`, `sessions/`

---

## 2. Key rotation (manual — provider dashboards)

Course/source keys may have appeared in local `.env` files or old logs. **Rotate before going public** even if not committed.

- [ ] **OpenRouter** — revoke old key at [openrouter.ai/keys](https://openrouter.ai/keys), create new key for portfolio use only
- [ ] **AIDEVS / course keys** — treat as compromised if ever pasted into source; do not publish; use hub-mock for demos
- [ ] Update local `.env` files with new keys (never commit)
- [ ] Confirm CI does not embed secrets (GitHub Actions uses `GITHUB_TOKEN` only for gitleaks)

Document rotation date and confirmation in your own notes (not in git):

| Provider | Rotated (Y/N) | Date | Notes |
|----------|---------------|------|-------|
| OpenRouter | | | |
| Other API keys | | | |

---

## 3. Agent completeness (all 10)

- [ ] [voice-ops-agent](../apps/voice-ops-agent/README.md) — EN + PL, docker-compose, hub fixture
- [ ] [prompt-optimization-loop](../apps/prompt-optimization-loop/README.md)
- [ ] [log-triage-agent](../apps/log-triage-agent/README.md)
- [ ] [logistics-chat-api](../apps/logistics-chat-api/README.md)
- [ ] [document-to-json-etl](../apps/document-to-json-etl/README.md)
- [ ] [shell-exploration-agent](../apps/shell-exploration-agent/README.md)
- [ ] [secure-command-agent](../apps/secure-command-agent/README.md)
- [ ] [multi-phase-planning-agent](../apps/multi-phase-planning-agent/README.md)
- [ ] [async-planning-agent](../apps/async-planning-agent/README.md)
- [ ] [multimodal-intel-pipeline](../apps/multimodal-intel-pipeline/README.md)

Hub-mock fixtures present under `packages/hub-mock/fixtures/` for each agent's task/routes.

---

## 4. Automated validation

- [ ] `npm install` succeeds at repo root
- [ ] `npm run lint` (turbo) exits 0
- [ ] Docker Compose config valid for all 10 agents + hub-mock
  ```powershell
  docker compose -f packages/hub-mock/docker-compose.yml config
  Get-ChildItem apps/*/docker-compose.yml | ForEach-Object {
    docker compose -f $_.FullName config
  }
  ```
- [ ] GitHub Actions CI green on default branch (gitleaks + lint + compose config)

---

## 5. Clone-fresh smoke test (manual)

On a clean machine or fresh clone:

- [ ] Pick **3 agents** (e.g. voice-ops, shell-exploration, async-planning)
- [ ] Copy `.env.example` → `.env` where needed
- [ ] Run `docker compose up --build` OR local Python + hub-mock with `DEMO_MODE=1`
- [ ] Each selected agent completes with demo flag or exit code 0

---

## 6. GitHub presentation

- [ ] Root [README.md](../README.md) competency table renders correctly on GitHub
- [ ] Repository description set (e.g. "10 GenAI Python agents — Docker portfolio")
- [ ] Default branch protected / PR checks required (optional but recommended)
- [ ] No private paths, internal URLs, or `D:\CVGOSI\...` references in committed docs

---

## 7. If secrets were ever committed

If gitleaks or review finds secrets in git history:

1. **Do not** push publicly until history is cleaned
2. Rotate all exposed keys immediately
3. Use `git filter-repo` or BFG to purge secrets from history
4. Force-push only after team agreement (never force-push shared main without coordination)

Pre-commit gitleaks should prevent new leaks; this section is a recovery playbook.

---

## Sign-off

| Role | Name | Date | OK to publish |
|------|------|------|---------------|
| Owner | | | |
