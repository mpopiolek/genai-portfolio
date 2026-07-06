import json
from datetime import datetime
from pathlib import Path


class SessionManager:
    """Operator session persistence on disk (excluded from git via .gitignore)."""

    def __init__(self, sessions_dir="sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self._memory_cache = {}

    def _get_session_path(self, session_id):
        return self.sessions_dir / f"{session_id}.json"

    def get_session(self, session_id):
        if session_id in self._memory_cache:
            return self._memory_cache[session_id]

        path = self._get_session_path(session_id)
        if path.exists():
            with open(path, "r", encoding="utf-8") as handle:
                session = json.load(handle)
                self._memory_cache[session_id] = session
                return session

        session = {
            "sessionID": session_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
        }
        self._memory_cache[session_id] = session
        self._save_session(session_id, session)
        return session

    def add_message(self, session_id, role, content):
        session = self.get_session(session_id)
        session["messages"].append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )
        self._save_session(session_id, session)
        return session

    def _save_session(self, session_id, session):
        path = self._get_session_path(session_id)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(session, handle, ensure_ascii=False, indent=2)

    def get_messages_for_llm(self, session_id):
        session = self.get_session(session_id)
        return [{"role": msg["role"], "content": msg["content"]} for msg in session["messages"]]
