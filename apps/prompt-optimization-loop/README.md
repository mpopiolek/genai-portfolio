# Prompt Optimization Loop

Automated prompt test → feedback → fix loop for cargo item classification (DNG vs NEU).

## Competency

- **Prompt engineering agent**: OpenRouter function-calling iterates on prompt templates
- **Closed-loop verification**: each cycle resets hub counter, classifies 10 CSV items, reads hub feedback
- **Constraint-aware prompts**: token budget, reactor-parts-always-NEU rule, DNG/NEU-only replies
- **Demo without course keys**: hub-mock + bundled `data/categorize.csv`

## Architecture

```
┌──────────────────────────┐   POST /verify    ┌──────────────┐
│ prompt-optimization-loop │ ◄───────────────► │   hub-mock   │
│  optimizer.py            │  prompt per item  │ categorize   │
└────────────┬─────────────┘                   └──────────────┘
             │ optional
             ▼
┌──────────────────────────┐
│      OpenRouter        │  prompt-engineer LLM (full mode)
└──────────────────────────┘
```

**Loop:** reset → load CSV → classify 10 items → analyse errors → refine prompt → repeat until `{FLG:...}`.

## Sample CSV

`data/categorize.csv` — 10 safe demo rows (reactor cassettes, tools, weapons). No course log files.

## Quick start

```powershell
cd apps/prompt-optimization-loop
Copy-Item .env.example .env
docker compose up --build --abort-on-container-exit
```

**Demo mode** (`DEMO_MODE=1`, default): single cycle with built-in prompt — no OpenRouter needed.

**Full mode**: set `DEMO_MODE=0` and `OPENROUTER_API_KEY` for iterative prompt engineering.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIDEVS_API_URL` | `http://hub-mock:8080` | Hub mock URL |
| `AIDEVS_API_KEY` | — | Placeholder key |
| `OPENROUTER_API_KEY` | — | Required for full agent loop |
| `CATEGORIZE_CSV_PATH` | `data/categorize.csv` | Local item list |
| `DEMO_MODE` | `1` | Single-cycle demo when set |

---

# Pętla Optymalizacji Promptów

Automatyczna pętla test → feedback → poprawka promptu dla klasyfikacji ładunków (DNG vs NEU).

## Kompetencje

- Agent inżynierii promptów z function-calling (OpenRouter)
- Weryfikacja w pętli: reset licznika, 10 pozycji CSV, odpowiedź huba
- Prompty z ograniczeniami: limit tokenów, części reaktora = NEU
- Demo bez kluczy kursu: hub-mock + lokalny CSV

## Przykładowy CSV

`data/categorize.csv` — 10 wierszy demo (bez plików logów kursu).

## Uruchomienie

```powershell
cd apps/prompt-optimization-loop
Copy-Item .env.example .env
docker compose up --build --abort-on-container-exit
```

Tryb demo (`DEMO_MODE=1`) — jeden cykl bez OpenRouter. Pełny tryb wymaga `OPENROUTER_API_KEY` i `DEMO_MODE=0`.

## Zmienne środowiskowe

Patrz tabela powyżej — opisy po angielsku; nazwy zmiennych uniwersalne.
