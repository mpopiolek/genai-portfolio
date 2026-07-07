#!/usr/bin/env python3
"""
Secure Command Agent — restricted VM shell access with guardrails and ban learning.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
SHELL_API_URL = os.getenv("SHELL_API_URL", f"{AIDEVS_API_URL}/api/shell")
MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

DEMO_CODE = "ECCS-DEMO1234567890abcdef"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("command_agent")

HARD_BLOCKED = {"/etc", "/root", "/proc"}

SENSITIVE_FILENAME_PATTERNS = re.compile(
    r"(^|/)\.env(\b|$)|\.secret|\.passwd|\.password|shadow|sudoers",
    re.IGNORECASE,
)

gitignore_blacklist: set[str] = set()
_current_dir = "/home/user"


def _add_to_blacklist(path: str, reason: str = "") -> None:
    path = path.strip()
    if path and path not in gitignore_blacklist:
        log.warning("[BLACKLIST] Adding '%s' (reason: %s)", path, reason or "-")
        gitignore_blacklist.add(path)


def _is_blacklisted(cmd: str) -> str | None:
    for blocked in HARD_BLOCKED:
        if re.search(r"(?<!\w)" + re.escape(blocked) + r"(?!\w)", cmd):
            return f"path '{blocked}' is hard-blocked (/etc, /root, /proc)"

    match = SENSITIVE_FILENAME_PATTERNS.search(cmd)
    if match:
        return f"sensitive filename pattern matched: '{match.group()}'"

    for blocked in gitignore_blacklist:
        if re.search(r"(?<!\w)" + re.escape(blocked) + r"(?!\w)", cmd):
            return f"path '{blocked}' is blacklisted (gitignore / previous ban)"

    return None


def _parse_gitignore(content: str, base_path: str) -> list[str]:
    entries = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("!"):
            continue
        if not line.startswith("/"):
            path = base_path.rstrip("/") + "/" + line
        else:
            path = line
        entries.append(path)
    return entries


def _maybe_update_gitignore_from_ls(ls_output: str, current_dir: str) -> None:
    if ".gitignore" not in ls_output:
        return
    gitignore_path = current_dir.rstrip("/") + "/.gitignore"
    log.info("Found .gitignore in ls output, reading %s", gitignore_path)
    result = _raw_shell("cat " + gitignore_path)
    for entry in _parse_gitignore(result, current_dir):
        if entry not in gitignore_blacklist:
            log.info("  [gitignore] blacklisting: %s", entry)
            gitignore_blacklist.add(entry)


def _raw_shell(cmd: str, max_retries: int = 3) -> str:
    payload = {"apikey": AIDEVS_API_KEY, "cmd": cmd}
    for attempt in range(1, max_retries + 1):
        try:
            log.debug("SHELL CMD (attempt %d): %s", attempt, cmd)
            response = requests.post(SHELL_API_URL, json=payload, timeout=30)
            body = response.text.strip()
            log.debug("SHELL RESP [HTTP %d]: %s", response.status_code, body[:600])

            try:
                data = json.loads(body)
                if isinstance(data, dict):
                    output = data.get("output", data.get("result"))
                    if output is not None:
                        return str(output)
                    return body
            except json.JSONDecodeError:
                pass

            return body
        except requests.RequestException as exc:
            log.error("Network error on attempt %d: %s", attempt, exc)
            time.sleep(2)

    return f"ERROR: all {max_retries} attempts failed for cmd: {cmd}"


def shell_exec(cmd: str) -> str:
    global _current_dir

    cmd_stripped = cmd.strip()
    block_reason = _is_blacklisted(cmd_stripped)
    if block_reason:
        log.warning("PRE-BLOCKED cmd (%s): %s", block_reason, cmd_stripped)
        return (
            f"BLOCKED: Command not sent to VM. Reason: {block_reason}. "
            f"Do NOT retry this command. Try a completely different approach."
        )

    result = _raw_shell(cmd_stripped)

    if cmd_stripped.startswith("cd "):
        pwd_result = _raw_shell("pwd")
        if pwd_result and not pwd_result.startswith("ERROR"):
            _current_dir = pwd_result.strip()

    base_cmd = cmd_stripped.split()[0] if cmd_stripped else ""
    if base_cmd == "ls":
        parts = cmd_stripped.split()
        listed_dir = _current_dir
        for part in parts[1:]:
            if not part.startswith("-"):
                listed_dir = part
                break
        _maybe_update_gitignore_from_ls(result, listed_dir)

    return result


def send_answer(code: str) -> str:
    url = f"{AIDEVS_API_URL}/verify"
    payload = {
        "apikey": AIDEVS_API_KEY,
        "task": "firmware",
        "answer": {"confirmation": code},
    }
    log.info("Sending answer to %s", url)
    try:
        response = requests.post(url, json=payload, timeout=20)
        return response.text
    except requests.RequestException as exc:
        log.error("Verify request failed: %s", exc)
        return f"ERROR: {exc}"


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "shell_exec",
            "description": "Execute one shell command on the restricted VM.",
            "parameters": {
                "type": "object",
                "properties": {"cmd": {"type": "string"}},
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_answer",
            "description": "Send ECCS confirmation code to verify endpoint.",
            "parameters": {
                "type": "object",
                "properties": {"code": {"type": "string"}},
                "required": ["code"],
            },
        },
    },
]

SYSTEM_PROMPT = """You operate on a restricted Linux VM via shell_exec.
Find the firmware password, run cooler.bin, obtain ECCS code, call send_answer.
NEVER access /etc, /root, /proc or sensitive dotfiles (.env, .secret).
Respect .gitignore blacklists. One command per tool call."""


def dispatch_tool(name: str, args: dict[str, Any]) -> Any:
    if name == "shell_exec":
        return shell_exec(args["cmd"])
    if name == "send_answer":
        return send_answer(args["code"])
    return f"ERROR: unknown tool {name}"


def demonstrate_guardrails() -> None:
    tests = [
        "cat /etc/passwd",
        "cat /opt/firmware/cooler/.env",
    ]
    for cmd in tests:
        reason = _is_blacklisted(cmd)
        allowed = reason is None
        print(f"Guardrail test: '{cmd}' -> allowed={allowed}")
        if allowed:
            raise RuntimeError(f"Guardrail failed to block: {cmd}")
        print(f"  Reason: {reason}")


def run_demo() -> None:
    """Deterministic firmware task against hub-mock without OpenRouter."""
    demonstrate_guardrails()

    steps = [
        "help",
        "ls /opt/firmware/cooler",
        "cat /opt/firmware/cooler/README.txt",
        "/opt/firmware/cooler/cooler.bin cool-demo-pass",
    ]

    code = DEMO_CODE
    for index, cmd in enumerate(steps, start=1):
        print(f"\n--- Demo step {index} ---")
        print(f"CMD: {cmd}")
        output = shell_exec(cmd)
        print(f"OUTPUT: {output[:500]}")
        if output.startswith("BLOCKED"):
            raise RuntimeError(f"Unexpected block on allowed command: {cmd}")
        if "ECCS-" in output:
            match = re.search(r"ECCS-[A-Za-z0-9]+", output)
            if match:
                code = match.group(0)

    print(f"\n--- Submitting code: {code} ---")
    verify_result = send_answer(code)
    print(f"VERIFY: {verify_result[:500]}")
    if "FLG" not in verify_result:
        raise RuntimeError("Expected flag in verify response")
    print("Success! Flag received.")


def run_agent(max_turns: int = 50) -> None:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": "Start firmware task. Run help first, then explore for password.",
        },
    ]

    for turn in range(1, max_turns + 1):
        log.info("--- Turn %d ---", turn)
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": messages,
            "tools": TOOLS,
            "tool_choice": "auto",
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        try:
            response = requests.post(
                f"{OPENROUTER_API_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            choice = response.json()["choices"][0]
        except requests.RequestException as exc:
            log.error("LLM API error: %s", exc)
            time.sleep(5)
            continue

        msg = choice["message"]
        messages.append(msg)

        if not msg.get("tool_calls"):
            print("\n=== AGENT DONE ===")
            print(msg.get("content", ""))
            break

        for tool_call in msg["tool_calls"]:
            fn_name = tool_call["function"]["name"]
            fn_args = json.loads(tool_call["function"]["arguments"])
            log.info("Tool call: %s(%s)", fn_name, fn_args)
            result = dispatch_tool(fn_name, fn_args)
            log.info("Tool result: %s", str(result)[:500])
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": str(result),
                }
            )

        last_tool = [m["content"] for m in messages if m.get("role") == "tool"]
        if last_tool and "FLG" in last_tool[-1]:
            print("\nFLAG:", last_tool[-1])
            break


def main() -> None:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
        run_demo()
        sys.exit(0)

    missing = [var for var in ("OPENROUTER_API_KEY", "AIDEVS_API_KEY", "AIDEVS_API_URL") if not os.getenv(var)]
    if missing:
        log.error("Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)

    run_agent()


if __name__ == "__main__":
    main()
