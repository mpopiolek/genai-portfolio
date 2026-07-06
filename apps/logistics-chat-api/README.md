# Logistics Chat API

Flask HTTP API for logistics operators — LLM function calling with package hub integration.

## Competency

- **HTTP API design**: `POST /chat`, `GET /health`, session persistence
- **Function calling**: `check_package`, `redirect_package` via OpenRouter (full mode)
- **Domain guardrails**: reactor shipments routed to `PWR6132PL` in tool code, not prompt-only
- **Hub integration**: `POST /api/packages` against hub-mock

## Architecture (Flask v1)

```
Operator ──POST /chat──► Flask server.py
                              │
                    LLMHandler (OpenRouter)
                              │
                    PackageAPI ──POST──► hub-mock /api/packages
                              │
                    SessionManager ──► sessions/ (gitignored)
```

**Future path (v2):** migrate to FastAPI for async handlers, OpenAPI docs, and WebSocket support — out of scope for this portfolio slice.

## Quick start

**Local (no Docker):**

```powershell
# Terminal 1 — hub-mock
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8092"
python src/server.py

# Terminal 2 — Flask API
cd apps/logistics-chat-api
$env:AIDEVS_API_URL = "http://127.0.0.1:8092/api/packages"
$env:DEMO_MODE = "1"
$env:FLASK_PORT = "5000"
python src/server.py
```

**Test:**

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/chat -Method POST -ContentType "application/json" `
  -Body '{"sessionID":"demo-1","msg":"Sprawdź status paczki PKG12345678"}'
```

**Docker** (when Docker Desktop available):

```powershell
cd apps/logistics-chat-api
Copy-Item .env.example .env
docker compose up --build
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_PORT` | `5000` | HTTP port |
| `AIDEVS_API_URL` | hub-mock packages URL | Package hub endpoint |
| `OPENROUTER_API_KEY` | — | Required for full LLM mode |
| `DEMO_MODE` | `1` | Keyword-based demo without OpenRouter |
| `SESSIONS_DIR` | `sessions` | Runtime session files (not committed) |

## Security note

Session JSON files under `sessions/` are **gitignored** — never commit operator chat history or API keys.

---

# API Czatu Logistycznego

Flask API dla operatorów logistyki — function calling LLM + integracja z hubem paczek.

## Kompetencje

- API HTTP (`/chat`, `/health`), sesje na dysku
- Narzędzia: sprawdzenie i przekierowanie paczki
- Reguła reaktora: `PWR6132PL` w kodzie narzędzia
- Hub-mock zamiast infrastruktury kursu

## Architektura

Patrz diagram powyżej. **v2:** planowana migracja na FastAPI (async, OpenAPI) — poza zakresem v1.

## Uruchomienie

Patrz Quick start. Tryb demo (`DEMO_MODE=1`) działa bez OpenRouter.

## Sesje

Katalog `sessions/` jest w `.gitignore` — stan rozmów nie trafia do git.
