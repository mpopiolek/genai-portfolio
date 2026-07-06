# Voice Operations Agent

Flagship portfolio agent demonstrating multi-turn voice dialog with a TTS/STT cascade against a mock AIDevs hub.

## Competency

- **Voice AI pipeline**: text → speech (TTS) → hub dialog → speech transcription (STT)
- **Multi-turn orchestration**: password gates, road-status analysis, conditional follow-up
- **Resilient fallbacks**: edge-tts → OpenRouter TTS → gTTS; hub text replies avoid STT when possible
- **Containerized demo**: Docker Compose with shared `hub-mock` — no course infrastructure required

## Architecture

```
┌─────────────────┐     POST /verify      ┌──────────────┐
│ voice-ops-agent │ ◄──────────────────► │   hub-mock   │
│  TTS / STT / LLM│   audio + text JSON   │   fixtures   │
└────────┬────────┘                       └──────────────┘
         │ HTTPS (optional)
         ▼
┌─────────────────┐
│   OpenRouter    │  TTS fallback, STT, road-analysis LLM
└─────────────────┘
```

**Dialog flow (4 steps):**

1. `start` session → operator greeting
2. Agent introduction → password prompt → `TASK_PASSWORD`
3. Road status query (RD224/RD472/RD820) → LLM extracts passable roads
4. Disable monitoring request → flag `{FLG:...}`

## Stack

| Layer | Technology |
|-------|------------|
| Runtime | Python 3.13 |
| TTS | edge-tts (primary), OpenRouter, gTTS |
| STT | OpenRouter multimodal / Whisper (when hub returns audio) |
| Hub | `packages/hub-mock` — text `message` fixtures |
| Container | Docker Compose |

## Quick start

```sh
cp .env.example .env
# Set TASK_PASSWORD and optionally OPENROUTER_API_KEY

docker compose up --build --abort-on-container-exit
```

**PowerShell:**

```powershell
Copy-Item .env.example .env
docker compose up --build --abort-on-container-exit
```

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AIDEVS_API_URL` | yes | Hub URL (default in compose: `http://hub-mock:8080`) |
| `AIDEVS_API_KEY` | yes | Placeholder key for hub mock |
| `TASK_PASSWORD` | yes | Dialog password (replaces hardcoded course value) |
| `OPENROUTER_API_KEY` | for full demo | User-owned key for TTS fallback, STT, road LLM |
| `OPENROUTER_API_URL` | no | Default `https://openrouter.ai/api/v1` |

> Course `AIDEVS_API_KEY` and hub URLs are **not** shipped. You supply your own `OPENROUTER_API_KEY` for live TTS/STT; hub-side turns use text fixtures and work without OpenRouter.

## Evolution note

Selected **agent7** (`phonecall_agent7FLG.py`) from seven iterations — best balance of TTS quality (edge-tts neural voice), STT cascade, and dialog robustness.

---

# Agent Operacji Głosowych

Flagowy agent portfolio — wieloetapowy dialog głosowy z kaskadą TTS/STT i mockiem huba AIDevs.

## Kompetencje

- **Pipeline głosowy**: tekst → mowa (TTS) → dialog z hubem → transkrypcja (STT)
- **Orkiestracja wieloetapowa**: hasła, analiza statusu dróg, warunkowe follow-upy
- **Fallbacki**: edge-tts → OpenRouter TTS → gTTS; odpowiedzi tekstowe huba omijają STT
- **Demo w kontenerze**: Docker Compose + `hub-mock` — bez infrastruktury kursu

## Architektura

Patrz diagram powyżej. Przepływ dialogu:

1. Start sesji → powitanie operatora
2. Przedstawienie → hasło (`TASK_PASSWORD`)
3. Zapytanie o drogi → LLM wybiera przejezdne odcinki
4. Wyłączenie monitoringu → flaga `{FLG:...}`

## Uruchomienie

```powershell
Copy-Item .env.example .env
# Ustaw TASK_PASSWORD i opcjonalnie OPENROUTER_API_KEY

docker compose up --build --abort-on-container-exit
```

## Zmienne środowiskowe

| Zmienna | Wymagana | Opis |
|---------|----------|------|
| `AIDEVS_API_URL` | tak | URL huba (w compose: `http://hub-mock:8080`) |
| `AIDEVS_API_KEY` | tak | Klucz placeholder dla mocka |
| `TASK_PASSWORD` | tak | Hasło dialogowe |
| `OPENROUTER_API_KEY` | pełne demo | Własny klucz OpenRouter (TTS/STT/LLM) |
| `OPENROUTER_API_URL` | nie | Domyślnie OpenRouter API v1 |

> Klucze kursowe **nie są** w repozytorium. Do pełnego demo podajesz własny `OPENROUTER_API_KEY`; tury huba działają na fixture tekstowych bez OpenRouter.

## Notatka ewolucyjna

Wybrano **agenta 7** spośród siedmiu iteracji — najlepszy kompromis jakości TTS (edge-tts neural) i odporności dialogu.
