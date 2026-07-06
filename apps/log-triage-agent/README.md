# Industrial Log Triage Agent

Function-calling agent that searches failure logs, builds a condensed summary under a token budget, and iterates on hub feedback.

## Competency

- **Function calling**: `search_logs`, `count_log_tokens`, `submit_logs`
- **Subagent pattern**: log search tool scans in-memory fixture file
- **Iterative verification**: hub feedback drives additional searches until flag
- **Token budget enforcement**: conservative 1 token ≈ 4 chars, max 1450

## Architecture

```
┌─────────────────────────────┐
│      MAIN AGENT (LLM)       │  OpenRouter (full mode)
│  orchestrates tool calls    │
└──────┬──────────┬───────────┘
       │          │
 search_logs  submit_logs ──► hub-mock /verify (task: failure)
       │
 fixtures/sample.log
```

**Demo mode** (`DEMO_MODE=1`): runs tool pipeline deterministically — no OpenRouter required.

## Sample log

`fixtures/sample.log` — fictional industrial events (ECCS8, WTRPMP, FIRMWARE). No course keys or URLs.

## Quick start

**Local (no Docker):**

```powershell
# Terminal 1
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8092"   # use free port if 8080 is busy
python src/server.py

# Terminal 2
cd apps/log-triage-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8092"
$env:DEMO_MODE = "1"
python src/triage_agent.py
```

**Docker** (when Docker Desktop available):

```powershell
cd apps/log-triage-agent
Copy-Item .env.example .env
docker compose up --build --abort-on-container-exit
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIDEVS_API_URL` | `http://hub-mock:8080` | Hub mock |
| `LOG_FILE` | `fixtures/sample.log` | Input log path |
| `MAX_TOKENS_BUDGET` | `1450` | Submission limit |
| `OPENROUTER_API_KEY` | — | Required for full LLM agent |
| `DEMO_MODE` | `1` | Tool-only demo |

Entry point: `src/triage_agent.py` (not `agent.py`).

---

# Agent Triażu Logów Przemysłowych

Agent z function calling do przeszukiwania logów awarii, budowy skondensowanego raportu i weryfikacji w hubie.

## Kompetencje

- Narzędzia: `search_logs`, `count_log_tokens`, `submit_logs`
- Pętla iteracyjna: feedback huba → dodatkowe wyszukiwania → ponowne wysłanie
- Limit tokenów: max 1450

## Przykładowy log

`fixtures/sample.log` — fikcyjne zdarzenia (bez kluczy kursu).

## Uruchomienie

Patrz sekcja Quick start powyżej. Tryb demo działa bez OpenRouter.

Punkt wejścia: `src/triage_agent.py`.
