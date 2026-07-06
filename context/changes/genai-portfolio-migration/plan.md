# GenAI Portfolio Migration Implementation Plan

## Overview

Migrate 10 curated AIDevs Python agent projects from `D:\CVGOSI\AIDevs\Zad_*` into the `genai-portfolio` Turborepo at `apps/<kebab-case>/`, producing a public, secret-free portfolio with Docker Compose per agent, bilingual READMEs (EN/PL), shared hub mock replacing `hub.ag3nts.org`, and CI-enforced publication hygiene.

## Current State Analysis

**Target repo (`cv_repo`):** Turborepo shell with `apps/web`, `apps/docs` (Next.js placeholders), `packages/ui`, `packages/eslint-config`, `packages/typescript-config`. No Python code, no Docker, no `.github/workflows/`. Root `.gitignore` covers Node/env but lacks `.venv/`, `*.log`, `audio_logs/`, `__pycache__/`. Turbo pipeline is Next.js-centric (`.next/**` outputs).

**Source projects:** 10 flat Python folders under `D:\CVGOSI\AIDevs\`. Each has a canonical `*FLG.py` flagship, 3–14 iteration scripts, missing `requirements.txt` (except Zad_3), live secrets in `.env`, and high-risk logs (Zad_17: 724 key occurrences).

**Key constraints from PRD/shape-notes:** 10 agents must-have; Docker Compose per project; no course API keys in git; agents retain behavioral demos via mocks; 6-week solo timeline.

### Key Discoveries:

- `apps/<kebab-case>/` aligns with `workspaces: ["apps/*"]` — preferred over flat root folders (`research.md`, `bootstrap-verification/verification.md`)
- Zad_22 flagship: `phonecall_agent7FLG.py` (~530 LOC), hardcoded `BARBAKAN` at lines 431/444/461, CLI batch job (no inbound ports)
- Removing `apps/web` + `apps/docs` orphans all `@repo/*` packages — delete `packages/ui`, `packages/eslint-config`, `packages/typescript-config` together
- Universal scrub list documented in `research.md` — never migrate `.env`, `*.log`, `audio_logs/`, iteration scripts

## Desired End State

1. `apps/` contains 10 agent folders, each with canonical Python entry, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`, bilingual README (EN + PL sections).
2. `packages/hub-mock/` provides HTTP stub for `POST /verify` with per-agent fixture responses.
3. Root `README.md` maps all 10 agents to GenAI competencies in EN and PL.
4. `.github/workflows/` runs gitleaks, `docker compose config` validation, and lint on PR/push.
5. Pre-commit hook blocks commits containing secret patterns.
6. Verification: clone repo → configure `.env` from `.env.example` → `docker compose up` in any agent folder → agent completes demo flow against hub-mock without course keys.

## What We're NOT Doing

- Publishing entire `D:\CVGOSI\AIDevs` directory or unscored projects (Zad_16, Zad_20, hybrid-rag, etc.)
- Flask→FastAPI migration for logistics-chat-api (README documents future path only)
- Production multi-user hosting, auth, or SLA
- Migrating iteration scripts (`agent1.py` … `agentN.py`) — canonical flagship only
- Automating API key rotation (documented manual checklist only)
- Building a Next.js landing page (JS placeholders removed, not replaced)

## Implementation Approach

**Prerequisites:** Python 3.12+, `pip install pre-commit`, Git for Windows (hooks enabled), Docker Desktop, access to `D:\CVGOSI\AIDevs\Zad_*` source folders, OpenRouter account for live voice demo.

**Phase ordering:** Foundation and security first → shared mock infrastructure → flagship voice agent establishes migration template → remaining 9 agents in research easy→hard order → final publication verification.

**Per-agent migration pattern (Phases 3–12):** Copy canonical flagship only → scrub secrets and hub URLs → externalize hardcoded passwords to `.env.example` → add `requirements.txt` → wire `AIDEVS_API_URL` to hub-mock → add Docker → write bilingual README → add hub-mock fixture → verify with CI.

**Mock strategy:** Shared `packages/hub-mock` HTTP server mimics hub endpoints: `/verify`, `/api/packages`, `/api/shell` (extensible route registry). Each agent ships fixture files under the matching route. OpenRouter calls remain env-configured (user supplies key) unless agent can demo with recorded fixtures alone.

## Critical Implementation Details

**Turbo workspace cleanup:** Deleting `apps/web` and `apps/docs` requires regenerating `package-lock.json` via `npm install` at root — stale lockfile entries will break CI otherwise.

**Zad_3 nested git:** Source `endpoint/.git` must not be copied — migrate code files only to prevent history leak.

**Voice agent runtime:** No microphone/speaker or ffmpeg required — audio is MP3 bytes over HTTP. Docker image can use `python:3.13-slim` with outbound HTTPS only.

---

## Phase 1: Monorepo Foundation & CI

### Overview

Remove Next.js placeholder stack, extend `.gitignore` for Python artifacts, retarget Turbo for multi-language workspace, and establish pre-commit + GitHub Actions secret scanning before any agent code lands.

### Changes Required:

#### 1. Remove JS placeholder apps and orphaned packages

**File**: `apps/web/`, `apps/docs/`, `packages/ui/`, `packages/eslint-config/`, `packages/typescript-config/`

**Intent**: Eliminate Turborepo starter noise so repo presents as Python agent portfolio from first commit.

**Contract**: Delete directories entirely; no imports of `@repo/*` remain anywhere in repo.

#### 2. Root workspace and Turbo config

**File**: `package.json`, `turbo.json`, `package-lock.json`

**Intent**: Keep `workspaces: ["apps/*", "packages/*"]` but retarget Turbo tasks for Python/Docker agents instead of Next.js builds.

**Contract**: `turbo.json` `build.outputs` no longer references `.next/**`; `build`, `lint`, `check-types`, `dev` tasks invoke per-app scripts via thin `package.json` shims. Run `npm install` after deletions to regenerate lockfile. Update root `format` script to include `*.py` (or remove if unused).

#### 3. Python publication gitignore

**File**: `.gitignore`

**Intent**: Prevent accidental commit of Python runtime artifacts across all 10 agents.

**Contract**: Add entries for `.venv/`, `__pycache__/`, `*.pyc`, `*.log`, `audio_logs/`, `*.mp3`, `.mypy_cache/`, `.ruff_cache/`.

#### 4. Pre-commit secret hook

**File**: `.pre-commit-config.yaml` (new)

**Intent**: Block commits containing API key patterns before they reach git history.

**Contract**: Hook runs gitleaks or equivalent secret scanner on staged files; documented in root README contributor section.

#### 5. GitHub Actions CI workflow

**File**: `.github/workflows/ci.yml` (new)

**Intent**: Automated defense in depth — secret scan, Docker Compose config validation, lint — on push and PR.

**Contract**: Workflow jobs: (1) gitleaks/trufflehog full-repo scan, (2) `docker compose config` for each `apps/*/docker-compose.yml` that exists (skip gracefully if none yet), (3) `turbo run lint` when lint scripts exist.

#### 6. Root README stub

**File**: `README.md`

**Intent**: Remove stale Turborepo/`@repo/*` references immediately so Phase 1 manual gate (`rg "@repo/"` empty) is passable.

**Contract**: Replace starter README with minimal portfolio stub: project name, one-line description, "agents migrating — see `apps/`" note, link to pre-commit setup. Full EN/PL competency map deferred to Phase 13.

### Success Criteria:

#### Automated Verification:

- `npm install` completes without workspace resolution errors
- `turbo run lint` exits 0 with no tasks (empty workspace acceptable until Phase 2 `hub-mock` lands)
- Pre-commit install succeeds: `pre-commit run --all-files` passes on clean repo
- CI workflow YAML validates (no syntax errors)

#### Manual Verification:

- No `apps/web`, `apps/docs`, or `@repo/ui` references remain (`rg "@repo/"` returns empty)
- `.gitignore` covers Python patterns listed above

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: Shared Hub Mock Infrastructure

### Overview

Create `packages/hub-mock` — a lightweight HTTP stub replacing `hub.ag3nts.org/verify` — with a fixture contract that all 10 agents will consume.

### Changes Required:

#### 1. Hub mock server package

**File**: `packages/hub-mock/` (new directory)

**Intent**: Provide a single mock backend so agents run without course infrastructure while preserving multi-turn dialog behavior.

**Contract**: HTTP server exposes multiple hub routes used by portfolio agents:
- `POST /verify` — body `{apikey, task, answer}` where `answer` is `{action: "start"}` or `{audio: "<base64>"}` (voice-ops, windpower, savethem, etc.)
- `POST /api/packages` — body `{apikey, action, packageid, ...}` (logistics-chat-api)
- `POST /api/shell` — body per firmware agent contract (secure-command-agent)

Responses loaded from per-route fixture files under `fixtures/<route>/<agent-name>.json`. Route registry documented in `packages/hub-mock/README.md`. Configurable via env `HUB_MOCK_PORT` (default 8080). Includes `Dockerfile` and `docker-compose.yml` for standalone startup.

#### 2. Fixture contract and voice-ops seed fixture

**File**: `packages/hub-mock/fixtures/<agent-name>.json` (new)

**Intent**: Define reusable fixture schema and seed the voice-ops-agent fixture as reference implementation for subsequent agents.

**Contract**: Each fixture file documents a sequence of `{request_match, response}` pairs. Dialog fixtures (voice-ops, verify-based agents) MUST return operator text via `message` or `text` fields — this avoids OpenRouter STT. Base64 `audio` responses are optional advanced path requiring OpenRouter transcription. Voice-ops fixture covers 4-step dialog (start → greeting → password prompt → road query → monitoring disable → flag). Include `README.md` in `packages/hub-mock/` explaining fixture authoring for implementers.

#### 3. Thin Turbo shim

**File**: `packages/hub-mock/package.json`

**Intent**: Register hub-mock in npm workspace for Turbo orchestration.

**Contract**: Scripts: `"dev": "docker compose up"`, `"build": "docker compose build"`, `"lint": "echo ok"` (or Python linter if server is Python).

### Success Criteria:

#### Automated Verification:

- `docker compose -f packages/hub-mock/docker-compose.yml config` validates
- `curl -X POST http://localhost:8080/verify` with start payload returns expected JSON from voice-ops fixture
- `turbo run build --filter=hub-mock` succeeds

#### Manual Verification:

- Fixture README explains how to add fixtures for remaining 9 agents
- Mock server starts and responds to 3+ sequential turns without error

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 3: Voice Ops Agent (Flagship)

### Overview

Migrate Zad_22_phonecall as `apps/voice-ops-agent/` — the portfolio flagship demonstrating TTS/STT + multi-turn voice dialog. Establishes the per-agent migration template for Phases 4–12.

### Changes Required:

#### 1. Agent source migration

**File**: `apps/voice-ops-agent/src/voice_agent.py` (new, from `phonecall_agent7FLG.py`)

**Intent**: Ship canonical voice agent code scrubbed of course secrets and hardcoded passwords.

**Contract**: Copy logic from `D:\CVGOSI\AIDevs\Zad_22_phonecall\phonecall\phonecall_agent7FLG.py` only. Replace hardcoded `BARBAKAN` with `TASK_PASSWORD` env var. Remove any literal `hub.ag3nts.org` URLs — use `AIDEVS_API_URL` env defaulting to hub-mock. Do not copy iterations, `phonecall.py`, `.env`, `phonecall.log`, or `audio_logs/`.

#### 2. Dependencies and environment template

**File**: `apps/voice-ops-agent/requirements.txt`, `apps/voice-ops-agent/.env.example`

**Intent**: Reproducible install and documented configuration for recruiters.

**Contract**: `requirements.txt` pins: `requests`, `python-dotenv`, `edge-tts`, `gTTS`, `aiohttp`. `.env.example` contains placeholders for `AIDEVS_API_URL`, `AIDEVS_API_KEY`, `OPENROUTER_API_KEY`, `OPENROUTER_API_URL`, `TASK_PASSWORD` — no `Zofia2026!`, no live keys, no unused `OKOEDITOR_*` vars.

#### 3. Container startup

**File**: `apps/voice-ops-agent/Dockerfile`, `apps/voice-ops-agent/docker-compose.yml`, `apps/voice-ops-agent/.dockerignore`

**Intent**: FR-004/US-01 — recruiter runs agent via containerized startup.

**Contract**: `FROM python:3.13-slim`; no audio device mapping; outbound HTTPS only. Compose file starts hub-mock as dependency service and voice agent with `AIDEVS_API_URL=http://hub-mock:8080`. CMD runs voice agent once (CLI batch, not daemon).

#### 4. Bilingual README

**File**: `apps/voice-ops-agent/README.md`

**Intent**: 5-minute read covering problem → architecture → stack → run steps for EN and PL audiences.

**Contract**: Sections: `# Voice Operations Agent` / `# Agent Operacji Głosowych`, competency pitch, architecture diagram (text), TTS/STT cascade explanation, `docker compose up` instructions, env var table, evolution note (agent7 selected from 7 iterations).

#### 5. Turbo workspace registration

**File**: `apps/voice-ops-agent/package.json`

**Intent**: Enable root `turbo run dev|build|lint` for this agent.

**Contract**: `"name": "voice-ops-agent"`, scripts delegate to Docker/Python tooling.

#### 6. Hub mock fixture wiring

**File**: `packages/hub-mock/fixtures/voice-ops-agent.json`

**Intent**: Voice agent demo completes full dialog against mock without course backend.

**Contract**: Fixture responses include operator prompts triggering password flow and final `{FLG:...}` flag pattern matching agent's `extract_flag()` regex.

### Success Criteria:

#### Automated Verification:

- `docker compose -f apps/voice-ops-agent/docker-compose.yml config` validates
- Hub smoke: `docker compose up` with hub-mock only — agent reaches `start_session()` without course keys (OpenRouter may be unset)
- Full demo (manual): with valid `OPENROUTER_API_KEY` in `.env`, `docker compose up --abort-on-container-exit` exits 0 with flag detected
- `rg -i "sk-or-v1|30d39e8c|BARBAKAN|hub\.ag3nts\.org" apps/voice-ops-agent/` returns no matches in committed files
- `turbo run lint --filter=voice-ops-agent` passes
- CI gitleaks scan passes on repo with voice-ops-agent added

#### Manual Verification:

- README readable in under 5 minutes; both EN and PL sections present
- README documents that course keys are replaced by user-owned `OPENROUTER_API_KEY` + hub-mock (PRD US-01 alignment)
- Agent completes 4-step dialog flow with hub-mock and OpenRouter configured; TTS/STT cascade logs visible
- No `.env`, `*.log`, or `audio_logs/` committed

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 4: Prompt Optimization Loop

### Overview

Migrate Zad_6_categorize as `apps/prompt-optimization-loop/` — lowest-risk agent establishing the repeatable migration template post-flagship.

### Changes Required:

#### 1. Agent source

**File**: `apps/prompt-optimization-loop/src/optimizer.py` (from `categorize3.py`)

**Intent**: Demonstrate automated prompt test→feedback→fix loop competency.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_6_categorize\categorize\categorize3.py`. Include safe sample `categorize.csv` (10 rows). Exclude `logi!TuraTylko.txt`, iterations, `.env`.

#### 2. Packaging

**File**: `apps/prompt-optimization-loop/requirements.txt`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `package.json`, `README.md`

**Intent**: Match voice-ops-agent packaging pattern with bilingual README.

**Contract**: Same file set as Phase 3 template. README pitch: "Automated Prompt Optimization" / "Automatyczna optymalizacja promptów".

#### 3. Hub mock fixture

**File**: `packages/hub-mock/fixtures/prompt-optimization-loop.json`

**Intent**: Agent verification calls succeed against mock.

**Contract**: Fixture covers categorize task verification endpoint responses.

### Success Criteria:

#### Automated Verification:

- `docker compose -f apps/prompt-optimization-loop/docker-compose.yml up --abort-on-container-exit` exits 0
- Secret scan clean on `apps/prompt-optimization-loop/`
- `turbo run lint --filter=prompt-optimization-loop` passes

#### Manual Verification:

- README explains prompt optimization loop with sample CSV
- Bilingual EN/PL sections present

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 5: Log Triage Agent

### Overview

Migrate Zad_8_failure as `apps/log-triage-agent/` — function-calling log analysis competency.

### Changes Required:

#### 1. Agent source

**File**: `apps/log-triage-agent/src/triage_agent.py` (from `failure_agent3.py`)

**Intent**: Demonstrate iterative LLM log triage with function calling.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_8_failure\failure\failure_agent3.py`. Adapt content from source `README_1.md` into bilingual README (fix `agent.py` → actual entry name drift). Exclude `failure.log.txt`, `.env`, iterations.

#### 2. Sample log data

**File**: `apps/log-triage-agent/fixtures/sample.log` (new, sanitized)

**Intent**: Provide safe demo input replacing excluded course log file.

**Contract**: Fictional log lines only — no API keys, no course-specific URLs.

#### 3. Packaging and hub fixture

**File**: Standard agent file set + `packages/hub-mock/fixtures/log-triage-agent.json`

**Intent**: Complete migration following established template.

**Contract**: README pitch: "Industrial Log Triage Agent" / "Agent triażu logów przemysłowych".

### Success Criteria:

#### Automated Verification:

- Docker compose startup exits 0 against hub-mock
- Secret scan clean
- Lint passes

#### Manual Verification:

- Function-calling flow demonstrable with sample log fixture
- Bilingual README under 5-minute read

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 6: Logistics Chat API

### Overview

Migrate Zad_3_proxy as `apps/logistics-chat-api/` — HTTP server with function calling (Flask, v1 keeps existing framework).

### Changes Required:

#### 1. Agent source

**File**: `apps/logistics-chat-api/src/` (from `endpoint/server.py`, `llm_handler.py`, `package_api.py`, `session_manager.py`)

**Intent**: Demonstrate HTTP API + LLM function calling for logistics domain.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_3_proxy\endpoint/`. Use existing `requirements.txt` as base (Flask 2.3.3). **Do not copy** nested `.git/`, tracked `.env`, `sessions/*.json`, or notes file with plaintext keys. Migrate code files only.

#### 2. HTTP server Docker exposure

**File**: `apps/logistics-chat-api/docker-compose.yml`

**Intent**: Recruiter can hit HTTP endpoint locally.

**Contract**: Expose port (e.g. 5000) for Flask server. Hub-mock or OpenRouter via env. README documents FastAPI upgrade path (non-goal for v1).

#### 3. Packaging and fixture

**File**: Standard set + `packages/hub-mock/fixtures/logistics-chat-api.json`

**Intent**: Complete migration; highest secret-tier source — extra scrub verification required.

**Contract**: README pitch: "Logistics Chat API" / "API czatu logistycznego".

### Success Criteria:

#### Automated Verification:

- `docker compose up` starts Flask server; health endpoint or sample POST returns 200
- `rg` finds no plaintext keys from Zad_3 notes file patterns
- CI secret scan passes

#### Manual Verification:

- README documents Flask architecture and FastAPI future path
- Session state does not persist secrets to git

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 7: Document-to-JSON ETL

### Overview

Migrate Zad_19_filesystem as `apps/document-to-json-etl/` — unstructured document → structured JSON competency.

### Changes Required:

#### 1. Agent source

**File**: `apps/document-to-json-etl/src/etl_agent.py` (from `filesystem1FLG.py`)

**Intent**: Demonstrate document ETL pipeline for GenAI roles.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_19_filesystem\filesystem\filesystem1FLG.py`. Include safe sample documents if present in source; exclude `.env`, iterations.

#### 2. Packaging and fixture

**File**: Standard agent file set + hub fixture

**Intent**: Lowest complexity optional agent — validates template scales to simpler agents.

**Contract**: README pitch: "Document-to-JSON ETL" / "ETL dokumentów do JSON".

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0
- Secret scan clean

#### Manual Verification:

- ETL output demonstrable with sample input files
- Bilingual README complete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 8: Shell Exploration Agent

### Overview

Migrate Zad_23_shellaccess as `apps/shell-exploration-agent/` — guarded shell tool use competency.

### Changes Required:

#### 1. Agent source

**File**: `apps/shell-exploration-agent/src/shell_agent.py` (from `agent4FLG.py`)

**Intent**: Demonstrate LLM-driven shell exploration with guardrails/blacklist.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_23_shellaccess\shellaccess\agent4FLG.py`. Preserve guardrail logic. README warns about local-only execution risks.

#### 2. Packaging and fixture

**File**: Standard set + hub fixture

**Intent**: Complete migration with security narrative for interview context.

**Contract**: README pitch: "Shell Exploration Agent" / "Agent eksploracji powłoki" with guardrails section prominent in both languages.

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0 in sandboxed container
- Secret scan clean

#### Manual Verification:

- README guardrails/warning sections present EN + PL
- Blacklist blocks dangerous commands in demo

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 9: Secure Command Agent

### Overview

Migrate Zad_12_firmware as `apps/secure-command-agent/` — command guardrails and blacklist competency.

### Changes Required:

#### 1. Agent source

**File**: `apps/secure-command-agent/src/command_agent.py` (from `firmware3FLG.py`)

**Intent**: Demonstrate secure command execution with guardrails for interview narrative.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_12_firmware\firmware\firmware3FLG.py`. Exclude `firmware_agent.log`, `.env`, iterations.

#### 2. Packaging and fixture

**File**: Standard set + hub fixture

**Intent**: Complete migration following template.

**Contract**: README pitch: "Secure Command Agent" / "Agent bezpiecznych poleceń".

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0
- No content from excluded log files in repo

#### Manual Verification:

- Guardrail behavior demonstrable
- Bilingual README complete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 10: Multi-Phase Planning Agent

### Overview

Migrate Zad_15_savethem as `apps/multi-phase-planning-agent/` — multi-step orchestration competency (distinct from async planning).

### Changes Required:

#### 1. Agent source

**File**: `apps/multi-phase-planning-agent/src/planning_agent.py` (from `savethem_agent_v4FLG.py`)

**Intent**: Demonstrate multi-phase LLM orchestration for complex tasks.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_15_savethem\savethem\savethem_agent_v4FLG.py`. Exclude `.env`, iterations.

#### 2. Packaging and fixture

**File**: Standard set + hub fixture

**Intent**: Complete migration.

**Contract**: README pitch: "Multi-Phase Planning Agent" / "Agent planowania wieloetapowego". Differentiate from async-planning-agent (Phase 11).

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0
- Secret scan clean

#### Manual Verification:

- Multi-phase flow visible in logs/output
- Bilingual README explains orchestration vs async planning difference

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 11: Async Planning Agent

### Overview

Migrate Zad_17_windpower as `apps/async-planning-agent/` — asyncio multi-step planning competency. Source had critical log exposure (724 keys) — extra verification required.

### Changes Required:

#### 1. Agent source

**File**: `apps/async-planning-agent/src/async_agent.py` (from `windpower_agent10FLG.py`)

**Intent**: Demonstrate async/await planning patterns with concurrent requests.

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_17_windpower\windpower\windpower_agent10FLG.py`. **Never copy** `windpower_agent.log`. Exclude 11 iteration scripts, `.venv/`, `.env`.

#### 2. Async dependencies

**File**: `apps/async-planning-agent/requirements.txt`

**Intent**: Document asyncio HTTP dependencies.

**Contract**: Include `requests`, `python-dotenv`, `aiohttp` at minimum.

#### 3. Packaging and fixture

**File**: Standard set + hub fixture

**Intent**: Complete migration with enhanced post-migration secret scan.

**Contract**: README pitch: "Async Planning Agent" / "Agent planowania asynchronicznego".

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0
- `rg "30d39e8c" apps/async-planning-agent/` returns empty (spot-check known leaked key prefix)
- Full CI gitleaks pass

#### Manual Verification:

- Async concurrency visible in agent logs
- Bilingual README complete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 12: Multimodal Intel Pipeline

### Overview

Migrate Zad_21_radiomonitoring as `apps/multimodal-intel-pipeline/` — speech recognition + LLM analysis competency. Final agent migration.

### Changes Required:

#### 1. Agent source

**File**: `apps/multimodal-intel-pipeline/src/radio_agent.py` (from `radio_monitoring_agent7.py`)

**Intent**: Demonstrate multimodal pipeline (audio → transcription → intelligence extraction).

**Contract**: Source: `D:\CVGOSI\AIDevs\Zad_21_radiomonitoring\radiomonitoring\radio_monitoring_agent7.py`. Exclude audio logs, `.env`, iterations. Heavy deps isolated in Docker.

#### 2. Packaging and fixture

**File**: Standard set + hub fixture

**Intent**: Complete 10-agent migration set.

**Contract**: README pitch: "Multimodal Intel Pipeline" / "Pipeline inteligencji multimodalnej".

### Success Criteria:

#### Automated Verification:

- Docker compose run exits 0
- Secret scan clean

#### Manual Verification:

- Multimodal flow (audio processing → LLM) demonstrable
- Bilingual README complete

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 13: Root README & Pre-Publication Verification

### Overview

Write root competency map (EN + PL), run final publication checklist, document manual key rotation steps, and verify all 10 agents listed.

### Changes Required:

#### 1. Root bilingual README

**File**: `README.md`

**Intent**: Single entry point for recruiters — map all 10 agents to GenAI competencies with one-line pitches.

**Contract**: Table with columns: Agent folder | Competency (EN) | Kompetencja (PL) | One-line pitch. Links to each `apps/<agent>/README.md`. Quick start: clone → Docker → pick agent. Contributor section references pre-commit setup.

#### 2. Pre-publication checklist

**File**: `docs/PRE-PUBLISH-CHECKLIST.md` (new)

**Intent**: Human-verifiable gate before `git push` to public GitHub.

**Contract**: Checklist items from shape-notes: no `.env` committed, gitleaks clean, rotate OpenRouter keys, rotate AIDEVS keys, all 10 READMEs complete, all docker compose configs valid, hub-mock fixtures present for all agents.

#### 3. CI coverage verification

**File**: `.github/workflows/ci.yml`

**Intent**: CI validates all 10 agent docker-compose files and runs full secret scan.

**Contract**: Matrix or loop over `apps/*/docker-compose.yml`. Job fails on any secret detection.

### Success Criteria:

#### Automated Verification:

- `turbo run lint` passes across all workspace packages
- CI workflow green on full repo
- `docker compose config` succeeds for all 10 agents
- `rg -l "\.env$" --glob "!.env.example"` finds no committed `.env` files

#### Manual Verification:

- Root README readable in under 3 minutes; competency table complete for all 10 agents
- Pre-publish checklist executed; key rotation documented as done (manual confirmation)
- Clone-fresh test: pick any 3 agents, run `docker compose up` successfully

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Testing Strategy

### Unit Tests:

- Hub-mock: test `/verify` endpoint returns fixture responses for start and turn payloads
- Per-agent: optional pytest for secret-free config loading and env var validation
- Key edge case: agent behavior when `TASK_PASSWORD` / API keys missing — clear error message, no silent hang

### Integration Tests:

- Each agent: `docker compose up --abort-on-container-exit` completes with exit code 0 against hub-mock
- Logistics-chat-api: HTTP POST to Flask endpoint returns expected response shape
- CI: gitleaks full-repo scan on every PR

### Manual Testing Steps:

1. Fresh clone → `cp apps/voice-ops-agent/.env.example apps/voice-ops-agent/.env` → fill OpenRouter key → `docker compose up` in voice-ops-agent
2. Repeat spot-check for logistics-chat-api (HTTP) and shell-exploration-agent (guardrails)
3. Run pre-publish checklist end-to-end before first public push
4. Verify bilingual README rendering on GitHub (EN/PL headings, tables)

## Performance Considerations

- Agents are CLI batch jobs or single-user demos — no production load targets
- Docker images use slim Python base; no GPU required except potentially multimodal-intel-pipeline Whisper (CPU fallback acceptable for portfolio)
- Turbo caching irrelevant for Docker builds — disable or use `cache: false` for agent build tasks

## Migration Notes

- **Source path:** Copy from `D:\CVGOSI\AIDevs\Zad_*` locally — never commit source path or keys
- **Key rotation:** After all migrations, manually rotate `OPENROUTER_API_KEY` and `AIDEVS_API_KEY` at provider dashboards — keys appear in 20+ source files
- **Rollback:** Each phase is independent — revert single agent folder if migration fails without affecting others
- **Git history:** If any secret accidentally committed, use `git filter-repo` before public push (document in checklist, hope pre-commit prevents need)

## References

- Related research: `context/changes/genai-portfolio-migration/research.md`
- PRD: `context/foundation/prd.md`
- Shape notes: `context/foundation/shape-notes.md`
- Bootstrap verification: `context/changes/bootstrap-verification/verification.md`
- Voice flagship source: `D:\CVGOSI\AIDevs\Zad_22_phonecall\phonecall\phonecall_agent7FLG.py`

## Progress

> Convention: `- [ ]` pending, `- [x]` done. Append ` — <commit sha>` when a step lands. Do not rename step titles.

### Phase 1: Monorepo Foundation & CI

#### Automated

- [x] 1.1 `npm install` completes without workspace resolution errors — b757a78
- [x] 1.2 `turbo run lint` exits 0 — b757a78
- [x] 1.3 Pre-commit install succeeds: `pre-commit run --all-files` passes on clean repo — b757a78
- [x] 1.4 CI workflow YAML validates (no syntax errors) — b757a78

#### Manual

- [x] 1.5 No `apps/web`, `apps/docs`, or `@repo/ui` references remain — b757a78
- [x] 1.6 `.gitignore` covers Python patterns — b757a78

### Phase 2: Shared Hub Mock Infrastructure

#### Automated

- [x] 2.1 `docker compose -f packages/hub-mock/docker-compose.yml config` validates — 780f0bf
- [x] 2.2 `curl` POST to `/verify` with start payload returns expected JSON — 780f0bf
- [x] 2.3 `turbo run build --filter=hub-mock` succeeds — 780f0bf

#### Manual

- [x] 2.4 Fixture README explains fixture authoring for remaining agents — 780f0bf
- [x] 2.5 Mock server responds to 3+ sequential turns without error — 780f0bf

### Phase 3: Voice Ops Agent (Flagship)

#### Automated

- [x] 3.1 `docker compose -f apps/voice-ops-agent/docker-compose.yml config` validates — 256b3d7
- [x] 3.2 Hub smoke: docker compose reaches start_session without course keys — 256b3d7
- [x] 3.3 Secret grep clean on `apps/voice-ops-agent/` — 256b3d7
- [x] 3.4 `turbo run lint --filter=voice-ops-agent` passes — 256b3d7
- [x] 3.5 CI gitleaks scan passes with voice-ops-agent added — 256b3d7

#### Manual

- [x] 3.6 README readable under 5 minutes; EN and PL sections present — 256b3d7
- [x] 3.7 README documents OPENROUTER_API_KEY + hub-mock requirement — 256b3d7
- [x] 3.8 Full demo: 4-step dialog with OpenRouter configured; flag detected — 256b3d7
- [x] 3.9 No `.env`, `*.log`, or `audio_logs/` committed — 256b3d7

### Phase 4: Prompt Optimization Loop

#### Automated

- [x] 4.1 Docker compose run exits 0 — 77d0024
- [x] 4.2 Secret scan clean on `apps/prompt-optimization-loop/` — 77d0024
- [x] 4.3 Lint passes — 77d0024

#### Manual

- [x] 4.4 README explains prompt optimization loop with sample CSV — 77d0024
- [x] 4.5 Bilingual EN/PL sections present — 77d0024

### Phase 5: Log Triage Agent

#### Automated

- [x] 5.1 Docker compose startup exits 0 against hub-mock — d7684ce
- [x] 5.2 Secret scan clean — d7684ce
- [x] 5.3 Lint passes — d7684ce

#### Manual

- [x] 5.4 Function-calling flow demonstrable with sample log fixture — d7684ce
- [x] 5.5 Bilingual README under 5-minute read — d7684ce

### Phase 6: Logistics Chat API

#### Automated

- [x] 6.1 Docker compose starts Flask server; sample POST returns 200 — 447478c
- [x] 6.2 No plaintext keys from Zad_3 notes patterns — 447478c
- [x] 6.3 CI secret scan passes — 447478c

#### Manual

- [x] 6.4 README documents Flask architecture and FastAPI future path — 447478c
- [x] 6.5 Session state does not persist secrets to git — 447478c

### Phase 7: Document-to-JSON ETL

#### Automated

- [x] 7.1 Docker compose run exits 0
- [x] 7.2 Secret scan clean

#### Manual

- [x] 7.3 ETL output demonstrable with sample input files
- [x] 7.4 Bilingual README complete

### Phase 8: Shell Exploration Agent

#### Automated

- [ ] 8.1 Docker compose run exits 0 in sandboxed container
- [ ] 8.2 Secret scan clean

#### Manual

- [ ] 8.3 README guardrails/warning sections present EN + PL
- [ ] 8.4 Blacklist blocks dangerous commands in demo

### Phase 9: Secure Command Agent

#### Automated

- [ ] 9.1 Docker compose run exits 0
- [ ] 9.2 No content from excluded log files in repo

#### Manual

- [ ] 9.3 Guardrail behavior demonstrable
- [ ] 9.4 Bilingual README complete

### Phase 10: Multi-Phase Planning Agent

#### Automated

- [ ] 10.1 Docker compose run exits 0
- [ ] 10.2 Secret scan clean

#### Manual

- [ ] 10.3 Multi-phase flow visible in logs/output
- [ ] 10.4 Bilingual README explains orchestration vs async planning

### Phase 11: Async Planning Agent

#### Automated

- [ ] 11.1 Docker compose run exits 0
- [ ] 11.2 Known leaked key prefix absent from agent folder
- [ ] 11.3 Full CI gitleaks pass

#### Manual

- [ ] 11.4 Async concurrency visible in agent logs
- [ ] 11.5 Bilingual README complete

### Phase 12: Multimodal Intel Pipeline

#### Automated

- [ ] 12.1 Docker compose run exits 0
- [ ] 12.2 Secret scan clean

#### Manual

- [ ] 12.3 Multimodal flow demonstrable
- [ ] 12.4 Bilingual README complete

### Phase 13: Root README & Pre-Publication Verification

#### Automated

- [ ] 13.1 `turbo run lint` passes across all workspace packages
- [ ] 13.2 CI workflow green on full repo
- [ ] 13.3 `docker compose config` succeeds for all 10 agents
- [ ] 13.4 No committed `.env` files (except `.env.example`)

#### Manual

- [ ] 13.5 Root README competency table complete for all 10 agents
- [ ] 13.6 Pre-publish checklist executed; key rotation documented
- [ ] 13.7 Clone-fresh test: 3 agents run successfully
