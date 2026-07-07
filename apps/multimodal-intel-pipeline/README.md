# Multimodal Intel Pipeline

Radio monitoring pipeline — **transcription + attachment processing + intelligence extraction** → hub report.

## Competency

- **Multimodal ingest**: hub transcriptions, JSON/text attachments, audio (Whisper via OpenRouter in full mode)
- **Intel extraction**: LLM JSON extraction (or deterministic demo parser)
- **Report transmit**: structured answer to `/verify` task `radiomonitoring`

## Pipeline flow

```
listen (hub) -> transcription -> intel extraction
            -> attachment -> decode -> JSON/audio branch -> intel extraction
transmit(city, area, warehouses, phone) -> flag
```

## Quick start

```powershell
cd packages/hub-mock; $env:HUB_MOCK_PORT = "8099"; python src/server.py
# second terminal:
cd apps/multimodal-intel-pipeline
$env:AIDEVS_API_URL = "http://127.0.0.1:8099"
$env:DEMO_MODE = "1"
python src/radio_agent.py
```

Expected: `[PIPELINE]` logs for transcription + JSON attachment, flag `{FLG:multimodal-demo}`.

## Demo vs full mode

| Demo (`DEMO_MODE=1`) | Full mode |
|----------------------|-----------|
| Regex intel extraction | OpenRouter LLM extraction |
| Mock audio transcription | GPT-4o audio preview via OpenRouter |
| Stream logging only | Same (no audio log dirs in repo) |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `1` | Demo without OpenRouter |
| `INTEL_TRIGGER` | `alpha sector` | Keyword gating analysis |

---

# Pipeline Inteligencji Multimodalnej

Pipeline monitorowania sygnałów radiowych — transkrypcja, załączniki, ekstrakcja danych, raport do huba.

## Przepływ

Nasłuch → transkrypcja/załącznik → ekstrakcja intel → transmit → flaga.

## Uruchomienie

Patrz Quick start. Szukaj logów `[PIPELINE]`. Flaga: `{FLG:multimodal-demo}`.
