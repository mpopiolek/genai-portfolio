# Secure Command Agent

Autonomous agent for a restricted Linux VM — with **pre-execution guardrails**, runtime `.gitignore` learning, and hub-mock sandbox.

## Competency

- **Hard-blocked paths**: `/etc`, `/root`, `/proc` rejected before VM call
- **Sensitive file patterns**: `.env`, `.secret`, `shadow`, etc.
- **Runtime blacklist**: learns paths from `.gitignore` after `ls`
- **Function-calling loop**: OpenRouter tools `shell_exec` + `send_answer`
- **Demo mode**: scripted firmware task without live LLM

## Guardrails

Commands are validated in `shell_exec()` **before** POST to `/api/shell`. Demo starts with guardrail tests blocking `/etc/passwd` and `.env` reads.

## Architecture

```
command_agent.py
  ├── shell_exec(cmd)  ──guardrail gate──►  POST /api/shell  ──►  hub-mock
  └── send_answer(code) ─────────────────►  POST /verify (firmware)
```

## Quick start

```powershell
# Terminal 1
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8096"
python src/server.py

# Terminal 2
cd apps/secure-command-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8096"
$env:SHELL_API_URL = "http://127.0.0.1:8096/api/shell"
$env:DEMO_MODE = "1"
python src/command_agent.py
```

Expected: guardrail tests pass, firmware demo completes, flag `{FLG:command-demo}`.

## Warning

Full LLM mode sends real command strings to the shell API. Use hub-mock only. Do not disable guardrails for portfolio demos.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SHELL_API_URL` | `{AIDEVS_API_URL}/api/shell` | Remote shell endpoint |
| `AIDEVS_API_URL` | hub-mock | Verify endpoint base |
| `DEMO_MODE` | `1` | Scripted demo without OpenRouter |

---

# Agent Bezpiecznych Poleceń

Agent autonomiczny na ograniczonej maszynie wirtualnej — z guardrails przed wykonaniem, uczeniem `.gitignore` i sandboxem hub-mock.

## Guardrails

Blokada ścieżek `/etc`, `/root`, `/proc` oraz wrażliwych plików (`.env`, `.secret`) **przed** wysłaniem do VM. Demo pokazuje testy blokady.

## Ostrzeżenie

Tryb pełny wysyła prawdziwe komendy do API powłoki. Używaj wyłącznie z hub-mock. Nie wyłączaj guardrails.

## Uruchomienie

Patrz Quick start. Oczekiwany wynik: testy guardrails + flaga `{FLG:command-demo}`.
