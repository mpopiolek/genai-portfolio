"""
Failure Log Analysis Agent — function-calling log triage with hub verification.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
LOG_FILE = os.getenv("LOG_FILE", "fixtures/sample.log")
MODEL = os.getenv("MODEL", "google/gemini-2.0-flash-001")
MAX_TOKENS_BUDGET = int(os.getenv("MAX_TOKENS_BUDGET", "1450"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "6"))
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

LOG_LINES: list[str] = []


def count_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def load_log_file(path: str) -> list[str]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Log file not found: {path}")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search log file by severity, keywords, or time range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "levels": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["CRIT", "ERRO", "WARN", "INFO"]},
                    },
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "time_from": {"type": "string"},
                    "time_to": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "count_log_tokens",
            "description": "Count tokens in condensed log text.",
            "parameters": {
                "type": "object",
                "properties": {"log_text": {"type": "string"}},
                "required": ["log_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "submit_logs",
            "description": "Submit condensed logs to verification hub.",
            "parameters": {
                "type": "object",
                "properties": {"log_text": {"type": "string"}},
                "required": ["log_text"],
            },
        },
    },
]


def _parse_log_timestamp(line: str) -> datetime | None:
    match = re.match(r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]", line)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None


def tool_search_logs(
    levels=None, keywords=None, time_from=None, time_to=None, limit=100
) -> dict:
    results: list[str] = []
    tf = datetime.strptime(time_from, "%Y-%m-%d %H:%M:%S") if time_from else None
    tt = datetime.strptime(time_to, "%Y-%m-%d %H:%M:%S") if time_to else None
    levels_set = {level.upper() for level in levels} if levels else None
    kw_lower = [kw.lower() for kw in keywords] if keywords else None

    for line in LOG_LINES:
        if levels_set:
            level_match = re.search(r"\[(CRIT|ERRO|WARN|INFO)\]", line)
            if not level_match or level_match.group(1) not in levels_set:
                continue
        if kw_lower:
            line_lower = line.lower()
            if not any(kw in line_lower for kw in kw_lower):
                continue
        if tf or tt:
            ts = _parse_log_timestamp(line)
            if ts is None:
                continue
            if tf and ts < tf:
                continue
            if tt and ts > tt:
                continue
        results.append(line)

    if limit:
        results = results[:limit]
    return {"count": len(results), "entries": results}


def tool_count_tokens(log_text: str) -> dict:
    tokens = count_tokens(log_text)
    return {"token_count": tokens, "within_limit": tokens <= MAX_TOKENS_BUDGET, "budget": MAX_TOKENS_BUDGET}


def tool_submit_logs(log_text: str) -> dict:
    tokens = count_tokens(log_text)
    if tokens > MAX_TOKENS_BUDGET:
        return {"error": f"Token count {tokens} exceeds limit {MAX_TOKENS_BUDGET}."}

    payload = {"apikey": AIDEVS_API_KEY, "task": "failure", "answer": {"logs": log_text}}
    try:
        resp = requests.post(f"{AIDEVS_API_URL}/verify", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        print(f"\n[HUB RESPONSE] {json.dumps(data, ensure_ascii=False, indent=2)}")
        return data
    except requests.RequestException as exc:
        return {"error": str(exc)}


def dispatch_tool(name: str, args: dict) -> dict:
    print(f"\n  [TOOL CALL] {name}({json.dumps(args, ensure_ascii=False)[:200]})")
    if name == "search_logs":
        result = tool_search_logs(**args)
        print(f"  [TOOL RESULT] found {result['count']} entries")
        return result
    if name == "count_log_tokens":
        result = tool_count_tokens(**args)
        print(f"  [TOOL RESULT] tokens={result['token_count']}, ok={result['within_limit']}")
        return result
    if name == "submit_logs":
        return tool_submit_logs(**args)
    return {"error": f"Unknown tool: {name}"}


def call_llm(messages: list, tools=None) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    body: dict = {"model": MODEL, "messages": messages, "temperature": 0.1, "max_tokens": 4096}
    if tools:
        body["tools"] = tools
    resp = requests.post(f"{OPENROUTER_API_URL}/chat/completions", headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()


SYSTEM_PROMPT = """You are a failure analysis agent for an industrial power plant.
Use search_logs, build a condensed chronological log (<=1450 tokens), count_log_tokens, then submit_logs.
Format: YYYY-MM-DD HH:MM [LEVEL] COMPONENT short_description
Iterate on hub feedback until you receive a flag."""


def _condense_line(line: str) -> str:
    match = re.match(
        r"\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}):\d{2}\] \[(CRIT|ERRO|WARN|INFO)\] (.+)", line
    )
    if match:
        return f"{match.group(1)} [{match.group(2)}] {match.group(3)}"
    return line[:160]


def run_demo() -> dict | None:
    """Deterministic demo using function tools without OpenRouter."""
    global LOG_LINES
    LOG_LINES = load_log_file(LOG_FILE)
    print(f"[DEMO] Loaded {len(LOG_LINES)} log lines from {LOG_FILE}")

    search = dispatch_tool(
        "search_logs",
        {
            "levels": ["CRIT", "ERRO"],
            "keywords": ["WTRPMP", "ECCS8", "FIRMWARE", "coolant", "pump"],
            "limit": 40,
        },
    )
    condensed = [_condense_line(entry) for entry in search["entries"]]
    log_text = "\n".join(dict.fromkeys(condensed))

    dispatch_tool("count_log_tokens", {"log_text": log_text})
    result = dispatch_tool("submit_logs", {"log_text": log_text})

    if "FLG" not in json.dumps(result, ensure_ascii=False):
        extra = dispatch_tool("search_logs", {"keywords": ["WTRPMP", "ECCS8"], "limit": 20})
        merged = list(dict.fromkeys(condensed + [_condense_line(e) for e in extra["entries"]]))
        log_text = "\n".join(merged)
        dispatch_tool("count_log_tokens", {"log_text": log_text})
        result = dispatch_tool("submit_logs", {"log_text": log_text})

    return result


def run_agent() -> None:
    global LOG_LINES
    LOG_LINES = load_log_file(LOG_FILE)
    print(f"[INFO] Loaded {len(LOG_LINES)} log lines from {LOG_FILE}")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Analyze failure logs: search CRIT/ERRO for power, cooling, pumps, firmware. "
                "Submit condensed log <=1450 tokens and iterate on hub feedback."
            ),
        },
    ]

    iteration = 0
    flag_found = False

    while iteration < MAX_ITERATIONS and not flag_found:
        iteration += 1
        print(f"\n{'=' * 60}\nITERATION {iteration}/{MAX_ITERATIONS}\n{'=' * 60}")

        while True:
            response = call_llm(messages, tools=TOOLS)
            msg = response["choices"][0]["message"]
            messages.append(msg)
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                content = msg.get("content", "")
                if content:
                    print(f"\n[AGENT] {content[:500]}")
                break

            for tc in tool_calls:
                tool_name = tc["function"]["name"]
                try:
                    tool_args = json.loads(tc["function"]["arguments"])
                except json.JSONDecodeError:
                    tool_args = {}
                result = dispatch_tool(tool_name, tool_args)
                result_str = json.dumps(result, ensure_ascii=False)
                if "FLG" in result_str:
                    print(f"\nFLAG FOUND: {result_str}")
                    flag_found = True
                messages.append({"role": "tool", "tool_call_id": tc["id"], "content": result_str})

            if flag_found:
                break

        if flag_found:
            break

        if iteration < MAX_ITERATIONS and not flag_found:
            messages.append(
                {
                    "role": "user",
                    "content": "Continue: address hub feedback, update log, verify tokens, resubmit.",
                }
            )

    if flag_found:
        print("\nTask completed successfully!")
    else:
        print(f"\nReached max iterations ({MAX_ITERATIONS}) without flag.")


def main() -> None:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
        result = run_demo()
        if result and "FLG" in json.dumps(result, ensure_ascii=False):
            print(f"\nSuccess! {result}")
            sys.exit(0)
        print("\nNo flag obtained.")
        sys.exit(1)

    run_agent()


if __name__ == "__main__":
    main()
