from supabase import create_client
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create Supabase client instance (NOT import the module directly)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

response = supabase.table('conversations').insert({
    "user_id": "test_user",
    "role": "user",
    "content": "Test message from test script",
    "timestamp": datetime.utcnow().isoformat()
}).execute()

if response.error:
    print(f"Insert error: {response.error.message}")
else:
    print("Insert successful")
