# Multi-Phase Planning Agent

Sequential **multi-phase orchestration**: gather world state via tool APIs, then plan and verify a grid route.

## Competency

- **Phase 1 — World gathering**: toolsearch discovery + maps/vehicles/books API calls + LLM synthesis
- **Phase 2 — Route planning**: separate LLM pass produces move array, retry loop on verify failures
- **Synchronous phases**: each phase completes before the next starts

## vs Async Planning Agent (Phase 11)

| Multi-Phase (this app) | Async Planning (Phase 11) |
|------------------------|---------------------------|
| Sequential phases | Concurrent asyncio requests |
| Tool discovery then planning | Parallel data fetching |
| Blocking HTTP calls | `asyncio.gather` patterns |

## Architecture

```
Phase 1: toolsearch -> /api/maps|wehicles|books -> world model
Phase 2: LLM route planner -> POST /verify (task: savethem, answer: [...])
```

## Quick start

```powershell
cd packages/hub-mock; $env:HUB_MOCK_PORT = "8097"; python src/server.py
# second terminal:
cd apps/multi-phase-planning-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8097"
$env:HUB_BASE = "http://127.0.0.1:8097"
$env:DEMO_MODE = "1"
python src/planning_agent.py
```

Expected log phases 1-2 visible, flag `{FLG:planning-demo}`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HUB_BASE` | `AIDEVS_API_URL` | Base for relative tool URLs |
| `DEMO_MODE` | `1` | Scripted demo without OpenRouter |

---

# Agent Planowania Wieloetapowego

Sekwencyjna orchestracja w fazach: zbieranie informacji o świecie, potem planowanie trasy.

## Różnica vs Async Planning Agent

Ten agent wykonuje **fazy synchronicznie** (najpierw świat, potem trasa). Async Planning Agent (Faza 11) używa `asyncio` do równoległych zapytań.

## Uruchomienie

Patrz Quick start. Oczekiwany wynik: widoczne fazy 1-2 w logach + flaga `{FLG:planning-demo}`.
