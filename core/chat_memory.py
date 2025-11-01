import json
import os
from datetime import datetime

CONVERSATIONS_DIR = "conversations"

if not os.path.exists(CONVERSATIONS_DIR):
    os.makedirs(CONVERSATIONS_DIR)

def load_user_conversation(user_id: str):
    filepath = os.path.join(CONVERSATIONS_DIR, f"{user_id}.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_user_conversation(user_id: str, conversation):
    filepath = os.path.join(CONVERSATIONS_DIR, f"{user_id}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False)

def append_to_conversation(user_id: str, role: str, content: str):
    conversation = load_user_conversation(user_id)
    conversation.append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat()
    })
    save_user_conversation(user_id, conversation)
    return conversation
