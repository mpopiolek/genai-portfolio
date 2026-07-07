# GenAI Portfolio

Public portfolio of **10 Python GenAI agents** — each runnable via Docker Compose with a shared [hub-mock](packages/hub-mock/) replacing live course APIs. Every agent ships with bilingual README (EN/PL), `DEMO_MODE=1` defaults, and portfolio-safe fixtures.

---

## Agent competency map

| Agent folder | Competency (EN) | Kompetencja (PL) | One-line pitch |
|--------------|-----------------|------------------|----------------|
| [voice-ops-agent](apps/voice-ops-agent/) | Voice dialog orchestration | Orchestracja dialogu głosowego | Multi-turn phone ops with TTS/STT cascade and hub verification |
| [prompt-optimization-loop](apps/prompt-optimization-loop/) | Prompt engineering loop | Pętla inżynierii promptów | Iterative classify → feedback → refine until hub accepts answer |
| [log-triage-agent](apps/log-triage-agent/) | Log analysis & triage | Analiza i triaż logów | Rule-assisted LLM failure diagnosis from industrial log streams |
| [logistics-chat-api](apps/logistics-chat-api/) | Tool-using chat API | API czatu z narzędziami | Flask chat agent with package hub tools and session memory |
| [document-to-json-etl](apps/document-to-json-etl/) | Document ETL pipeline | Pipeline ETL dokumentów | Batch filesystem ops → structured JSON extraction via LLM |
| [shell-exploration-agent](apps/shell-exploration-agent/) | Guarded shell exploration | Eksploracja powłoki z guardrails | LLM shell recon with client-side command blacklist |
| [secure-command-agent](apps/secure-command-agent/) | Secure command execution | Bezpieczne wykonywanie poleceń | Firmware VM agent with guardrails + runtime `.gitignore` learning |
| [multi-phase-planning-agent](apps/multi-phase-planning-agent/) | Multi-phase planning | Planowanie wieloetapowe | Sequential world-gather → route plan → verify (savethem) |
| [async-planning-agent](apps/async-planning-agent/) | Async concurrent planning | Planowanie asynchroniczne | `asyncio.gather` hub polling for windpower turbine scheduling |
| [multimodal-intel-pipeline](apps/multimodal-intel-pipeline/) | Multimodal intelligence | Inteligencja multimodalna | Radio listen → transcription/attachments → intel report |

---

## Quick start

### Prerequisites

- Docker + Docker Compose (recommended), **or** Python 3.11+ for local demo
- Node.js 18+ (monorepo tooling only)

### Clone and install tooling

```powershell
git clone <your-repo-url>
cd genai-portfolio
npm install
```

### Run any agent (Docker)

```powershell
cd apps/voice-ops-agent
copy .env.example .env
docker compose up --build
```

All agents default to `DEMO_MODE=1` — no live API keys required for portfolio demos.

### Run locally without Docker (Python + hub-mock)

```powershell
# Terminal 1 — shared hub mock
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8080"
python src/server.py

# Terminal 2 — pick an agent (example)
cd apps/shell-exploration-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8080"
$env:DEMO_MODE = "1"
python src/shell_agent.py
```

See each agent's README for env vars and expected demo output (flags like `{FLG:*-demo}`).

---

## Repository layout

```
apps/           # 10 portfolio agents (each: src/, Dockerfile, docker-compose.yml, README)
packages/
  hub-mock/     # Shared HTTP stub for /verify, /api/packages, /api/shell, tool routes
.github/        # CI: gitleaks + docker compose config + turbo lint
docs/           # Pre-publication checklist
```

---

## Contributing

This repo uses [pre-commit](https://pre-commit.com/) with [gitleaks](https://github.com/gitleaks/gitleaks) to block accidental secret commits.

```powershell
pip install pre-commit
pre-commit install
python -m pre_commit run --all-files
```

**Never commit `.env` files** — copy from `.env.example` only.

```powershell
npm run lint          # turbo lint across workspaces
```

Before your first public push, complete [docs/PRE-PUBLISH-CHECKLIST.md](docs/PRE-PUBLISH-CHECKLIST.md).

---

## Polski — skrót

Ten monorepo demonstruje 10 wzorców GenAI: dialog głosowy, optymalizacja promptów, triaż logów, API z narzędziami, ETL dokumentów, eksploracja powłoki, bezpieczne komendy, planowanie sekwencyjne i asynchroniczne oraz pipeline multimodalny.

Każdy agent ma README po polsku i angielsku w swoim folderze. Domyślny tryb demo (`DEMO_MODE=1`) działa z hub-mock bez kluczy kursowych.
