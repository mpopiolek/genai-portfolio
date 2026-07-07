#!/usr/bin/env python3
"""
Async Planning Agent — asyncio turbine scheduling with concurrent hub requests.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
import time
from typing import Any, Optional

import aiohttp
import requests
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

if not AIDEVS_API_URL.endswith("/verify"):
    AIDEVS_API_URL = f"{AIDEVS_API_URL}/verify"

TASK_NAME = "windpower"
LLM_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("async_agent")
http_log = logging.getLogger("async_agent.http")


def llm_call(system: str, user: str, temperature: float = 0.0) -> str:
    response = requests.post(
        f"{OPENROUTER_API_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LLM_MODEL,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


async def hub(session: aiohttp.ClientSession, action: str, extra: Optional[dict] = None) -> dict:
    payload: dict[str, Any] = {
        "apikey": AIDEVS_API_KEY,
        "task": TASK_NAME,
        "answer": {"action": action},
    }
    if extra:
        payload["answer"].update(extra)

    http_log.debug("[HUB ->] action=%s", action)
    started = time.monotonic()
    async with session.post(AIDEVS_API_URL, json=payload) as resp:
        data = await resp.json(content_type=None)
    elapsed = time.monotonic() - started
    http_log.info("[HUB <-] action=%s  %.2fs", action, elapsed)
    return data


async def collect_results(
    session: aiohttp.ClientSession,
    expected: int,
    label: str = "",
    retries: int = 80,
    delay: float = 0.2,
) -> list[dict]:
    collected: list[dict] = []
    attempts = 0
    while len(collected) < expected and attempts < retries:
        attempts += 1
        resp = await hub(session, "getResult")
        if resp.get("code") == -805:
            break
        if resp.get("code", 0) < 0 or not resp.get("sourceFunction"):
            await asyncio.sleep(delay)
            continue
        src = resp.get("sourceFunction", "?")
        log.info("[POLL:%s] sourceFunction=%s (%d/%d)", label, src, len(collected) + 1, expected)
        collected.append(resp)
        if len(collected) < expected:
            await asyncio.sleep(0.05)
    if len(collected) < expected:
        log.warning("[POLL:%s] collected %d/%d", label, len(collected), expected)
    return collected


def estimate_power_kw(
    wind_ms: float,
    pitch: int,
    rated_kw: float,
    wind_yield_table: list[dict],
    pitch_yield_table: list[dict],
) -> float:
    wind_pct = 0.0
    best_diff = float("inf")
    for entry in wind_yield_table:
        wm = entry.get("windMs")
        if wm is None:
            parts = str(entry.get("windMsRange", "0-0")).replace("+", "-999").split("-")
            wm = float(parts[0])
        diff = abs(float(wm) - wind_ms)
        if diff < best_diff:
            best_diff = diff
            yp = str(entry.get("yieldPercent", "0"))
            if "-" in yp:
                lo, hi = yp.split("-")
                wind_pct = (float(lo) + float(hi)) / 2
            else:
                wind_pct = float(yp)

    pitch_pct = 0.0
    for entry in pitch_yield_table:
        if int(entry.get("pitchAngleDeg", -1)) == pitch:
            yp = str(entry.get("yieldPercent", "0"))
            if "-" in yp:
                lo, hi = yp.split("-")
                pitch_pct = (float(lo) + float(hi)) / 2
            else:
                pitch_pct = float(yp)
            break

    return round(rated_kw * (wind_pct / 100) * (pitch_pct / 100), 2)


def analyse_python(
    forecast: list[dict],
    cutoff_wind: float,
    rated_kw: float,
    power_deficit_kw: float,
    wind_yield_table: list[dict],
    pitch_yield_table: list[dict],
) -> dict:
    storm_slots = []
    production_candidates = []

    for slot in forecast:
        wind_ms = float(slot.get("windMs", 0))
        raw = slot.get("timestamp", "1970-01-01 00:00:00")
        date, hour = raw.split(" ", 1)
        hour = hour[:8]

        if wind_ms > cutoff_wind:
            storm_slots.append({"date": date, "hour": hour, "windMs": wind_ms})
        else:
            power = estimate_power_kw(wind_ms, 0, rated_kw, wind_yield_table, pitch_yield_table)
            production_candidates.append(
                {"date": date, "hour": hour, "windMs": wind_ms, "estimatedPowerKw": power}
            )

    sufficient = [c for c in production_candidates if c["estimatedPowerKw"] >= power_deficit_kw]
    if sufficient:
        best = max(sufficient, key=lambda c: c["windMs"])
    elif production_candidates:
        best = max(production_candidates, key=lambda c: c["windMs"])
    else:
        best = None

    return {
        "storm_slots": storm_slots,
        "production_slot": best,
        "production_pitch": 0,
        "storm_pitch": 90,
    }


def parse_power_deficit(deficit_str: str) -> float:
    text = str(deficit_str).strip()
    if "-" in text:
        try:
            return float(text.split("-")[-1])
        except ValueError:
            pass
    try:
        return float(text)
    except ValueError:
        return 5.0


ANALYSIS_SYSTEM = """Verify wind turbine schedule analysis. Return JSON only."""


def analyse_with_llm(
    forecast: list[dict],
    cutoff_wind: float,
    rated_kw: float,
    power_deficit_kw: float,
    wind_yield_table: list[dict],
    pitch_yield_table: list[dict],
) -> dict:
    user = (
        f"forecast={json.dumps(forecast)}\n"
        f"cutoff={cutoff_wind} rated={rated_kw} deficit={power_deficit_kw}\n"
        f"windYield={json.dumps(wind_yield_table)}\n"
        f"pitchYield={json.dumps(pitch_yield_table)}"
    )
    raw = llm_call(ANALYSIS_SYSTEM, user)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)


async def run_agent(use_llm: bool = False) -> None:
    log.info("=== ASYNC PLANNING AGENT START ===")

    async with aiohttp.ClientSession() as session:
        log.info("-- Step 0: documentation --")
        doc_resp = await hub(session, "get", {"param": "documentation"})
        if doc_resp.get("code", -1) < 0:
            await hub(session, "start")
            doc_resp = await hub(session, "get", {"param": "documentation"})

        cutoff_wind = float((doc_resp.get("safety") or {}).get("cutoffWindMs") or 14)
        rated_kw = float(doc_resp.get("ratedPowerKw") or 14)
        wind_yield_table = doc_resp.get("windPowerYieldPercent", [])
        pitch_yield_table = doc_resp.get("pitchAngleYieldPercent", [])

        log.info("-- Step 1: start session --")
        start_resp = await hub(session, "start")
        session_timeout = start_resp.get("sessionTimeout", 120)
        t_session = time.monotonic()

        log.info("-- Step 2: queue 3 data requests CONCURRENTLY (asyncio.gather) --")
        await asyncio.gather(
            hub(session, "get", {"param": "weather"}),
            hub(session, "get", {"param": "powerplantcheck"}),
            hub(session, "get", {"param": "turbinecheck"}),
        )
        log.info("[ASYNC] 3 hub get() calls dispatched in parallel")

        log.info("-- Step 3: poll getResult for queued responses --")
        data_results = await collect_results(session, expected=3, label="data")

        weather_data = plant_data = turbine_data = None
        for item in data_results:
            src = (item.get("sourceFunction") or "").lower()
            if "weather" in src:
                weather_data = item
            elif "powerplant" in src:
                plant_data = item
            elif "turbine" in src:
                turbine_data = item

        if not weather_data:
            raise RuntimeError("Missing weather data from hub mock")

        forecast = weather_data.get("forecast", [])
        power_deficit_kw = parse_power_deficit((plant_data or {}).get("powerDeficitKw", "4"))
        log.info(
            "Data ready: forecast=%d points deficit=%.1f kW turbine=%s",
            len(forecast),
            power_deficit_kw,
            bool(turbine_data),
        )

        log.info("-- Step 4: deterministic Python analysis --")
        analysis = analyse_python(
            forecast, cutoff_wind, rated_kw, power_deficit_kw, wind_yield_table, pitch_yield_table
        )

        if use_llm:
            log.info("-- Step 4b: optional LLM cross-check --")
            try:
                analyse_with_llm(
                    forecast, cutoff_wind, rated_kw, power_deficit_kw, wind_yield_table, pitch_yield_table
                )
            except Exception as exc:
                log.warning("LLM cross-check skipped: %s", exc)

        storm_slots = analysis["storm_slots"]
        production_slot = analysis["production_slot"]
        if not production_slot:
            raise RuntimeError("No production slot found")

        log.info(
            "Analysis: storms=%d production=%s %s",
            len(storm_slots),
            production_slot["date"],
            production_slot["hour"],
        )

        slots_to_sign = [
            {
                "startDate": s["date"],
                "startHour": s["hour"],
                "windMs": s["windMs"],
                "pitchAngle": analysis["storm_pitch"],
            }
            for s in storm_slots
        ]
        slots_to_sign.append(
            {
                "startDate": production_slot["date"],
                "startHour": production_slot["hour"],
                "windMs": production_slot["windMs"],
                "pitchAngle": analysis["production_pitch"],
            }
        )

        log.info("-- Step 5: queue %d unlock requests CONCURRENTLY --", len(slots_to_sign))
        await asyncio.gather(*[hub(session, "unlockCodeGenerator", slot) for slot in slots_to_sign])
        log.info("[ASYNC] unlockCodeGenerator batch dispatched in parallel")

        unlock_results = await collect_results(session, expected=len(slots_to_sign), label="unlock")
        unlock_map: dict[str, str] = {}
        for item in unlock_results:
            signed = item.get("signedParams", {})
            key = f"{signed.get('startDate', '')} {signed.get('startHour', '')}"
            code = item.get("unlockCode", "")
            if key.strip() and code:
                unlock_map[key] = code
                log.info("[UNLOCK] %s -> %s", key, code)

        configs: dict[str, dict] = {}
        for slot in storm_slots:
            key = f"{slot['date']} {slot['hour']}"
            configs[key] = {
                "pitchAngle": analysis["storm_pitch"],
                "turbineMode": "idle",
                "unlockCode": unlock_map.get(key, "DEMO-STORM"),
            }

        prod_key = f"{production_slot['date']} {production_slot['hour']}"
        configs[prod_key] = {
            "pitchAngle": analysis["production_pitch"],
            "turbineMode": "production",
            "unlockCode": unlock_map.get(prod_key, "DEMO-PROD"),
        }

        log.info("-- Step 6: submit config (%d slots) --", len(configs))
        config_resp = await hub(session, "config", {"configs": configs})
        log.info("[CONFIG] %s", config_resp)

        log.info("-- Step 7: turbinecheck data --")
        if turbine_data:
            log.info("[TURBINECHECK] status=%s", turbine_data.get("status"))

        log.info("-- Step 8: done --")
        done_resp = await hub(session, "done")
        elapsed = time.monotonic() - t_session
        log.info("Finished in %.1fs / %ss timeout", elapsed, session_timeout)

        flag = done_resp.get("flag") or done_resp.get("message") or done_resp.get("result")
        print(f"\nResult: {flag}")
        if flag and "FLG" not in str(flag):
            raise RuntimeError("Expected flag in done response")


def main() -> None:
    use_llm = not DEMO_MODE and bool(OPENROUTER_API_KEY)
    if DEMO_MODE or not OPENROUTER_API_KEY:
        if not OPENROUTER_API_KEY:
            print("[INFO] OPENROUTER_API_KEY not set — demo mode (Python analysis only)")
    elif not all([OPENROUTER_API_KEY, AIDEVS_API_KEY, AIDEVS_API_URL]):
        log.critical("Missing required environment variables")
        sys.exit(1)

    asyncio.run(run_agent(use_llm=use_llm))


if __name__ == "__main__":
    main()
