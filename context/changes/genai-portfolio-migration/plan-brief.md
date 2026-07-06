# GenAI Portfolio Migration — Plan Brief

> Full plan: `context/changes/genai-portfolio-migration/plan.md`
> Research: `context/changes/genai-portfolio-migration/research.md`

## What & Why

Migrate 10 curated AIDevs Python agent projects from scattered `Zad_*` folders into the `genai-portfolio` Turborepo as a public, secret-free portfolio for GenAI recruitment. Each subproject demonstrates one competency (voice, function calling, log triage, etc.) with Docker Compose startup, bilingual README, and no course API keys in git.

## Starting Point

`cv_repo` is a fresh Turborepo shell with Next.js placeholders (`apps/web`, `apps/docs`), no Python code, incomplete `.gitignore`, and no CI. Source projects live at `D:\CVGOSI\AIDevs\Zad_*` with live secrets in `.env`, logs, and hardcoded passwords. Research mapped all 10 flagships, exclusion lists, and security tiers.

## Desired End State

Public GitHub repo with 10 isolated agents under `apps/<kebab-case>/`, each runnable via `docker compose up` with own API keys and a shared hub mock. Root README maps projects to GenAI competencies in EN and PL. No committed secrets; pre-commit + CI enforce hygiene. Recruiter clones repo, picks an agent, reads README, runs locally without course infrastructure.

## Key Decisions Made

| Decision | Choice | Why (1 sentence) | Source |
| -------- | ------ | ---------------- | ------ |
| First implementation slice | `voice-ops-agent` (Zad_22) | Flagship demo value; directly satisfies US-01 | Plan |
| Hub replacement | Shared mock server + per-agent fixtures | Recruiter runs without course backend; consistent pattern | Plan |
| JS placeholders | Remove immediately in Phase 1 | Repo reads as Python portfolio from day one | Plan |
| README language | Bilingual EN + PL (root and per-agent) | International recruiters + owner's Polish context | Plan |
| CI scope | Secret scan + Docker validate + lint | Defense in depth after Zad_17/Zad_3 key exposure | Plan |
| Agent layout | `apps/<kebab-case>/` | Matches npm workspaces and bootstrap hand-off | Research |
| Migration order (after voice) | Research easy→hard sequence | Build confidence on simpler agents before async/audio heavy | Plan |
| Hardcoded secrets | Move to `.env.example`; pre-commit + CI | No secrets in git; automated regression catch | Plan |
| Source curation | Canonical flagship file only per agent | Smaller audit surface; README documents evolution | Research |

## Scope

**In scope:** Monorepo foundation (gitignore, CI, pre-commit); shared hub mock; migration of all 10 agents with Docker, requirements, bilingual README; root competency map; pre-publication secret verification.

**Out of scope:** Flask→FastAPI migration (document only); production hosting; Zad_20 and unscored projects; key rotation operation (document checklist, execute manually); landing page web app.

## Architecture / Approach

```
cv_repo/
├── apps/
│   ├── voice-ops-agent/          ← Phase 3 (Zad_22)
│   ├── prompt-optimization-loop/ ← Phase 4 (Zad_6)
│   └── … (8 more agents)
├── packages/
│   └── hub-mock/                 ← Phase 2: stub hub.ag3nts.org/verify
├── .github/workflows/            ← Phase 1: gitleaks + docker compose config
└── README.md                     ← Phase 13: EN/PL competency map
```

Each agent: canonical Python entry, `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `.env.example`, bilingual README. Agents point `AIDEVS_API_URL` at hub-mock container. OpenRouter calls remain real (user supplies key) or stubbed where feasible.

## Phases at a Glance

| Phase | What it delivers | Key risk |
| ----- | ---------------- | -------- |
| 1. Monorepo Foundation | Remove JS stack, Python gitignore, pre-commit, GHA | Orphaned lockfile refs after workspace cleanup |
| 2. Shared Hub Mock | `packages/hub-mock` stub + fixture contract | Mock responses may not match all 10 agent flows |
| 3. Voice Ops Agent | Zad_22 flagship migrated, Docker, EN/PL README | Audio/TTS deps; BARBAKAN scrub |
| 4. Prompt Optimization | Zad_6 — simplest template agent | Low |
| 5. Log Triage | Zad_8 — function calling pattern | README drift from source |
| 6. Logistics Chat API | Zad_3 — Flask HTTP server | Nested git history; tracked `.env` in source |
| 7. Document ETL | Zad_19 — optional batch, lowest complexity | Low |
| 8. Shell Exploration | Zad_23 — guardrails narrative | Public shell tools perception |
| 9. Secure Command | Zad_12 — guardrails/blacklist | Log file secrets in source |
| 10. Multi-Phase Planning | Zad_15 — orchestration | Medium complexity |
| 11. Async Planning | Zad_17 — asyncio heavy | Source log had 724 key occurrences |
| 12. Multimodal Intel | Zad_21 — Whisper pipeline | Heavy audio deps |
| 13. Root README & Publish | Competency map EN/PL, final scan, checklist | Human key rotation outside repo |

**Prerequisites:** Docker Desktop, Python 3.12+, access to `D:\CVGOSI\AIDevs\Zad_*` source folders, OpenRouter account for live demos.

**Estimated effort:** ~6 weeks after-hours, 13 phases, solo implementer.

## Open Risks & Assumptions

- Shared hub mock may need agent-specific response tuning beyond generic `/verify` stub.
- OpenRouter TTS/STT in voice-ops still requires user's API key — mock covers hub only, not OpenRouter.
- Key rotation (`AIDEVS_API_KEY`, `OPENROUTER_API_KEY`) is manual post-scrub — plan documents but cannot automate.
- Windows path `D:\CVGOSI\AIDevs\` assumed available during migration; not committed to repo.

## Success Criteria (Summary)

- All 10 agents under `apps/` start via `docker compose up` with hub-mock and documented env vars.
- `git grep` and CI secret scan find no live keys, `.env`, logs, or `audio_logs/`.
- Root README maps each agent to one GenAI competency in EN and PL within 5-minute read per agent README.
