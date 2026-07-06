"""
Document-to-JSON ETL — unstructured trade notes to structured JSON and virtual filesystem.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
NOTES_DIR = os.getenv("NOTES_DIR", "data/natan_notes")
DEMO_DATA_PATH = os.getenv("DEMO_DATA_PATH", "data/food4cities.json")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

SYSTEM = """\
Jestes asystentem analizujacym notatki handlowe. Odpowiadasz WYLACZNIE czystym JSONem.
Format: {"miasta": {...}, "osoby": {...}, "towary": {...}}
"""


def normalize(text: str) -> str:
    table = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return text.translate(table).replace(" ", "_").lower()


def normalize_for_llm(text: str) -> str:
    table = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")
    return text.translate(table).lower()


def aidevs_post(action_payload: dict | list) -> dict:
    response = requests.post(
        f"{AIDEVS_API_URL}/verify",
        json={"apikey": AIDEVS_API_KEY, "task": "filesystem", "answer": action_payload},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def openrouter_chat(system: str, user: str) -> str:
    response = requests.post(
        f"{OPENROUTER_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "temperature": 0,
            "max_tokens": 4096,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()


def load_local_notes(notes_dir: str) -> dict[str, str]:
    print(f"Loading notes from {notes_dir}...")
    notes: dict[str, str] = {}
    root = Path(notes_dir)
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix in (".txt", ".md", ".json"):
            notes[path.name] = path.read_text(encoding="utf-8")
    print(f"  Loaded {len(notes)} file(s).")
    return notes


def demo_parse_notes(notes: dict[str, str]) -> dict:
    """Deterministic parse using bundled city inventory + transaction edges."""
    miasta_raw = json.loads(Path(DEMO_DATA_PATH).read_text(encoding="utf-8"))
    miasta = {city.title(): goods for city, goods in miasta_raw.items()}

    towary: dict[str, list[str]] = {}
    transakcje = notes.get("transakcje.txt", "")
    for line in transakcje.strip().splitlines():
        parts = [part.strip() for part in line.split("->")]
        if len(parts) != 3:
            continue
        city_from, product, city_to = parts
        product_key = normalize(product)
        cities = towary.setdefault(product_key, [])
        for city in (city_from, city_to):
            city_title = city.strip().title()
            if city_title not in cities:
                cities.append(city_title)

    osoby = {
        "Natan Rams": "Domatowo",
        "Iga Kapecka": "Opalino",
        "Damian Kroll": "Puck",
        "Lena Konkel": "Karlinkowo",
    }

    return {"miasta": miasta, "osoby": osoby, "towary": towary}


def parse_notes(notes: dict[str, str]) -> dict:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        print("[DEMO] Parsing notes with bundled rules...")
        return demo_parse_notes(notes)

    text = "\n\n---\n\n".join(f"=== {name} ===\n{body}" for name, body in notes.items())
    print("Parsing via OpenRouter...")
    raw = openrouter_chat(SYSTEM, f"Notatki:\n\n{normalize_for_llm(text)}")
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    data = json.loads(raw)
    print("  OK.")
    return data


def build_operations(data: dict) -> list[dict]:
    ops = [{"action": "createDirectory", "path": path} for path in ["/miasta", "/osoby", "/towary"]]

    for miasto, towary in data["miasta"].items():
        ops.append(
            {
                "action": "createFile",
                "path": f"/miasta/{normalize(miasto)}",
                "content": json.dumps(towary, ensure_ascii=False, indent=2),
            }
        )

    for osoba, miasto in data["osoby"].items():
        ops.append(
            {
                "action": "createFile",
                "path": f"/osoby/{normalize(osoba)}",
                "content": f"[{miasto}](/miasta/{normalize(miasto)})",
            }
        )

    for towar, miasta in data["towary"].items():
        ops.append(
            {
                "action": "createFile",
                "path": f"/towary/{normalize(towar)}",
                "content": "\n".join(f"[{m}](/miasta/{normalize(m)})" for m in miasta),
            }
        )

    return ops


def main() -> None:
    print("\n=== HELP ===")
    print(json.dumps(aidevs_post({"action": "help"}), indent=2, ensure_ascii=False))

    notes = load_local_notes(NOTES_DIR)
    data = parse_notes(notes)
    print("\n=== PARSED JSON ===")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    ops = build_operations(data)
    print(f"\n=== OPERATIONS ({len(ops)}) ===")
    for op in ops:
        print(f"  {op['action']:12s}  {op['path']}")

    print("\n=== RESET ===")
    print(aidevs_post({"action": "reset"}))

    print("\n=== BATCH SEND ===")
    print(aidevs_post(ops))

    print("\n=== LISTING ===")
    for path in ["/miasta", "/osoby", "/towary"]:
        print(f"  {path}:", aidevs_post({"action": "listFiles", "path": path}))

    print("\n=== DONE ===")
    result = aidevs_post({"action": "done"})
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if "FLG" in json.dumps(result, ensure_ascii=False):
        print("\nSuccess! ETL pipeline complete.")
        sys.exit(0)

    print("\nNo flag in done response.")
    sys.exit(1)


if __name__ == "__main__":
    main()
