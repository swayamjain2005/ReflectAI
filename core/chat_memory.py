import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def load_user_conversation(user_id: str):
    try:
        response = (
            supabase
            .table('conversations')
            .select('*')
            .eq('user_id', user_id)
            .order('timestamp', desc=False)
            .execute()
        )
        error = getattr(response, 'error', None)
        if error:
            print(f"Error loading conversation: {error.message if hasattr(error, 'message') else str(error)}")
            return []
        return getattr(response, 'data', [])
    except Exception as exc:
        print(f"Error loading conversation for {user_id}: {exc}")
        return []


def append_to_conversation(user_id: str, role: str, content: str, session_id=None):
    try:
        payload = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": session_id,
        }
        response = supabase.table('conversations').insert(payload).execute()
        error = getattr(response, 'error', None)
        if error:
            print(f"Error appending conversation: {error.message if hasattr(error, 'message') else str(error)}")
    except Exception as exc:
        print(f"Error appending conversation for {user_id}: {exc}")
