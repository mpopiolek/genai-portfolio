#!/usr/bin/env python3
"""
Multimodal Intel Pipeline — radio signal monitoring with transcription and LLM extraction.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()

AIDEVS_API_KEY = os.getenv("AIDEVS_API_KEY", "demo-key")
AIDEVS_API_URL = os.getenv("AIDEVS_API_URL", "http://localhost:8080").rstrip("/")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1").rstrip("/")
DEMO_MODE = os.getenv("DEMO_MODE", "1").lower() in ("1", "true", "yes")

TRIGGER_KEYWORD = os.getenv("INTEL_TRIGGER", "alpha sector")
TASK = "radiomonitoring"


class SignalLogger:
    """Stream-only logger for portfolio demos (no session files committed)."""

    def __init__(self) -> None:
        self.signal_index = 0

    def log(self, message: str) -> None:
        print(message)

    def log_response(self, response: dict[str, Any]) -> None:
        self.signal_index += 1
        self.log(f"\n--- Signal #{self.signal_index} ---")
        self.log(f"  code: {response.get('code')}")
        self.log(f"  message: {response.get('message', '')}")
        if transcription := response.get("transcription"):
            self.log(f"  [TRANSCRIPTION]\n{transcription}")
        if meta := response.get("meta"):
            self.log(f"  [META] {meta}")

    def log_info(self, message: str) -> None:
        self.log(f"[INFO] {message}")

    def log_error(self, message: str) -> None:
        self.log(f"[ERROR] {message}")

    def log_analysis(self, label: str, data: dict[str, Any]) -> None:
        self.log(f"  [INTEL - {label}] {json.dumps(data, ensure_ascii=False)}")


class RadioAgent:
    def __init__(self) -> None:
        self.logger = SignalLogger()
        self.city_name: str | None = None
        self.city_area: float | None = None
        self.warehouses_count: int | None = None
        self.phone_number: str | None = None

    def call_hub(self, answer: dict[str, Any]) -> dict[str, Any]:
        payload = {"apikey": AIDEVS_API_KEY, "task": TASK, "answer": answer}
        response = requests.post(f"{AIDEVS_API_URL}/verify", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()

    def start_session(self) -> dict[str, Any]:
        return self.call_hub({"action": "start"})

    def listen(self) -> dict[str, Any]:
        return self.call_hub({"action": "listen"})

    def analyze_with_llm(self, content: str) -> dict[str, Any]:
        prompt = f"""Extract intelligence as JSON only:
{{"city_name": str|null, "area": number|null, "warehouses_count": int|null, "phone_number": str|null}}

Text:
{content}"""

        response = requests.post(
            f"{OPENROUTER_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
            },
            timeout=60,
        )
        response.raise_for_status()
        message = response.json()["choices"][0]["message"]["content"]
        start, end = message.find("{"), message.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(message[start:end])
        return {}

    def demo_extract_intel(self, content: str) -> dict[str, Any]:
        """Deterministic extraction for DEMO_MODE without OpenRouter."""
        city_match = re.search(r"city\s+([A-Za-zÀ-ž\-]+)", content, re.IGNORECASE)
        area_match = re.search(r"(\d+(?:\.\d+)?)\s*km2", content, re.IGNORECASE)
        warehouses_count = None
        numeric_wh = re.search(r"(\d+)\s+warehouses", content, re.IGNORECASE)
        if numeric_wh:
            warehouses_count = int(numeric_wh.group(1))
        else:
            word_match = re.search(
                r"(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+warehouses",
                content,
                re.IGNORECASE,
            )
            if word_match:
                words = {
                    "one": 1,
                    "two": 2,
                    "three": 3,
                    "four": 4,
                    "five": 5,
                    "six": 6,
                    "seven": 7,
                    "eight": 8,
                    "nine": 9,
                    "ten": 10,
                    "eleven": 11,
                    "twelve": 12,
                }
                warehouses_count = words[word_match.group(1).lower()]

        phone_match = re.search(r"(\d{9,12})", content)

        return {
            "city_name": city_match.group(1) if city_match else None,
            "area": float(area_match.group(1)) if area_match else None,
            "warehouses_count": warehouses_count,
            "phone_number": phone_match.group(1) if phone_match else None,
        }

    def extract_intel(self, content: str, label: str) -> bool:
        if TRIGGER_KEYWORD.lower() not in content.lower() and label != "json attachment":
            self.logger.log_info(f"No trigger keyword in {label}")
            return False

        if DEMO_MODE or not OPENROUTER_API_KEY:
            analysis = self.demo_extract_intel(content)
        else:
            analysis = self.analyze_with_llm(content)

        self.logger.log_analysis(label, analysis)
        self._update_findings(analysis)
        return True

    def transcribe_audio_demo(self, audio_bytes: bytes, mime_type: str) -> str:
        self.logger.log_info(f"[PIPELINE] Audio received ({len(audio_bytes)} bytes, {mime_type})")
        self.logger.log_info("[PIPELINE] DEMO_MODE: using mock transcription from hub or placeholder")
        return f"Alpha sector update. City Krakow area 326.55 km2 twelve warehouses contact 48123456789."

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str) -> str | None:
        if DEMO_MODE or not OPENROUTER_API_KEY:
            return self.transcribe_audio_demo(audio_bytes, mime_type)

        fmt_map = {
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
            "audio/ogg": "ogg",
            "audio/mp4": "mp4",
        }
        fmt = fmt_map.get(mime_type.lower(), "mp3")
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

        response = requests.post(
            f"{OPENROUTER_API_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-4o-audio-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_audio", "input_audio": {"data": audio_b64, "format": fmt}},
                            {"type": "text", "text": "Transcribe this audio in Polish. Return text only."},
                        ],
                    }
                ],
                "max_tokens": 1000,
            },
            timeout=60,
        )
        if response.status_code != 200:
            self.logger.log_error(f"Audio transcription failed: {response.status_code}")
            return None
        return response.json()["choices"][0]["message"]["content"].strip()

    def process_attachment(self, attachment_data: dict[str, Any]) -> bool:
        meta = attachment_data.get("meta", "").lower()
        raw_b64 = attachment_data["attachment"]
        decoded = base64.b64decode(raw_b64)

        if any(token in meta for token in ("text", "json", "xml", "html", "csv")):
            self.logger.log_info(f"[PIPELINE] Text/JSON attachment ({meta})")
            content = decoded.decode("utf-8")
            self.logger.log_info(f"[PIPELINE] Attachment content: {content[:200]}")
            try:
                parsed = json.loads(content)
                self.logger.log_analysis("json attachment", parsed)
                self._update_findings(parsed)
                return True
            except json.JSONDecodeError:
                return self.extract_intel(content, "text attachment")

        if any(token in meta for token in ("audio", "mpeg", "wav", "ogg")):
            self.logger.log_info(f"[PIPELINE] Audio attachment ({meta})")
            transcription = self.transcribe_audio(decoded, attachment_data.get("meta", "audio/mpeg"))
            if transcription:
                self.logger.log_info(f"[PIPELINE] Transcription: {transcription}")
                return self.extract_intel(transcription, "audio->transcription")
            return False

        self.logger.log_info(f"[PIPELINE] Unsupported attachment type: {meta}")
        return False

    def _update_findings(self, analysis: dict[str, Any]) -> None:
        if analysis.get("city_name") and not self.city_name:
            self.city_name = str(analysis["city_name"])
        if isinstance(analysis.get("area"), (int, float)) and analysis["area"]:
            self.city_area = round(float(analysis["area"]), 2)
        if analysis.get("warehouses_count") is not None:
            try:
                self.warehouses_count = int(analysis["warehouses_count"])
            except (TypeError, ValueError):
                pass
        if analysis.get("phone_number"):
            self.phone_number = str(analysis["phone_number"])

    def send_final_report(self) -> dict[str, Any] | None:
        self.logger.log_info(
            f"Collected intel: city={self.city_name} area={self.city_area} "
            f"warehouses={self.warehouses_count} phone={self.phone_number}"
        )

        if not all([self.city_name, self.city_area, self.warehouses_count, self.phone_number]):
            self.logger.log_error("Incomplete intel — report not sent")
            return None

        payload = {
            "action": "transmit",
            "cityName": self.city_name,
            "cityArea": f"{self.city_area:.2f}",
            "warehousesCount": self.warehouses_count,
            "phoneNumber": self.phone_number,
        }
        self.logger.log_info(f"Transmitting report: {json.dumps(payload, ensure_ascii=False)}")
        return self.call_hub(payload)

    def run(self) -> None:
        self.logger.log_info("=== MULTIMODAL INTEL PIPELINE START ===")
        start = self.start_session()
        self.logger.log_info(f"Session: {start.get('message', start)}")

        while True:
            response = self.listen()
            self.logger.log_response(response)
            code = response.get("code")

            if code == 100:
                if transcription := response.get("transcription"):
                    self.logger.log_info("[PIPELINE] Hub transcription -> intel extraction")
                    self.extract_intel(transcription, "hub transcription")

                if attachment := response.get("attachment"):
                    self.process_attachment(
                        {
                            "meta": response.get("meta", ""),
                            "filesize": response.get("filesize", 0),
                            "attachment": attachment,
                        }
                    )

            elif code in (101, 403):
                self.logger.log_info(f"Listen loop ended: {response.get('message')}")
                break
            else:
                self.logger.log_error(f"Unexpected listen code: {code}")
                break

        result = self.send_final_report()
        if result:
            flag = result.get("message") or result.get("flag") or str(result)
            print(f"\nResult: {flag}")
            if "FLG" not in str(flag):
                raise RuntimeError("Expected flag in transmit response")


def main() -> None:
    if DEMO_MODE and not OPENROUTER_API_KEY:
        print("[INFO] OPENROUTER_API_KEY not set — using demo mode")
    agent = RadioAgent()
    agent.run()
    sys.exit(0)


if __name__ == "__main__":
    main()
