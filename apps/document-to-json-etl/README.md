# Document-to-JSON ETL

Unstructured trade notes → structured JSON → virtual filesystem operations via hub-mock.

## Competency

- **Document ETL**: parse `.txt` notes into `{miasta, osoby, towary}` schema
- **LLM extraction** (full mode) or **rule-based demo** (no OpenRouter)
- **Batch filesystem API**: create directories/files, list, done/flag

## Pipeline

```
data/natan_notes/*.txt  ──► parse (LLM or demo rules)
                                │
                           structured JSON
                                │
                           build_operations()
                                │
                           POST /verify (task: filesystem) ──► hub-mock
```

## Sample data

| Path | Description |
|------|-------------|
| `data/natan_notes/ogloszenia.txt` | City supply requests |
| `data/natan_notes/rozmowy.txt` | Trade conversation notes |
| `data/natan_notes/transakcje.txt` | City → product → city edges |
| `data/food4cities.json` | Reference inventory for demo parse |

## Quick start

**Local:**

```powershell
# Terminal 1
cd packages/hub-mock
$env:HUB_MOCK_PORT = "8093"   # restart hub-mock after updates; use free port
python src/server.py

# Terminal 2
cd apps/document-to-json-etl
$env:AIDEVS_API_URL = "http://127.0.0.1:8093"
$env:DEMO_MODE = "1"
python src/etl_agent.py
```

Expected: parsed JSON printed, operations batch sent, flag `{FLG:filesystem-demo}`.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTES_DIR` | `data/natan_notes` | Input documents |
| `DEMO_DATA_PATH` | `data/food4cities.json` | Demo city inventory |
| `DEMO_MODE` | `1` | Rule-based parse without OpenRouter |
| `AIDEVS_API_URL` | hub-mock | Filesystem verify endpoint |

---

# ETL Dokumentów do JSON

Notatki handlowe → JSON → operacje wirtualnego filesystemu.

## Kompetencje

- Ekstrakcja struktury z dokumentów tekstowych
- Tryb demo bez OpenRouter (reguły + `food4cities.json`)
- Integracja z hub-mock (`task: filesystem`)

## Dane przykładowe

Patrz `data/natan_notes/` i `data/food4cities.json` — fikcyjne dane, bez kluczy kursu.

## Uruchomienie

Patrz Quick start powyżej. Pełny tryb LLM wymaga `OPENROUTER_API_KEY` i `DEMO_MODE=0`.
