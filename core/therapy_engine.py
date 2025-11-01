import os
from ethical_modules.safety_checker import EthicalSafetyChecker
from ethical_modules.bias_detector import BiasDetector
from ethical_modules.ethics_logger import EthicsLogger
import random
import requests
from dotenv import load_dotenv
from core.chat_memory import load_user_conversation, append_to_conversation

load_dotenv()

SYSTEM_PROMPT = """
You are ReflectAI, a skilled and empathetic digital therapist trained in cognitive-behavioral therapy (CBT) and motivational interviewing techniques.

Your role:
- Listen carefully and respond thoughtfully to the user's thoughts and feelings.
- Be warm, supportive, and professional, balancing empathy with gentle guidance.
- Use light humor or mild sarcasm only when the user's tone is casual and not about serious or crisis topics, to build rapport without offending.
- Never dismiss, minimize, or make light of genuine distress or serious issues.
- Always prioritize safety: if the user shows crisis signs, offer resources and suggest professional help.
- Do not provide medical or diagnostic advice.
- If a user asks about topics outside mental health and emotional wellbeing, gently redirect them to focus on what ReflectAI is designed for.

Conversational style:
- Reflect feelings back genuinely but avoid pretending to feel exactly what the user feels.
- Encourage self-reflection and empowerment.
- Keep responses concise but meaningful.

Example:
User: "I'm feeling super anxious but also kind of frustrated."
ReflectAI: "Sometimes that mix can feel like your brain throwing a big noisy party. Let's see if we can quiet down the guests a bit — what's been on your mind lately?"

Remember to adapt your tone based on user cues and maintain ethical boundaries at all times.
"""

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateMessage?key={GOOGLE_API_KEY}"

def query_gemini_with_messages(messages):
    body = {
        "prompt": {
            "messages": messages
        },
        "temperature": 0.7,
        "maxOutputTokens": 300
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(GEMINI_API_URL, headers=headers, json=body)
    if response.status_code == 200:
        data = response.json()
        return data['candidates'][0]['content']
    else:
        return "Sorry, I am having trouble connecting to the support system right now."

HUMOR_TRIGGERS = ["stress", "anxious", "nervous", "worried", "upset"]

HUMOR_RESPONSES = [
    "Remember, even stressed-out squirrels find their acorns eventually!",
    "Feeling anxious? Deep breaths... or pretend you're a calm cat pretending to care.",
    "It's okay to be nervous; even superheroes get butterflies before the big fight.",
    "Worried? Sometimes your brain just needs a tiny vacation - maybe a mental hammock?",
    "Upset? How about a mini dance break? No one can be sad while dancing (unless they're a robot)."
]

UNSUPPORTED_TOPICS = [
    "math", "programming", "history", "capital of", "movie",
    "football", "phone", "shopping", "flight", "recipe",
    "disease", "joke", "horoscope", "translate", "news"
]

def is_out_of_scope(user_input):
    lower = user_input.lower()
    return any(topic in lower for topic in UNSUPPORTED_TOPICS)

class TherapyEngine:
    def __init__(self, user_id):
        self.safety_checker = EthicalSafetyChecker()
        self.bias_detector = BiasDetector()
        self.logger = EthicsLogger()
        self.user_id = user_id

    def process(self, user_input: str):
        # Humor response shortcut
        if any(trigger in user_input.lower() for trigger in HUMOR_TRIGGERS):
            humor = random.choice(HUMOR_RESPONSES)
            return f"{humor}\n\nTell me more about what you're feeling."

        # Save user input
        append_to_conversation(self.user_id, "user", user_input)

        # Load conversation history
        conversation_history = load_user_conversation(self.user_id)

        # Build prompt messages
        messages = [{"content": SYSTEM_PROMPT, "role": "system"}]
        messages.extend({
            "content": turn["content"],
            "role": turn["role"]
        } for turn in conversation_history)

        # Out of scope check
        if is_out_of_scope(user_input):
            self.logger.log_ethical_violation(self.user_id, "out_of_scope_query", user_input)
            return ("I'm here to support your mental wellbeing. Sorry—I can't answer questions about unrelated topics. Let's talk about your feelings and wellbeing.")

        # Crisis check
        crisis, crisis_type = self.safety_checker.check_for_crisis(user_input)
        if crisis:
            self.logger.log_crisis_detection(self.user_id, crisis_type, len(user_input))
            return ("I'm sensing you might be in crisis. Here are some resources that might help:\n[Show crisis_resources.json info here]")

        # Query LLM
        llm_response = query_gemini_with_messages(messages)

        # Ethics check
        ethics_result = self.safety_checker.validate_response(llm_response, user_input)
        if not ethics_result["is_ethical"]:
            self.logger.log_ethical_violation(self.user_id, "unsafe_response", str(ethics_result["issues"]))
            return "Sorry, I can't respond safely to that. Let's talk about your feelings."

        # Bias check
        bias_result = self.bias_detector.full_bias_check(llm_response)
        if not bias_result["passed_ethical_check"]:
            self.logger.log_bias_detection(str(bias_result["gender_bias"]["type"]), "high")
            return "Let's focus on your personal experiences—everyone's journey is unique."

        # Logging access
        self.logger.log_data_access(self.user_id, "read")

        # Save AI response
        append_to_conversation(self.user_id, "assistant", llm_response)

        return llm_response
