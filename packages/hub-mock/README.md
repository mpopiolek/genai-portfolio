# Hub Mock

Lightweight HTTP stub replacing `hub.ag3nts.org` for local portfolio agent demos.

## Routes

| Route | Method | Used by | Body shape |
|-------|--------|---------|------------|
| `/verify` | POST | voice-ops, windpower, savethem, … | `{apikey, task, answer}` |
| `/api/packages` | POST | logistics-chat-api | `{apikey, action, packageid, …}` |
| `/api/shell` | POST | secure-command-agent | per firmware contract |

Configure port via `HUB_MOCK_PORT` (default `8080`).

## Quick start

```sh
docker compose up --build
curl http://localhost:8080/health
```

## Fixture contract

Fixtures live under `fixtures/<route>/<agent-name>.json`.

Each file defines:

```json
{
  "task": "phonecall",
  "agent": "voice-ops-agent",
  "turns": [
    {
      "request_match": { "answer": { "action": "start" } },
      "response": { "message": "Operator reply text" }
    }
  ]
}
```

### Rules

1. **Sequential turns** — the server advances through `turns` for each `task`, matching optional `request_match` patterns.
2. **Text-first dialog** — use `message` or `text` in responses for operator replies. This avoids OpenRouter STT on hub-side turns.
3. **Audio responses** — base64 `audio` in `response` is supported as an advanced path (requires agent-side transcription).
4. **Wildcards** — use `"*"` in `request_match` to match any value (e.g. `"audio": "*"` for all audio turns).
5. **Flags** — embed `{FLG:...}` in `message`/`text` fields; agents detect via regex.

### Adding fixtures for remaining agents

1. Identify the hub route (`/verify`, `/api/packages`, or `/api/shell`) from the agent source.
2. Create `fixtures/<route-dir>/<agent-name>.json` where `<route-dir>` is `verify`, `api-packages`, or `api-shell`.
3. Set `"task"` to the agent's AIDevs task name (must match the `task` field in POST body).
4. Define `turns` with `request_match` + `response` pairs mirroring the agent's dialog or API sequence.
5. Restart hub-mock and test with `curl` before wiring the agent's `AIDEVS_API_URL`.

### Example: start session (voice-ops)

**Bash / Git Bash / `curl.exe`:**

```sh
curl -s -X POST http://localhost:8080/verify \
  -H "Content-Type: application/json" \
  -d '{"apikey":"demo","task":"phonecall","answer":{"action":"start"}}'
```

**PowerShell** (use `Invoke-RestMethod` — `curl` is an alias with different syntax):

```powershell
Invoke-RestMethod -Uri http://localhost:8080/verify -Method POST `
  -ContentType "application/json" `
  -Body '{"apikey":"demo","task":"phonecall","answer":{"action":"start"}}'
```

Or call real curl explicitly:

```powershell
curl.exe -s -X POST http://localhost:8080/verify `
  -H "Content-Type: application/json" `
  -d "{\"apikey\":\"demo\",\"task\":\"phonecall\",\"answer\":{\"action\":\"start\"}}"
```

Expected first response:

```json
{"message": "Centrala monitoringu dróg, słucham."}
```

## Route registry (all agents)

| Agent | Route dir | Task | Fixture file |
|-------|-----------|------|--------------|
| voice-ops-agent | `verify` | `phonecall` | `fixtures/verify/voice-ops-agent.json` |
| prompt-optimization-loop | `verify` | `categorize` | `fixtures/verify/prompt-optimization-loop.json` |
| log-triage-agent | `verify` | `failure` | `fixtures/verify/log-triage-agent.json` |
| logistics-chat-api | `api-packages` | — | `fixtures/api-packages/logistics-chat-api.json` |
| document-to-json-etl | `verify` | `filesystem` | `fixtures/verify/document-to-json-etl.json` |
| shell-exploration-agent | `verify` | `shellaccess` | `fixtures/verify/shell-exploration-agent.json` |
| secure-command-agent | `api-shell` | — | `fixtures/api-shell/secure-command-agent.json` |
| multi-phase-planning-agent | `verify` + `api-*` | `savethem` | `fixtures/verify/multi-phase-planning-agent.json` (+ tool routes) |
| async-planning-agent | `verify` | `windpower` | `fixtures/verify/async-planning-agent.json` |
| multimodal-intel-pipeline | `verify` | `radiomonitoring` | `fixtures/verify/multimodal-intel-pipeline.json` |
