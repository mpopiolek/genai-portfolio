import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from llm_handler import LLMHandler
from package_api import PackageAPI
from session_manager import SessionManager

load_dotenv()

app = Flask(__name__)

session_manager = SessionManager(sessions_dir=os.getenv("SESSIONS_DIR", "sessions"))
package_api = PackageAPI(
    api_key=os.getenv("AIDEVS_API_KEY", "demo-key"),
    api_url=os.getenv("AIDEVS_API_URL", "http://localhost:8080/api/packages"),
)
llm_handler = LLMHandler(
    openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
    openrouter_api_url=os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1"),
    package_api=package_api,
)

SYSTEM_PROMPT = llm_handler.SYSTEM_PROMPT


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing JSON body"}), 400

        session_id = data.get("sessionID")
        user_message = data.get("msg")
        if not session_id or not user_message:
            return jsonify({"error": "Missing sessionID or msg"}), 400

        session_manager.get_session(session_id)
        messages_for_llm = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages_for_llm.extend(session_manager.get_messages_for_llm(session_id))

        response_text = llm_handler.process_message(user_message, messages_for_llm)

        session_manager.add_message(session_id, "user", user_message)
        session_manager.add_message(session_id, "assistant", response_text)

        return jsonify({"msg": response_text}), 200
    except Exception as exc:
        return jsonify({"error": f"Server error: {exc}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Logistics server available"}), 200


@app.route("/sessions", methods=["GET"])
def list_sessions():
    try:
        sessions_dir = session_manager.sessions_dir
        if not sessions_dir.exists():
            return jsonify({"sessions": []}), 200
        sessions = [path.stem for path in sessions_dir.glob("*.json")]
        return jsonify({"sessions": sessions}), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    print(f"Logistics server starting on http://localhost:{port}")
    print(f"POST http://localhost:{port}/chat")
    print(f"GET  http://localhost:{port}/health")
    app.run(debug=False, host="0.0.0.0", port=port)
