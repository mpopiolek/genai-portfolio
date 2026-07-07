# Async Planning Agent

Asyncio turbine scheduling agent — **concurrent hub requests** with polling-based result collection.

## Competency

- **asyncio + aiohttp**: parallel `get` and `unlockCodeGenerator` via `asyncio.gather`
- **Async queue pattern**: hub queues work; agent polls `getResult`
- **Hybrid analysis**: deterministic Python scheduling + optional LLM cross-check
- **Session timeout awareness**: tracks elapsed time vs `sessionTimeout`

## vs Multi-Phase Planning Agent (Phase 10)

| Async Planning (this app) | Multi-Phase Planning |
|---------------------------|----------------------|
| Concurrent HTTP with `asyncio.gather` | Sequential phases |
| Poll `getResult` for async hub work | Synchronous tool API calls |
| Single event loop | Blocking `requests` |

## Architecture

```
asyncio.gather(get weather, get plant, get turbine)
    -> poll getResult x3
    -> Python storm/production analysis
asyncio.gather(unlockCodeGenerator x N)
    -> poll getResult x N
    -> config -> done
```

## Quick start

```powershell
cd packages/hub-mock; $env:HUB_MOCK_PORT = "8098"; python src/server.py
# second terminal:
cd apps/async-planning-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8098"
$env:DEMO_MODE = "1"
python src/async_agent.py
```

Expected logs: `[ASYNC] 3 hub get() calls dispatched in parallel` and flag `{FLG:async-demo}`.

## Security note

Source project had `windpower_agent.log` with leaked keys — **never committed**. This migration uses stream logging only.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIDEVS_API_URL` | hub-mock | Base URL (auto-appends `/verify`) |
| `DEMO_MODE` | `1` | Demo without OpenRouter LLM cross-check |

---

# Agent Planowania Asynchronicznego

Agent harmonogramu turbiny z **równoległymi** zapytaniami asyncio do huba.

## Różnica vs Multi-Phase Planning

Ten agent używa `asyncio.gather` i pollingu `getResult`. Multi-Phase Planning (Faza 10) wykonuje fazy sekwencyjnie.

## Uruchomienie

Patrz Quick start. W logach szukaj `[ASYNC]` — oznacza równoległe wywołania. Flaga: `{FLG:async-demo}`.
