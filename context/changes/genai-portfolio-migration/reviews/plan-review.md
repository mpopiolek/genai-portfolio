<!-- PLAN-REVIEW-REPORT -->
# Plan Review: GenAI Portfolio Migration

- **Plan**: `context/changes/genai-portfolio-migration/plan.md`
- **Mode**: Deep
- **Date**: 2026-07-06
- **Verdict**: SOUND (after triage fixes)
- **Findings**: 1 critical, 4 warnings, 2 observations

## Verdicts

| Dimension | Verdict |
|-----------|---------|
| End-State Alignment | PASS ✅ (after F3 fix) |
| Lean Execution | PASS ✅ |
| Architectural Fitness | PASS ✅ (after F1 multi-route fix) |
| Blind Spots | PASS ✅ (after F5/F6 fixes) |
| Plan Completeness | PASS ✅ (after F2/F4/F7 fixes) |

## Grounding

Grounding: 6/6 paths ✓, 3/3 symbols ✓ (`@repo/` in README+lockfile, `turbo.json` `.next/**`, voice `phonecall_agent7FLG.py` exists), brief↔plan ✓ (13 phases, decisions match). Progress↔Phase: 13/13 phases matched, checkboxes only in `## Progress`, success criteria counts align.

## Findings

### F1 — Hub mock `/verify`-only cannot serve all 10 agents

- **Severity**: ❌ CRITICAL
- **Impact**: 🔬 HIGH — architectural stakes; think carefully before deciding
- **Dimension**: Architectural Fitness
- **Location**: Phase 2 — Shared Hub Mock; Phase 6, 9, 12
- **Detail**: Plan defines hub-mock as `POST /verify` with `{apikey, task, answer}` only (`plan.md:138`). Logistics-chat-api uses `POST /api/packages` with `{apikey, action, packageid}` (`Zad_3_proxy/endpoint/package_api.py:6-21`, default `AIDEVS_API_URL=https://hub.ag3nts.org/api/packages`). Secure-command-agent hardcodes `https://hub.ag3nts.org/api/shell` (`firmware3FLG.py:27`). Phase 6 adds `fixtures/logistics-chat-api.json` but fixture contract is built for `/verify`. Shared mock cannot satisfy logistics or firmware demos without extension.
- **Fix A ⭐ Recommended**: Extend Phase 2 hub-mock to multi-route stub (`/verify`, `/api/packages`, `/api/shell`) with per-route fixture files; document route registry in `packages/hub-mock/README.md`
  - Strength: One mock server, consistent pattern; matches actual agent coupling points discovered in source.
  - Tradeoff: Phase 2 scope grows; each new route needs fixture authoring.
  - Confidence: HIGH — verified against `package_api.py` and `firmware3FLG.py`.
  - Blind spot: Remaining 7 agents' hub endpoints not fully audited; may reveal more routes.
- **Fix B**: Per-agent local mocks inside each `apps/*` docker-compose (no shared package)
  - Strength: Agents with unusual APIs don't block each other.
  - Tradeoff: Duplicated mock code; contradicts "shared hub mock" decision from planning session.
  - Confidence: MEDIUM — works but erodes consistency goal.
  - Blind spot: Maintenance cost across 10 agents unestimated.
- **Decision**: FIXED via Fix A — multi-route hub-mock (`/verify`, `/api/packages`, `/api/shell`)

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Plan Completeness
- **Location**: Phase 1 success criteria 1.5 vs Phase 13
- **Detail**: Phase 1 manual verification requires `rg "@repo/"` returns empty (`plan.md:117`, Progress 1.5). Root `README.md:19-23` still documents `@repo/ui`, `@repo/eslint-config`, `@repo/typescript-config`. README rewrite is deferred to Phase 13 (`plan.md:653-659`). Phase 1 cannot pass its own gate without either updating README early or relaxing the criterion.
- **Fix**: Add Phase 1 task to replace root `README.md` with minimal portfolio stub (project name + "agents migrating" note); Phase 13 expands to full competency map.
  - Strength: Phase 1 gate becomes passable; no stale Turborepo starter text after JS removal.
  - Tradeoff: README edited twice (stub → full).
  - Confidence: HIGH — `README.md` content verified.
  - Blind spot: None significant.
- **Decision**: FIXED — Phase 1 README stub added; Phase 13 expands to full map

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: End-State Alignment
- **Location**: Phase 3 — automated 3.2; Desired End State line 29
- **Detail**: Plan end state says recruiter runs "without course keys" (`plan.md:29`). Voice agent STT and road-analysis LLM call OpenRouter exclusively (`phonecall_agent7FLG.py:181-236`, `306-337`); edge-tts covers TTS only. Phase 3 automated criterion 3.2 (`docker compose up --abort-on-container-exit` exits 0 with flag) will fail without valid `OPENROUTER_API_KEY`. PRD US-01 forbids course keys, not user-supplied OpenRouter (`prd.md:64,68`). Plan-brief acknowledges this (`plan-brief.md:79`) but Phase 3 success criteria do not.
- **Fix**: Add to Phase 3 Manual Verification: "Demo requires `OPENROUTER_API_KEY` in `.env`; document in README that course keys are replaced by user-owned OpenRouter + hub-mock." Optionally split automated 3.2 into hub-only smoke (start session) vs full demo (needs OpenRouter).
  - Strength: Implementer won't chase false failures; aligns with PRD wording.
  - Tradeoff: "One-command demo" is weaker without user's key.
  - Confidence: HIGH — source agent code confirms OpenRouter-only STT path.
  - Blind spot: CI cannot run full voice demo without secret injection.
- **Decision**: FIXED — split hub smoke vs full demo; README OpenRouter note added

- **Severity**: ⚠️ WARNING
- **Impact**: 🔎 MEDIUM — real tradeoff; pause to reason through it
- **Dimension**: Plan Completeness
- **Location**: Phase 2 — fixture contract (`plan.md:146`)
- **Detail**: Phase 2 defines `{request_match, response}` pairs but not response JSON fields. Voice agent accepts operator text via `response.message`, `response.text`, or transcribed base64 audio (`phonecall_agent7FLG.py:375-381`). Text-only fixtures work and avoid OpenRouter STT; audio fixtures require OpenRouter. Plan Phase 2 voice fixture implies "4-step dialog" but doesn't specify text-field responses — implementer may build audio fixtures unnecessarily.
- **Fix**: Add to Phase 2 Contract: "Voice and dialog fixtures MUST use `message` or `text` fields for operator replies; base64 `audio` responses are optional advanced path requiring OpenRouter STT."
  - Strength: Faster Phase 2/3 implementation; lower OpenRouter dependency for hub-side turns.
  - Tradeoff: Less faithful to original course audio loop.
  - Confidence: HIGH — agent code has explicit text fallback branch.
  - Blind spot: Other agents may need different response shapes per route.
- **Decision**: FIXED — text-field fixtures mandated; audio optional advanced path

- **Severity**: ⚠️ WARNING
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots
- **Location**: Phase 1 automated 1.2
- **Detail**: Phase 1 deletes all `apps/*` and `packages/*`. Until Phase 2 creates `packages/hub-mock`, `turbo run lint` operates on an empty workspace. Criterion 1.2 says "exits 0 (or succeeds with no apps yet)" — ambiguous whether vacuous pass is acceptable or masks misconfiguration.
- **Fix**: Clarify 1.2: "exits 0 with no tasks (empty workspace) OR add minimal `packages/hub-mock/package.json` stub in Phase 1 pointing to Phase 2." Prefer merging hub-mock scaffold into end of Phase 1 or start of Phase 2 with explicit note.
  - Strength: Removes ambiguity for implementer.
  - Tradeoff: None significant.
  - Confidence: HIGH.
  - Blind spot: None.
- **Decision**: FIXED — criterion 1.2 clarified for empty workspace

### F6 — Pre-commit prerequisites undocumented for Windows solo dev

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Blind Spots
- **Location**: Phase 1 — pre-commit (`plan.md:90-96`)
- **Detail**: Phase 1 requires `pre-commit run --all-files` but plan prerequisites list Docker and Python 3.12+ only in brief, not Phase 1. Pre-commit needs Python + `pip install pre-commit` on Windows. Feasible but unstated.
- **Fix**: Add to Phase 1 Overview or plan Prerequisites: "Python 3.12+, `pip install pre-commit`, Git for Windows hooks enabled."
- **Decision**: FIXED — added to Implementation Approach Prerequisites

### F7 — Root `package.json` format script stays TS-only after JS removal

- **Severity**: 💡 OBSERVATION
- **Impact**: 🏃 LOW — quick decision; fix is obvious and narrowly scoped
- **Dimension**: Lean Execution
- **Location**: Phase 1 — root workspace (`plan.md:76-80`)
- **Detail**: After deleting Next.js apps, root `package.json:8` still runs `prettier --write "**/*.{ts,tsx,md}"` — won't format Python. Minor drift; not blocking.
- **Fix**: Phase 1 optionally extend format script to `*.py` or drop format task until needed.
- **Decision**: FIXED — Phase 1 contract updates format script for `*.py`
