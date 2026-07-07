# Pre-Publication Checklist

Human-verifiable gate before the first **public** `git push` to GitHub.

Complete every item. Check boxes when done. Keep this file in the repo as documentation — do not commit secrets or rotation tokens here.

---

## 1. Secrets & git hygiene

- [x] No `.env` files committed (only `.env.example` templates)
  **PowerShell:**
  ```powershell
  git ls-files "*.env" | Select-String -NotMatch "\.env\.example"
  # Expected: empty output
  ```
  **Git Bash / WSL / Linux:**
  ```bash
  git ls-files | grep '\.env$' | grep -v '\.env\.example$'
  # Expected: empty output
  ```

- [x] Secret scan clean (gitleaks or equivalent)
  **Preferred on Linux / CI:** GitHub Actions job **Secret scan** after push (runs gitleaks on Ubuntu).
  **pre-commit (Linux / macOS):**
  ```bash
  python -m pre_commit run gitleaks --all-files
  ```
  **Windows — known issue:** `pre-commit` gitleaks may crash with `panic: wasm error: invalid table access`. That is a **local tooling bug**, not proof of secrets in the repo. Use one of these instead:
  1. **Native gitleaks** (recommended locally on Windows):
    ```powershell
     winget install gitleaks
     cd <repo-root>
     gitleaks detect --source . --verbose
    ```
  2. **Manual spot-check** on committed agent code (required minimum on Windows):
    ```powershell
     rg -i "sk-or-v1|30d39e8c|BARBAKAN|hub\.ag3nts\.org|Zofia2026" apps/ packages/
    ```
     Expected: **no matches** in `apps/` or `packages/`. Matches only in `context/` or `docs/` planning text are documentation references, not live keys.
  3. **Skip broken hook** while running other pre-commit checks:
    ```powershell
     $env:SKIP = "gitleaks"
     python -m pre_commit run --all-files
     Remove-Item Env:SKIP
    ```

- [x] Manual grep for known leaked patterns (spot-check — same as above if gitleaks unavailable)
- [x] No `*.log`, audio captures, or session dumps in git history for this branch
- [x] `.gitignore` covers Python artifacts, `.venv/`, `logs/`, `sessions/`

---



## 2. Key rotation (manual — provider dashboards)

Course/source keys may have appeared in local `.env` files or old logs. **Rotate before going public** even if not committed.

- [x] **OpenRouter** — revoke old key at [openrouter.ai/keys](https://openrouter.ai/keys), create new key for portfolio use only
- [x] **AIDEVS / course keys** — treat as compromised if ever pasted into source; do not publish; use hub-mock for demos
- [x] Update local `.env` files with new keys (never commit)
- [x] Confirm CI does not embed secrets (GitHub Actions uses `GITHUB_TOKEN` only for gitleaks)

Document rotation date and confirmation in your own notes (not in git):


| Provider       | Rotated (Y/N) | Date       | Notes   |
| -------------- | ------------- | ---------- | ------- |
| OpenRouter     | y             | 07.07.2026 | cv-repo |
| Other API keys |               |            |         |


---



## 3. Agent completeness (all 10)

- [x] [voice-ops-agent](../apps/voice-ops-agent/README.md) — EN + PL, docker-compose, hub fixture
- [x] [prompt-optimization-loop](../apps/prompt-optimization-loop/README.md)
- [x] [log-triage-agent](../apps/log-triage-agent/README.md)
- [x] [logistics-chat-api](../apps/logistics-chat-api/README.md)
- [x] [document-to-json-etl](../apps/document-to-json-etl/README.md)
- [x] [shell-exploration-agent](../apps/shell-exploration-agent/README.md)
- [x] [secure-command-agent](../apps/secure-command-agent/README.md)
- [x] [multi-phase-planning-agent](../apps/multi-phase-planning-agent/README.md)
- [x] [async-planning-agent](../apps/async-planning-agent/README.md)
- [x] [multimodal-intel-pipeline](../apps/multimodal-intel-pipeline/README.md)

Hub-mock fixtures present under `packages/hub-mock/fixtures/` for each agent's task/routes. *(Verified 2026-07-07 — impl review.)*

---



## 4. Automated validation

- [x] `npm install` succeeds at repo root
- [x] `npm run lint` (turbo) exits 0
- [ ] Docker Compose config valid for all 10 agents + hub-mock *(run locally when Docker available, or rely on CI compose-config job)*
  ```powershell
  docker compose -f packages/hub-mock/docker-compose.yml config
  Get-ChildItem apps/*/docker-compose.yml | ForEach-Object {
    docker compose -f $_.FullName config
  }
  ```
- [ ] GitHub Actions CI green on default branch (gitleaks + lint + compose config) — **authoritative gitleaks gate** if local pre-commit fails on Windows *(confirm on GitHub before public push)*

---



## 5. Clone-fresh smoke test (manual)

On a clean machine or fresh clone *(required before first public push)*:

- [ ] Pick **3 agents** (e.g. voice-ops, shell-exploration, async-planning)
- [ ] Copy `.env.example` → `.env` where needed
- [ ] Run `docker compose up --build` OR local Python + hub-mock with `DEMO_MODE=1`
- [ ] Each selected agent completes with demo flag or exit code 0

---



## 6. GitHub presentation

- [x] Root [README.md](../README.md) competency table renders correctly on GitHub *(10 agents listed — verified 2026-07-07)*
- [ ] Repository description set (e.g. "10 GenAI Python agents — Docker portfolio")
- [ ] Default branch protected / PR checks required (optional but recommended)
- [x] No private paths, internal URLs, or `D:\CVGOSI\...` references in committed docs *(fixed 2026-07-07)*

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


| Role  | Name | Date | OK to publish |
| ----- | ---- | ---- | ------------- |
| Owner |      |      |               |


