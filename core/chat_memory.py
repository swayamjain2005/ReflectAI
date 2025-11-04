import os
import json
from datetime import datetime
from pathlib import Path


CONVERSATIONS_DIR = Path("conversations")


def _get_user_file(user_id: str) -> Path:
    safe_user_id = ''.join(c for c in user_id if c.isalnum() or c in ('-', '_'))
    return CONVERSATIONS_DIR / f"{safe_user_id}.json"


def load_user_conversation(user_id: str):
    try:
        file_path = _get_user_file(user_id)
        if not file_path.exists():
            return []
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception as exc:
        print(f"Error loading conversation for {user_id}: {exc}")
        return []


def append_to_conversation(user_id: str, role: str, content: str, session_id=None):
    try:
        CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = _get_user_file(user_id)
        history = []
        if file_path.exists():
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    history = json.load(f) or []
            except Exception:
                history = []
        history.append({
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id
        })
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        print(f"Error appending conversation for {user_id}: {exc}")
