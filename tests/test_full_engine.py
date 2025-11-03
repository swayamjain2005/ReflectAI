import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.therapy_engine_groq import TherapyEngine

if __name__ == "__main__":
    engine = TherapyEngine(user_id="test_user")
    prompt = "I feel overwhelmed and anxious."
    response = engine.process(prompt)
    print("ReflectAI Response:\n", response)
