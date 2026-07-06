# Shell Exploration Agent

LLM-driven server exploration via remote shell commands — with client-side guardrails and hub-mock sandbox.

## Competency

- **Tool use**: agent proposes shell commands, hub returns output
- **Guardrails**: regex blacklist blocks destructive/network commands before hub call
- **Iterative exploration**: multi-step recon until structured JSON answer
- **Sandboxed demo**: hub-mock simulates `/data` filesystem — no real shell on host

## Guardrails (client-side blacklist)

Blocked patterns include: `rm -rf`, `sudo`, `curl`, `wget`, `mkfs`, fork bombs, writes to `/etc`, etc.

Demo mode runs `demonstrate_guardrails()` first — verifies `rm -rf /` is **rejected** before any allowed commands run.

## Architecture

```
shell_agent.py  ──POST /verify (task: shellaccess)──►  hub-mock
     │                                                    │
     └── is_command_allowed(cmd)  ◄── guardrail gate      └── mock /data output
```

## Quick start

```powershell
# Terminal 1
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8093"
python src/server.py

# Terminal 2
cd apps/shell-exploration-agent
$env:AIDEVS_API_URL = "http://127.0.0.1:8093"
$env:DEMO_MODE = "1"
python src/shell_agent.py
```

Expected: guardrail test passes, 4 demo commands, flag `{FLG:shell-demo}`.

## Warning — local execution risks

Full LLM mode (`DEMO_MODE=0` + OpenRouter) sends **real command strings** to the hub endpoint. Never point this agent at production systems. Use hub-mock only for portfolio demos. Do not disable guardrails.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIDEVS_API_URL` | hub-mock | Shell verify endpoint base |
| `DEMO_MODE` | `1` | Scripted demo without OpenRouter |
| `OPENROUTER_API_KEY` | — | Required for full LLM agent |

---

# Agent Eksploracji Powłoki

Agent LLM eksplorujący serwer przez komendy zdalne — z guardrails po stronie klienta.

## Guardrails

Blacklist regex blokuje m.in. `rm -rf`, `sudo`, `curl`, `wget` **zanim** komenda trafi do huba. Demo wypisuje test blokady `rm -rf /`.

## Ostrzeżenie

Tryb pełny wysyła prawdziwe stringi komend do endpointu. Używaj wyłącznie z hub-mock w demo portfolio. Nie wyłączaj guardrails.

## Uruchomienie

Patrz Quick start powyżej. Oczekiwany wynik: test guardrails + flaga `{FLG:shell-demo}`.
