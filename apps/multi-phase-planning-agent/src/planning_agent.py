#!/usr/bin/env python3
"""
Multi-Phase Planning Agent — sequential world gathering then route planning.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
HUB_BASE = os.getenv("HUB_BASE", AIDEVS_API_URL).rstrip("/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

INFO_MODEL = os.getenv("INFO_MODEL", "openai/gpt-4o-mini")
ROUTE_MODEL = os.getenv("ROUTE_MODEL", "openai/gpt-4o-mini")

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
DEMO_ROUTE = [
    "rocket",
    "up",
    "up",
    "up",
    "right",
    "right",
    "right",
    "right",
    "right",
    "dismount",
    "right",
    "right",
    "right",
]

KNOWN_OPERATIONS = ["up", "down", "left", "right", "dismount", "rocket", "horse", "walk", "car"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("planning_agent")


def make_absolute(url: str) -> str:
    if url.startswith("http"):
        return url
    return HUB_BASE + ("" if url.startswith("/") else "/") + url


def tool_search(query: str) -> dict:
    url = f"{HUB_BASE}/api/toolsearch"
    log.info("[toolsearch] %r", query)
    response = requests.post(url, json={"apikey": AIDEVS_API_KEY, "query": query}, timeout=30)
    response.raise_for_status()
    data = response.json()
    log.info("[toolsearch] -> %s", json.dumps(data, ensure_ascii=False)[:300])
    return data


def call_tool(url: str, query: str) -> dict:
    abs_url = make_absolute(url)
    log.info("[tool] %s <- %r", abs_url, query)
    response = requests.post(abs_url, json={"apikey": AIDEVS_API_KEY, "query": query}, timeout=30)
    response.raise_for_status()
    data = response.json()
    log.info("[tool] -> %s", json.dumps(data, ensure_ascii=False)[:400])
    return data


def llm(model: str, messages: list, temperature: float = 0.0) -> str:
    log.info("[llm] model=%s msgs=%d", model, len(messages))
    response = requests.post(
        f"{OPENROUTER_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={"model": model, "messages": messages, "temperature": temperature},
        timeout=120,
    )
    response.raise_for_status()
    text = response.json()["choices"][0]["message"]["content"]
    log.info("[llm] response (%d chars)", len(text))
    return text


def verify(answer: list) -> dict:
    log.info("[verify] route=%s", answer)
    response = requests.post(
        f"{AIDEVS_API_URL}/verify",
        json={"apikey": AIDEVS_API_KEY, "task": "savethem", "answer": answer},
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    log.info("[verify] -> %s", data)
    return data


def extract_tools(data: dict | list, found: dict | None = None) -> dict:
    if found is None:
        found = {}
    if isinstance(data, dict):
        url = data.get("url") or data.get("endpoint") or data.get("href")
        name = data.get("name") or data.get("title")
        if url and isinstance(url, str):
            found[name or url] = make_absolute(url)
        for value in data.values():
            extract_tools(value, found)
    elif isinstance(data, list):
        for item in data:
            extract_tools(item, found)
    return found


def load_world_fixture() -> dict:
    path = FIXTURES_DIR / "world_info.json"
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def gather_world_info() -> tuple[dict, dict]:
    log.info("=== PHASE 1: World information gathering ===")

    all_results: list[str] = []
    tool_urls: dict[str, str] = {}

    for query in ["map grid terrain", "vehicle fuel consumption", "movement rules"]:
        try:
            data = tool_search(query)
            all_results.append(f"TOOLSEARCH {query!r}:\n{json.dumps(data, ensure_ascii=False)}")
            tool_urls.update(extract_tools(data))
            time.sleep(0.2)
        except Exception as exc:
            log.warning("toolsearch error %r: %s", query, exc)

    known_tools = {
        "maps": f"{HUB_BASE}/api/maps",
        "wehicles": f"{HUB_BASE}/api/wehicles",
        "books": f"{HUB_BASE}/api/books",
    }
    for name, url in known_tools.items():
        tool_urls.setdefault(name, url)

    log.info("Discovered tools: %s", tool_urls)

    query_sets = {
        "maps": ["map", "grid", "start position", "goal position"],
        "wehicles": ["vehicle list", "fuel per move", "food per move"],
        "books": ["movement rules", "resource costs"],
    }

    for tool_name, tool_url in tool_urls.items():
        short = tool_name.lower()
        if "map" in short:
            queries = query_sets["maps"]
        elif "wehicle" in short or "vehicle" in short:
            queries = query_sets["vehicles"]
        elif "book" in short:
            queries = query_sets["books"]
        else:
            queries = query_sets["maps"]

        for query in queries:
            try:
                data = call_tool(tool_url, query)
                all_results.append(
                    f"TOOL {tool_name} query={query!r}:\n{json.dumps(data, ensure_ascii=False)}"
                )
                time.sleep(0.15)
            except Exception as exc:
                log.debug("Tool error %s %r: %s", tool_url, query, exc)

    full_data = "\n\n---\n\n".join(all_results)
    log.info("Collected %d chars from %d API calls", len(full_data), len(all_results))

    synthesis = llm(
        INFO_MODEL,
        [
            {
                "role": "user",
                "content": f"""Extract world model JSON for a 10x10 grid pathfinding task.
Output ONLY JSON inside <WORLD_INFO>...</WORLD_INFO> tags.

RAW DATA:
{full_data[:12000]}
""",
            }
        ],
    )

    world_info: dict = {}
    match = re.search(r"<WORLD_INFO>(.*?)</WORLD_INFO>", synthesis, re.DOTALL)
    if match:
        try:
            world_info = json.loads(match.group(1).strip())
        except json.JSONDecodeError as exc:
            world_info = {"parse_error": str(exc), "llm_raw": synthesis}
    else:
        world_info = {"no_tags": True, "llm_raw": synthesis}

    world_info["_raw_data"] = full_data
    world_info["_tool_urls"] = tool_urls
    return world_info, tool_urls


ROUTE_SYSTEM = """You plan routes on a 10x10 grid.
Output ONLY a JSON array: first element is transport (rocket|horse|car|walk), then moves.
Allowed moves: up, down, left, right, dismount."""


def plan_route(world_info: dict, failures: list | None = None) -> list:
    log.info("=== PHASE 2: Route planning ===")

    failures_txt = ""
    if failures:
        failures_txt = f"\nPREVIOUS FAILURES:\n{json.dumps(failures, indent=2)}\n"

    clean = {k: v for k, v in world_info.items() if not k.startswith("_")}
    user_msg = f"""World model:
{json.dumps(clean, indent=2, ensure_ascii=False)}
{failures_txt}
Plan optimal route. Output JSON array only."""

    response = llm(
        ROUTE_MODEL,
        [
            {"role": "system", "content": ROUTE_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )

    cleaned = re.sub(r"```(?:json)?", "", response).strip().rstrip("`").strip()
    for pattern in [r'(\["(?:rocket|horse|car|walk)".*?\])', r"(\[.*?\])"]:
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            try:
                route = json.loads(match.group(1))
                if isinstance(route, list) and len(route) >= 2:
                    fixed = [el for el in route if el in KNOWN_OPERATIONS]
                    if len(fixed) >= 2:
                        log.info("Final route: %s", fixed)
                        return fixed
            except json.JSONDecodeError:
                continue

    log.error("Could not extract valid route")
    return []


def run_demo() -> None:
    log.info("=== PHASE 1: World information gathering (demo) ===")

    for query in ["map grid terrain", "vehicle fuel", "movement rules"]:
        tool_search(query)

    for path in ["/api/maps", "/api/wehicles", "/api/books"]:
        call_tool(path, "demo query")

    world_info = load_world_fixture()
    start = world_info.get("map", {}).get("start")
    goal = world_info.get("map", {}).get("goal")
    log.info("World model loaded: start=%s goal=%s", start, goal)

    log.info("=== PHASE 2: Route planning (demo) ===")
    route = DEMO_ROUTE
    log.info("Using precomputed demo route (%d steps): %s", len(route), route)

    log.info("=== Verify route with hub ===")
    result = verify(route)
    message = str(result.get("message", result))
    print(f"\nVerify result: {message}")
    if "FLG" not in message:
        raise RuntimeError("Expected flag in verify response")
    print("Success! Multi-phase demo complete.")


def run_agent() -> None:
    world_info, _ = gather_world_info()
    grid = world_info.get("map", {}).get("grid")
    if not grid:
        log.warning("No map grid in world model — route planning may fail")

    failures: list[dict] = []
    for attempt in range(1, 4):
        log.info("--- Route attempt %d/3 ---", attempt)
        route = plan_route(world_info, failures or None)
        if not route:
            failures.append({"attempt": attempt, "error": "No route generated"})
            continue

        result = verify(route)
        message = str(result.get("message", ""))
        if result.get("code") == 0 or "FLG:" in message:
            print(f"\nSUCCESS!\nRoute: {route}\nResult: {result}")
            return

        failures.append({"attempt": attempt, "route": route, "result": result})
        world_info["_last_error"] = message

    raise RuntimeError("All route attempts failed")


def main() -> None:
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
        run_demo()
        sys.exit(0)

    missing = [name for name in ("OPENROUTER_API_KEY", "AIDEVS_API_KEY", "AIDEVS_API_URL") if not os.getenv(name)]
    if missing:
        log.error("Missing environment variables: %s", ", ".join(missing))
        sys.exit(1)

    run_agent()


if __name__ == "__main__":
    main()
