"""
Automated Prompt Engineering Agent for Item Classification
Downloads items from local CSV, classifies via hub-mock, and optionally
uses OpenRouter to iterate on prompt templates until a flag is received.
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from io import StringIO
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
CATEGORIZE_CSV_PATH = os.getenv("CATEGORIZE_CSV_PATH", "data/categorize.csv")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")
ENGINEER_MODEL = os.getenv("ENGINEER_MODEL", "anthropic/claude-sonnet-4-5")

HUB_VERIFY_URL = f"{AIDEVS_API_URL}/verify"

DEMO_PROMPT = (
    "Weapons and fire hazards are DNG. Reactor parts always NEU. "
    "Reply only DNG or NEU. {code} {description}"
)


def openrouter_chat(
    messages: list, tools: list | None = None, tool_choice: str = "auto", max_tokens: int = 2048
) -> dict:
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    body: dict = {"model": ENGINEER_MODEL, "messages": messages, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice

    resp = requests.post(f"{OPENROUTER_API_URL}/chat/completions", headers=headers, json=body, timeout=60)
    resp.raise_for_status()
    return resp.json()


def load_csv() -> list[dict]:
    path = Path(CATEGORIZE_CSV_PATH)
    print(f"  [CSV] Loading from {path}")
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(StringIO(text))
    items = [row for row in reader]
    print(f"  [CSV] Loaded {len(items)} items")
    return items


def send_to_hub(prompt: str) -> dict:
    payload = {"apikey": AIDEVS_API_KEY, "task": "categorize", "answer": {"prompt": prompt}}
    resp = requests.post(HUB_VERIFY_URL, json=payload, timeout=30)
    try:
        return resp.json()
    except Exception:
        return {"raw": resp.text, "status_code": resp.status_code}


def reset_counter() -> dict:
    print("  [HUB] Sending reset …")
    result = send_to_hub("reset")
    print(f"  [HUB] Reset response: {result}")
    return result


def run_classification_cycle(prompt_template: str) -> dict:
    print("\n" + "=" * 60)
    print("[CYCLE] Starting full cycle")
    print(f"[CYCLE] Prompt template: {prompt_template!r}")
    print("=" * 60)

    reset_counter()
    time.sleep(0.5)

    items = load_csv()
    csv_headers = list(items[0].keys()) if items else []
    sample_row = dict(items[0]) if items else {}

    results = []
    flag = None

    for item in items:
        item_code = item.get("code", item.get("Code", ""))
        item_desc = item.get("description", item.get("Description", ""))

        if "{code}" in prompt_template or "{description}" in prompt_template:
            final_prompt = prompt_template.format(code=item_code, description=item_desc)
        else:
            final_prompt = f"{prompt_template} Code:{item_code} {item_desc}"

        print(f"\n  [ITEM {item_code}] Prompt ({len(final_prompt)} chars)")
        response = send_to_hub(final_prompt)
        print(f"  [ITEM {item_code}] Response: {response}")

        message = response.get("message", "") or response.get("note", "") or str(response)
        if "FLG:" in str(response):
            flag = str(response)

        results.append(
            {
                "code": item_code,
                "description": item_desc,
                "prompt": final_prompt,
                "response": response,
                "message": message,
            }
        )
        time.sleep(0.2)

    return {
        "prompt_template": prompt_template,
        "csv_headers": csv_headers,
        "sample_row": sample_row,
        "results": results,
        "flag": flag,
    }


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "run_classification_cycle",
        "description": (
            "Runs a full classification cycle: resets hub counter, loads 10 CSV items, "
            "sends each with the prompt template to hub/verify, returns all responses."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "prompt_template": {
                    "type": "string",
                    "description": (
                        "Classification prompt template with {code} and {description} placeholders. "
                        "Under 100 tokens including item data. Reply DNG or NEU only. "
                        "Reactor parts are ALWAYS NEU."
                    ),
                }
            },
            "required": ["prompt_template"],
        },
    },
}

SYSTEM_PROMPT = """\
You are an expert prompt engineer crafting a classification prompt for cargo items (DNG vs NEU).
Constraints: under 100 tokens total, reply DNG or NEU only, reactor parts always NEU.
Use {code} and {description} placeholders from csv_headers. Iterate until you receive a flag.
"""


def run_agent() -> dict | None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Design a prompt template and run the full cycle until you get the flag.",
        },
    ]

    print("\n" + "=" * 60)
    print("[AGENT] Starting prompt-engineering agent")
    print("=" * 60 + "\n")

    max_iterations = 20
    for iteration in range(1, max_iterations + 1):
        print(f"\n[AGENT] ── Turn {iteration} ──────────────────────────────")

        raw = openrouter_chat(messages, tools=[TOOL_SCHEMA], tool_choice="auto")
        choice = raw["choices"][0]
        msg = choice["message"]
        finish_reason = choice["finish_reason"]
        messages.append(msg)

        if msg.get("content"):
            print(f"[AGENT] {msg['content']}")

        tool_calls = msg.get("tool_calls") or []
        if finish_reason != "tool_calls" or not tool_calls:
            print("[AGENT] Agent finished without calling tool.")
            break

        for tool_call in tool_calls:
            if tool_call["function"]["name"] != "run_classification_cycle":
                continue

            args = json.loads(tool_call["function"]["arguments"])
            prompt_template = args["prompt_template"]
            print(f"[AGENT] Tool call with template: {prompt_template!r}")
            cycle_result = run_classification_cycle(prompt_template)

            if cycle_result["flag"]:
                print(f"\n[AGENT] FLAG OBTAINED: {cycle_result['flag']}\n")
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(cycle_result, ensure_ascii=False),
                    }
                )
                return cycle_result

            summary_lines = [
                f"CSV headers: {cycle_result['csv_headers']}",
                f"Sample row:  {cycle_result['sample_row']}",
                "",
                "Results:",
            ]
            for r in cycle_result["results"]:
                summary_lines.append(
                    f"  code={r['code']} | desc={r['description']!r} | hub={r['message']!r}"
                )
            summary_lines.append("\nNo flag yet. Improve the prompt and retry.")
            tool_result_str = "\n".join(summary_lines)

            messages.append(
                {"role": "tool", "tool_call_id": tool_call["id"], "content": tool_result_str}
            )

    print("[AGENT] Max iterations reached without flag.")
    return None


def run_demo() -> dict:
    """Single-cycle demo against hub-mock — no OpenRouter required."""
    print("[DEMO] Running single classification cycle with built-in prompt")
    return run_classification_cycle(DEMO_PROMPT)


def main() -> None:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
        result = run_demo()
    else:
        result = run_agent()

    if result and result.get("flag"):
        print(f"\nSuccess! Flag: {result['flag']}")
        sys.exit(0)

    print("\nNo flag obtained.")
    sys.exit(1)


if __name__ == "__main__":
    main()
