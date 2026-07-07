"""
Shell exploration agent — LLM-driven server exploration with command guardrails.
"""

from __future__ import annotations

import json
import os
import re
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

HARD_BLOCKED_PATHS = ("/etc", "/root", "/proc")
SENSITIVE_FILENAME_PATTERNS = re.compile(
    r"(^|/)\.env(\b|$)|\.secret|\.passwd|\.password|shadow|sudoers",
    re.IGNORECASE,
)

BLOCKED_PATTERNS = [
    r"rm\s+-rf",
    r"mkfs",
    r":\(\)\{",
    r"\bwget\b",
    r"\bcurl\b",
    r"\bnc\b",
    r"/dev/tcp",
    r"\bsudo\b",
    r"chmod\s+777",
    r">\s*/etc",
    r"\bdd\s+if=",
    r"\bshutdown\b",
    r"\breboot\b",
]

SYSTEM_PROMPT = """Jesteś agentem eksplorującym serwer przez komendy powłoki.
Masz narzędzie shell(cmd). Szukaj daty, miasta i współrzędnych GPS.
Gdy gotowy: FINAL_ANSWER: {"date":"YYYY-MM-DD","city":"...","longitude":...,"latitude":...}
Data = dzień PRZED znalezieniem ciała."""

DEMO_FINAL = {
    "date": "2024-03-17",
    "city": "Krakow",
    "longitude": 19.9450,
    "latitude": 50.0647,
}


def is_command_allowed(cmd: str) -> tuple[bool, str]:
    for blocked in HARD_BLOCKED_PATHS:
        if re.search(r"(?<!\w)" + re.escape(blocked) + r"(?!\w)", cmd):
            return False, f"Blocked by guardrail (path: {blocked})"

    match = SENSITIVE_FILENAME_PATTERNS.search(cmd)
    if match:
        return False, f"Blocked by guardrail (sensitive path: {match.group()})"

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, cmd, re.IGNORECASE):
            return False, f"Blocked by guardrail (pattern: {pattern})"
    return True, ""


def call_shell(cmd: str) -> str:
    allowed, reason = is_command_allowed(cmd)
    if not allowed:
        return f"GUARDRAIL BLOCK: {reason}"

    payload = {"apikey": AIDEVS_API_KEY, "task": "shellaccess", "answer": {"cmd": cmd}}
    response = requests.post(f"{AIDEVS_API_URL}/verify", json=payload, timeout=30)
    data = response.json()
    return data.get("output") or data.get("message") or json.dumps(data)


def call_llm(messages: list) -> str:
    response = requests.post(
        f"{OPENROUTER_API_URL}/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
            "messages": messages,
            "max_tokens": 1024,
        },
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def extract_cmd(text: str) -> str | None:
    match = re.search(r'shell\(["\'`]?(.+?)["\'`]?\)', text, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```(?:bash|sh)?\n(.+?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_final(text: str) -> dict | None:
    match = re.search(r"FINAL_ANSWER:\s*(\{.+?\})", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    return None


def demonstrate_guardrails() -> None:
    for dangerous in ("rm -rf /", "cat /etc/passwd"):
        allowed, reason = is_command_allowed(dangerous)
        print(f"Guardrail test: '{dangerous}' -> allowed={allowed}")
        if allowed:
            raise RuntimeError(f"Guardrail failed to block dangerous command: {dangerous}")
        print(f"  Reason: {reason}")


def run_demo() -> dict:
    """Deterministic exploration against hub-mock without OpenRouter."""
    demonstrate_guardrails()

    steps = [
        "ls /data",
        "grep -i found /data/notes.txt",
        "cat /data/gps.json",
        f"echo '{json.dumps(DEMO_FINAL)}'",
    ]

    for index, cmd in enumerate(steps, start=1):
        print(f"\n--- Demo step {index} ---")
        print(f"CMD: {cmd}")
        output = call_shell(cmd)
        print(f"OUTPUT: {output[:500]}")
        if "GUARDRAIL BLOCK" in output:
            raise RuntimeError(f"Unexpected guardrail block on allowed command: {cmd}")
        if "FLG" in output:
            print(f"\nSuccess! Flag in response.")
            return DEMO_FINAL

    return DEMO_FINAL


def run_agent() -> dict | None:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": "Zacznij eksplorację serwera."})

    for step in range(25):
        print(f"\n--- Step {step + 1} ---")
        response = call_llm(messages)
        print(f"LLM: {response[:300]}...")
        messages.append({"role": "assistant", "content": response})

        final = extract_final(response)
        if final:
            echo_cmd = f"echo '{json.dumps(final)}'"
            allowed, reason = is_command_allowed(echo_cmd)
            if not allowed:
                print(f"Blocked finalization: {reason}")
                return None
            result = call_shell(echo_cmd)
            print(f"Server result: {result}")
            return final

        cmd = extract_cmd(response)
        if not cmd:
            messages.append(
                {"role": "user", "content": "Podaj komendę w formacie: shell('twoja komenda')"}
            )
            continue

        print(f"CMD: {cmd}")
        output = call_shell(cmd)
        print(f"OUTPUT: {output[:500]}")
        if output.startswith("GUARDRAIL BLOCK"):
            messages.append({"role": "user", "content": output})
            continue

        messages.append({"role": "user", "content": f"Wynik komendy `{cmd}`:\n{output}"})

    print("Agent did not find answer within step limit.")
    return None


def main() -> None:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
        result = run_demo()
    else:
        result = run_agent()

    if result:
        print(f"\nFinal answer: {result}")
        sys.exit(0)

    print("\nNo answer found.")
    sys.exit(1)


if __name__ == "__main__":
    main()
