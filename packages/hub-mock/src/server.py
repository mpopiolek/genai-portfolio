#!/usr/bin/env python3
"""Lightweight HTTP stub for AIDevs hub endpoints used by portfolio agents."""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"
PORT = int(os.getenv("HUB_MOCK_PORT", "8080"))

# Per-task turn counter for sequential dialog fixtures
_turn_counters: dict[str, int] = {}


def _load_fixtures() -> dict[str, dict[str, Any]]:
    """Load fixture files from fixtures/<route>/<agent>.json keyed by task name."""
    by_task: dict[str, dict[str, Any]] = {}
    route_registry: dict[str, list[str]] = {}

    if not FIXTURES_DIR.exists():
        return by_task

    for route_dir in sorted(FIXTURES_DIR.iterdir()):
        if not route_dir.is_dir():
            continue
        route = route_dir.name
        route_registry[route] = []
        for fixture_file in sorted(route_dir.glob("*.json")):
            data = json.loads(fixture_file.read_text(encoding="utf-8"))
            task = data.get("task")
            if not task:
                continue
            data["_route"] = route
            data["_agent"] = fixture_file.stem
            by_task[task] = data
            route_registry[route].append(fixture_file.stem)

    return by_task


FIXTURES_BY_TASK = _load_fixtures()


def _match_request(body: dict[str, Any], pattern: dict[str, Any]) -> bool:
    for key, expected in pattern.items():
        actual = body.get(key)
        if isinstance(expected, dict) and isinstance(actual, dict):
            for sub_key, sub_expected in expected.items():
                sub_actual = actual.get(sub_key)
                if sub_expected == "*" and sub_actual is not None:
                    continue
                if sub_actual != sub_expected:
                    return False
        elif actual != expected:
            return False
    return True


def _resolve_verify_response(body: dict[str, Any]) -> dict[str, Any]:
    task = body.get("task", "")
    fixture = FIXTURES_BY_TASK.get(task)
    if not fixture:
        return {"error": f"No fixture for task '{task}'", "code": 404}

    turns: list[dict[str, Any]] = fixture.get("turns", [])
    if not turns:
        return {"error": f"Empty fixture for task '{task}'", "code": 500}

    counter = _turn_counters.get(task, 0)

    # Find next matching turn starting from counter (allows optional request_match)
    for idx in range(counter, len(turns)):
        turn = turns[idx]
        request_match = turn.get("request_match")
        if request_match and not _match_request(body, request_match):
            continue
        _turn_counters[task] = idx + 1
        return turn.get("response", {})

    # Fallback: return last turn response if dialog exhausted
    last = turns[-1].get("response", {})
    return last


def _resolve_route_response(route: str, body: dict[str, Any]) -> dict[str, Any]:
    """Generic handler for /api/packages and /api/shell using action-based fixtures."""
    action = body.get("action", "")
    task = body.get("task", action or route)
    fixture = FIXTURES_BY_TASK.get(task)
    if fixture and fixture.get("_route") == route:
        return _resolve_verify_response(body)

    # Scan fixtures in route dir for action match
    route_dir = FIXTURES_DIR / route
    if route_dir.exists():
        for fixture_file in sorted(route_dir.glob("*.json")):
            data = json.loads(fixture_file.read_text(encoding="utf-8"))
            for turn in data.get("turns", []):
                match = turn.get("request_match", {})
                if _match_request(body, match):
                    return turn.get("response", {})
            if data.get("default_response"):
                return data["default_response"]

    return {"error": f"No fixture match for {route}", "code": 404}


class HubMockHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        print(f"[hub-mock] {self.address_string()} {format % args}")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        path = self.path.rstrip("/") or "/"

        if path == "/verify":
            result = _resolve_verify_response(body)
        elif path == "/api/packages":
            result = _resolve_route_response("api-packages", body)
        elif path == "/api/shell":
            result = _resolve_route_response("api-shell", body)
        else:
            self._send_json(404, {"error": f"Unknown route {path}"})
            return

        if result.get("code") == 404:
            self._send_json(404, result)
        elif result.get("code") == 500:
            self._send_json(500, result)
        else:
            self._send_json(200, result)

    def do_GET(self) -> None:
        if self.path.rstrip("/") == "/health":
            self._send_json(
                200,
                {
                    "status": "ok",
                    "tasks": list(FIXTURES_BY_TASK.keys()),
                    "routes": ["/verify", "/api/packages", "/api/shell"],
                },
            )
        else:
            self._send_json(404, {"error": "Not found"})


def main() -> None:
    server = HTTPServer(("0.0.0.0", PORT), HubMockHandler)
    print(f"hub-mock listening on :{PORT} — tasks: {list(FIXTURES_BY_TASK.keys())}")
    server.serve_forever()


if __name__ == "__main__":
    main()
