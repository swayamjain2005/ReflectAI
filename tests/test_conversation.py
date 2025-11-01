from core.chat_memory import append_to_conversation
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
append_to_conversation("test_user", "user", "Hello, this is a test.")
append_to_conversation("test_user", "assistant", "Hi! How can I assist you today?")
