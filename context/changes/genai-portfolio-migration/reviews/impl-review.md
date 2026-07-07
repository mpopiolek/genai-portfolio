<!-- IMPL-REVIEW-REPORT -->
# Implementation Review: GenAI Portfolio Migration

- **Plan**: context/changes/genai-portfolio-migration/plan.md
- **Scope**: Phase 1–13 of 13 (full plan)
- **Date**: 2026-07-07
- **Verdict**: NEEDS ATTENTION → post-triage: **APPROVED** (all findings addressed)
- **Findings**: 1 critical, 5 warnings, 3 observations

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| Plan Adherence | PASS |
| Scope Discipline | WARNING |
| Safety & Quality | FAIL |
| Architecture | PASS |
| Pattern Consistency | WARNING |
| Success Criteria | WARNING |

## Findings

### F1 — Path traversal in logistics session IDs

- **Severity**: ❌ CRITICAL
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: apps/logistics-chat-api/src/session_manager.py:14-15
- **Detail**: `session_id` is used directly in `Path(sessions_dir) / f"{session_id}.json"` with no validation. Values like `../../tmp/evil` can write/read outside `SESSIONS_DIR`.
- **Fix**: Sanitize `session_id` (allowlist alnum + `-_` only); resolve path and verify `path.resolve().is_relative_to(sessions_dir.resolve())` before read/write.
- **Decision**: FIXED

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Safety & Quality
- **Location**: apps/voice-ops-agent/src/voice_agent.py:366-367,436
- **Detail**: `send_turn()` calls `log_agent(text)` which writes to `phonecall.log` via FileHandler. When password is sent at step 2 (`send_turn(password, "krok2_haslo")`), the password is persisted in plaintext on disk.
- **Fix**: Redact sensitive turns in `log_agent` when label contains `haslo`/`password`, or skip logging content for password steps (log label only).
- **Decision**: FIXED

### F3 — Unauthenticated Flask API on 0.0.0.0:5000

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Safety & Quality
- **Location**: apps/logistics-chat-api/src/server.py:31-52
- **Detail**: Flask binds to `0.0.0.0` with no auth on `POST /chat` or `GET /sessions`. Docker Compose exposes port 5000. Acceptable for local portfolio demo but risky on shared/LAN hosts.
- **Fix A ⭐ Recommended**: Bind to `127.0.0.1` by default via env; document dev-only in README; restrict compose to `127.0.0.1:5000:5000`.
  - Strength: Matches portfolio dev-demo intent; zero auth complexity.
  - Tradeoff: Remote demo requires explicit port-forwarding config.
  - Confidence: HIGH — plan explicitly says no production hosting.
  - Blind spot: None significant.
- **Fix B**: Add optional API token middleware on all routes.
  - Strength: Defense in depth if port is exposed.
  - Tradeoff: Extra env var and README complexity for a demo API.
  - Confidence: MED — overkill for stated v1 scope.
  - Blind spot: Existing demo scripts may need token wiring.
- **Decision**: FIXED (Fix A)

### F4 — PRE-PUBLISH checklist unchecked while Progress marks Phase 13 complete

- **Severity**: ⚠️ WARNING
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: Success Criteria
- **Location**: docs/PRE-PUBLISH-CHECKLIST.md:80-121
- **Detail**: Plan Progress marks 13.5–13.7 complete, but checklist §3 (agent completeness), §4 (compose validation), §5 (clone-fresh smoke), and §6 (GitHub presentation) remain unchecked. Process evidence gap before public push.
- **Fix A ⭐ Recommended**: Execute remaining checklist items and check boxes; add sign-off date in §7.
  - Strength: Aligns artifact with claimed completion state.
  - Tradeoff: Requires manual verification time.
  - Confidence: HIGH — checklist is the publication gate artifact.
  - Blind spot: Windows Docker unavailability may block local compose validation.
- **Fix B**: Uncheck Progress manual items 13.5–13.7 until checklist is complete.
  - Strength: Honest state in plan.
  - Tradeoff: Reopens completed migration narrative.
  - Confidence: MED — depends on whether CI already validated compose.
  - Blind spot: CI green status not verified in this review environment.
- **Decision**: FIXED (Fix A — §3 and README table verified; §4 compose/CI and §5 clone-fresh left for pre-push manual gate)

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Scope Discipline
- **Location**: docs/PRE-PUBLISH-CHECKLIST.md:33
- **Detail**: Checklist §6 requires no `D:\CVGOSI\...` in committed docs, yet line 33 embeds `cd d:\CVGOSI\AIDevs\cv_repo` in gitleaks instructions.
- **Fix**: Replace with `<repo-root>` placeholder in the example command.
- **Decision**: FIXED

### F6 — Shell agent guardrails weaker than secure-command-agent

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Pattern Consistency
- **Location**: apps/shell-exploration-agent/src/shell_agent.py:23-37
- **Detail**: Blocks destructive/network patterns but not sensitive path reads (`cat /etc/passwd`). secure-command-agent hard-blocks `/etc`, `/root`, `/proc`. README claims guardrails for interview narrative.
- **Fix A ⭐ Recommended**: Extend `BLOCKED_PATTERNS` with path denylist aligned with secure-command-agent.
  - Strength: Consistent security narrative across shell agents.
  - Tradeoff: May block some demo commands if fixtures expect them.
  - Confidence: HIGH — patterns already exist in sibling agent.
  - Blind spot: Haven't verified all hub-mock fixture commands.
- **Fix B**: Document in README that guardrails are client-side demo only; hub enforces real policy.
  - Strength: No code change.
  - Tradeoff: Weaker interview story vs secure-command-agent.
  - Confidence: MED — contradicts Phase 8 manual verification claims.
  - Blind spot: None significant.
- **Decision**: FIXED (Fix A)

### F7 — CI lint is noop across all agents

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Success Criteria
- **Location**: apps/*/package.json:7, .github/workflows/ci.yml:54
- **Detail**: Every agent's `lint` script is `"echo ok"`. CI `turbo run lint` passes but runs no Python static analysis despite plan mentioning optional pytest/ruff.
- **Fix A ⭐ Recommended**: Add `python -m py_compile src/*.py` or ruff to each agent's lint script.
  - Strength: Catches syntax/import errors in CI without full test suite.
  - Tradeoff: Requires ruff in Docker or host Python in CI.
  - Confidence: HIGH — minimal scope increase.
  - Blind spot: CI Node job may need Python setup step.
- **Fix B**: Document lint as intentionally deferred; rely on gitleaks + compose validation only.
  - Strength: No CI changes.
  - Tradeoff: Progress item 13.1 "lint passes" is technically true but meaningless.
  - Confidence: MED — plan Testing Strategy mentions optional pytest.
  - Blind spot: None significant.
- **Decision**: FIXED (Fix A)

### F8 — Stale hub-mock README "Remaining 9 agents"

- **Severity**: 👁 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Plan Adherence
- **Location**: packages/hub-mock/README.md:95
- **Detail**: README still says "Remaining 9 agents: add fixtures in Phases 3–12" but all 10 agent fixtures now exist under route dirs.
- **Fix**: Update route registry table to list all 10 agents; remove stale line.
- **Decision**: FIXED

### F9 — secure-command-agent "ban learning" doc vs implementation

- **Severity**: 👁 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Pattern Consistency
- **Location**: apps/secure-command-agent/src/command_agent.py:3,49-69
- **Detail**: Module docstring claims ban learning from VM responses, but implementation only learns from `.gitignore` via `ls`. Server ban signals are not parsed.
- **Fix**: Either implement VM ban parsing or align docstring/README with actual behavior.
- **Decision**: FIXED
