---
date: 2026-07-06T09:58:00+02:00
researcher: Cursor Agent
git_commit: HEAD
branch: master
repository: genai-portfolio
topic: "GenAI portfolio migration — cv_repo target + AIDevs source projects"
tags: [research, migration, aidevs, turborepo, python-agents, secrets]
status: complete
last_updated: 2026-07-06
last_updated_by: Cursor Agent
---

# Research: GenAI Portfolio Migration

**Date**: 2026-07-06T09:58:00+02:00  
**Researcher**: Cursor Agent  
**Git Commit**: HEAD (no commits yet)  
**Branch**: master  
**Repository**: genai-portfolio (`d:\CVGOSI\AIDevs\cv_repo`)

## Research Question

What is required to migrate 10 curated AIDevs agent projects from `D:\CVGOSI\AIDevs\Zad_*` into the bootstrapped `cv_repo` Turborepo monorepo as a public, secret-free GenAI portfolio?

## Summary

**Target repo (`cv_repo`)** is a fresh Turborepo shell (`genai-portfolio`) with foundation docs complete but **zero Python agents migrated**. Default `apps/web` and `apps/docs` (Next.js placeholders) should be replaced. Recommended landing zone: **`apps/<kebab-case-agent-name>/`** — aligns with npm workspaces (`apps/*`) and bootstrap verification hand-off.

**Source projects (10)** are flat Python folders under `D:\CVGOSI\AIDevs\`. Each has a canonical `*FLG.py` flagship file, missing `requirements.txt` (except Zad_3), no project README (except Zad_8's `README_1.md`), and live secrets in `.env` plus several log/notes files.

**Critical blockers before publish:**
1. Rotate shared `AIDEVS_API_KEY` (UUID `30d39e8c-…`) and `OPENROUTER_API_KEY` (`sk-or-v1-…`) — same values across all 10 projects
2. Scrub/delete high-risk files: Zad_3 notes txt (plaintext keys), Zad_17 log (724 key occurrences), Zad_22 log, Zad_6 run log
3. Remove `Zofia2026!` from 5 `.env.example` templates
4. Extend root `.gitignore` for Python artifacts (`.venv/`, `*.log`, `audio_logs/`)

**Recommended migration order** (easiest → hardest):
1. Zad_6_categorize → `apps/prompt-optimization-loop/`
2. Zad_8_failure → `apps/log-triage-agent/`
3. Zad_3_proxy → `apps/logistics-chat-api/`
4. Zad_19_filesystem → `apps/document-to-json-etl/` (optional batch; lowest complexity optional)
5. Zad_23_shellaccess → `apps/shell-exploration-agent/`
6. Zad_12_firmware → `apps/secure-command-agent/`
7. Zad_15_savethem → `apps/multi-phase-planning-agent/`
8. Zad_17_windpower → `apps/async-planning-agent/`
9. Zad_21_radiomonitoring → `apps/multimodal-intel-pipeline/`
10. Zad_22_phonecall → `apps/voice-ops-agent/` (flagship demo value, highest packaging effort)

**First implementation slice** (per prior conversation): start with **Zad_22_phonecall** as portfolio flagship OR **Zad_6** as lowest-risk template — plan should decide.

## Detailed Findings

### Target: cv_repo monorepo

- Root workspace: `package.json` with `workspaces: ["apps/*", "packages/*"]`, name `genai-portfolio`
- Turbo pipeline is Next.js-centric (`.next/**` outputs) — Python agents likely run via Docker outside Turbo or need new tasks
- Foundation docs present: `context/foundation/shape-notes.md`, `prd.md`, `tech-stack.md`
- Change `genai-portfolio-migration` exists with status `new` — no plan yet
- Root `.gitignore` covers Node/env but **missing** `.venv/`, `*.log`, `audio_logs/`, `__pycache__/`
- No `.github/workflows/`, no Docker files, no Python code in repo yet

**Layout tension resolved for planning:**

| Option | Pros | Cons |
|--------|------|------|
| `apps/<agent>/` | Matches workspaces + bootstrap hand-off | Paths differ from flat shape-notes sketch |
| Root-level folders | Matches US-01 literal paths | Requires workspace config change |

**Recommendation:** `apps/<agent-name>/` with thin optional `package.json` per app for Turbo scripts.

### TOP 5 source projects

#### Zad_22_phonecall → voice-ops-agent (HIGH complexity)

- Flagship: `phonecall/phonecall_agent7FLG.py` (~530 LOC) — TTS/STT + hub dialog
- Exclude: `.venv/`, `phonecall.log` (48× AIDEVS key), `audio_logs/`, iterations `phonecall_agent{1..6}.py`
- Secrets: live `.env`, hardcoded task password `BARBAKAN` in agent code, `Zofia2026!` in `.env.example`
- No `requirements.txt` — infer: `requests`, `python-dotenv`, `edge-tts`, `gTTS`, `aiohttp`

#### Zad_3_proxy → logistics-chat-api (MEDIUM complexity)

- Entry: `endpoint/server.py` + `llm_handler.py`, `package_api.py`, `session_manager.py`
- Has `endpoint/requirements.txt` (Flask 2.3.3, requests, python-dotenv)
- Exclude: nested `.git/`, `sessions/*.json`, notes file with **plaintext keys**
- Critical: `.env` is **git-tracked** in nested repo (`github.com/mpopiolek/endpoint`)

#### Zad_8_failure → log-triage-agent (MEDIUM complexity)

- Flagship: `failure/failure_agent3.py` (~395 LOC) — function-calling log triage
- Best README: `failure/README_1.md` (drift: references `agent.py` not `failure_agent3.py`)
- Exclude: `.env`, large `failure.log.txt`, iteration scripts
- No `requirements.txt`

#### Zad_6_categorize → prompt-optimization-loop (LOW–MEDIUM complexity)

- Flagship: `categorize/categorize3.py` (~325 LOC) — prompt engineer loop
- Exclude: `.env`, `logi!TuraTylko.txt` (key in URL), iterations
- Keep: `categorize.csv` (10-row sample, safe)
- Easiest TOP 5 to package

#### Zad_17_windpower → async-planning-agent (HIGH complexity)

- Flagship: `windpower/windpower_agent10FLG.py` (~553 LOC) — asyncio + requests
- Exclude: `.venv/`, `windpower_agent.log` (**724×** AIDEVS key), 11 iteration scripts
- No `requirements.txt` — infer: `requests`, `python-dotenv`, `aiohttp`

### Optional 5 source projects

| Source | Target folder | Flagship file | Complexity |
|--------|---------------|---------------|------------|
| Zad_15_savethem | multi-phase-planning-agent | `savethem_agent_v4FLG.py` | High |
| Zad_23_shellaccess | shell-exploration-agent | `agent4FLG.py` | Medium |
| Zad_12_firmware | secure-command-agent | `firmware3FLG.py` | Med–High |
| Zad_21_radiomonitoring | multimodal-intel-pipeline | `radio_monitoring_agent7.py` | High |
| Zad_19_filesystem | document-to-json-etl | `filesystem1FLG.py` | Low–Med |

No heavy duplication with TOP 5 — optional set fills tool orchestration, guarded shell, multimodal batch intel, and document ETL gaps.

### Security exposure (pre-publish)

| Tier | Projects |
|------|----------|
| Critical | Zad_3_proxy (plaintext keys in notes), Zad_17_windpower (724 keys in log) |
| High | Zad_22_phonecall, Zad_12_firmware, Zad_6_categorize |
| Medium | Zad_15_savethem, Zad_21_radiomonitoring |
| Lower | Zad_8_failure, Zad_19_filesystem, Zad_23_shellaccess |

**Universal scrub list (never migrate):**
- `Zad_3_proxy\- Podmiana destination odbywa się w.txt`
- `Zad_17_windpower\windpower\windpower_agent.log`
- `Zad_22_phonecall\phonecall\phonecall.log`
- `Zad_12_firmware\firmware\firmware_agent.log`
- `Zad_6_categorize\logi!TuraTylko.txt`
- All `.env` files (ship `.env.example` only)

## Code References

### Target repo
- `d:\CVGOSI\AIDevs\cv_repo\package.json` — workspace root, `genai-portfolio`
- `d:\CVGOSI\AIDevs\cv_repo\turbo.json` — Next.js-centric task pipeline
- `d:\CVGOSI\AIDevs\cv_repo\.gitignore` — missing Python patterns
- `d:\CVGOSI\AIDevs\cv_repo\context\foundation\prd.md` — 10 FRs, success criteria
- `d:\CVGOSI\AIDevs\cv_repo\context\foundation\shape-notes.md` — folder layout, checklist

### Source flagships (canonical migration entry points)
- `D:\CVGOSI\AIDevs\Zad_22_phonecall\phonecall\phonecall_agent7FLG.py`
- `D:\CVGOSI\AIDevs\Zad_3_proxy\endpoint\server.py`
- `D:\CVGOSI\AIDevs\Zad_8_failure\failure\failure_agent3.py`
- `D:\CVGOSI\AIDevs\Zad_6_categorize\categorize\categorize3.py`
- `D:\CVGOSI\AIDevs\Zad_17_windpower\windpower\windpower_agent10FLG.py`
- `D:\CVGOSI\AIDevs\Zad_15_savethem\savethem\savethem_agent_v4FLG.py`
- `D:\CVGOSI\AIDevs\Zad_23_shellaccess\shellaccess\agent4FLG.py`
- `D:\CVGOSI\AIDevs\Zad_12_firmware\firmware\firmware3FLG.py`
- `D:\CVGOSI\AIDevs\Zad_21_radiomonitoring\radiomonitoring\radio_monitoring_agent7.py`
- `D:\CVGOSI\AIDevs\Zad_19_filesystem\filesystem\filesystem1FLG.py`

### High-risk secret files (delete/redact before copy)
- `D:\CVGOSI\AIDevs\Zad_3_proxy\- Podmiana destination odbywa się w.txt:1-4`
- `D:\CVGOSI\AIDevs\Zad_17_windpower\windpower\windpower_agent.log`
- `D:\CVGOSI\AIDevs\Zad_22_phonecall\phonecall\phonecall.log`

## Architecture Insights

1. **Iteration cruft pattern:** Every AIDevs project has 3–14 `agentN.py` / `*FLG.py` variants — portfolio ships **one canonical file** per subproject plus README explaining evolution.
2. **Course coupling pattern:** All agents POST to `hub.ag3nts.org` with `AIDEVS_API_KEY` — public portfolio needs env-based URLs + mock mode or README note "requires own backend."
3. **Deps pattern:** Universal minimum is `requests` + `python-dotenv`; voice adds TTS libs; windpower adds `aiohttp`; proxy adds Flask.
4. **Monorepo fit:** Python agents are independent demos — no shared Python package needed initially; Turborepo provides root README, CI hook point, unified `.gitignore`.
5. **Per-agent Docker:** PRD requires `docker compose up` per subproject — not present in any source; must be created during implementation.

## Historical Context (from prior changes)

- `context/changes/bootstrap-verification/verification.md` — Turborepo scaffold completed 2026-07-06; explicitly recommends replacing `apps/web` and `apps/docs` with Python agent subfolders
- `context/foundation/shape-notes.md` — locked decisions: 10 projects, Zad_17 over Zad_20, Docker per project, 6-week timeline
- `context/foundation/tech-stack.md` — `turborepo` + `multi` language family; Python agents as isolated workspace packages

## Related Research

None — first research artifact for this change.

## Open Questions

1. **First slice:** Zad_22 (flagship value) vs Zad_6 (lowest risk template) — decide in `/10x-plan`
2. **Mock strategy:** Per-agent stub hub vs README-only demo vs local replay fixtures (`world_info.json`, `categorize.csv`, `natan_notes/`)
3. **Remove JS placeholders:** Delete `apps/web`, `apps/docs`, `packages/ui` immediately or after first Python app lands?
4. **Zad_3 nested git:** Migrate code only (no `endpoint/.git`) — confirm no history leak to portfolio repo
5. **Root README:** Single competency table — mine pitches from shape-notes FRs
