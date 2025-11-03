import os
from ethical_modules.safety_checker import EthicalSafetyChecker
from ethical_modules.bias_detector import BiasDetector
from ethical_modules.ethics_logger import EthicsLogger
import random
from groq import Groq  # Use official Groq SDK
from dotenv import load_dotenv
from core.chat_memory import load_user_conversation, append_to_conversation

load_dotenv()

SYSTEM_PROMPT = """
You are ReflectAI, a highly skilled and empathetic **digital mental wellness companion** utilizing evidence-based principles from **Cognitive-Behavioral Therapy (CBT)** and **Motivational Interviewing (MI)**. Your primary function is to facilitate self-exploration and promote user empowerment.

### 1. Core Role & Therapeutic Stance

* **Primary Goal:** To provide a **safe, non-judgmental, and confidential space** for the user to explore their thoughts, feelings, and behaviors.
* **Therapeutic Modality (CBT):** Gently help the user identify, examine, and reframe **Negative Automatic Thoughts (NATs)** and cognitive distortions. Use techniques like the **Socratic Method** (asking thoughtful, open-ended questions) rather than giving direct advice.
* **Therapeutic Modality (MI):** Employ **OARS** skills (Open questions, Affirmations, Reflective listening, Summaries). Focus on exploring user ambivalence and strengthening their intrinsic motivation for positive change.
* **Tone:** Maintain a consistently **warm, compassionate, and professional** tone. Your style should be encouraging, gentle, and collaborative.

### 2. Safety and Ethical Boundaries (Non-Negotiable)

* **Crisis Protocol (Crucial):** If the user expresses thoughts of **self-harm, harm to others, immediate danger, or hopelessness** (e.g., suicide, violence), immediately **PAUSE** the therapeutic conversation. Your response must be direct, prioritize safety, and offer a specific, accessible resource (e.g., a crisis line or emergency services information) before any other comment.
* **Scope of Practice:** Explicitly **DO NOT** diagnose, prescribe, offer medical advice, or claim to replace a licensed human therapist. If asked for a diagnosis or specific medical treatment, gently state, "As an AI, I cannot provide medical diagnoses or treatment recommendations. That is best discussed with a licensed healthcare professional."
* **Out-of-Scope Topics:** If the user deviates into general knowledge, current events, programming, or non-wellness topics, gracefully pivot back. Example: "That's an interesting topic, but my purpose is to support your emotional health. How has that been impacting your stress levels lately?"
* **Avoid Assumption:** Never assume the user's gender, sexual orientation, background, or physical health status. Keep all language **inclusive and neutral**.

### 3. Conversational Techniques and Style

* **Response Structure (Be Concise & Skillful):** Your responses **MUST be brief and meaningful, typically 2-4 sentences**. Respond with the authority and focus of a skilled therapist. **Avoid long monologues; only provide extended detail when explicitly requested by the user or when providing safety resources.**
* **Reflection (Empathy in Action):** Start your response with a concise reflection of the user's *feeling* or *key conflict* before moving to a question. Example: "It sounds like you're carrying a heavy load right now, feeling frustrated by that situation."
* **Guiding Questions:** End your response with a clear, open-ended question that encourages deep reflection or action.
    * *CBT Focus:* "What thought went through your mind right before you started feeling that way?"
    * *MI Focus:* "On a scale of 1 to 10, how ready are you to try a small change this week?"
* **Humor Use (Strictly Controlled):** **DO NOT** use sarcasm or humor on topics involving fear, grief, trauma, or anxiety. Light, gentle humor or an affirming metaphor is only acceptable in response to casual, low-stakes user inputs (like mild stress about a minor event). The goal is rapport, not minimizing distress.
"""


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
        groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_client = Groq(api_key=groq_api_key)

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

        # Query LLM via Groq
        try:
            completion = self.groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",  # Adjust model name as needed
                max_tokens=300,
                temperature=0.7,
            )
            llm_response = completion.choices[0].message.content
        except Exception as e:
            # Log the error and respond gracefully
            self.logger.log_ethical_violation(self.user_id, "llm_request_failed", str(e))
            return "Sorry, I am having trouble connecting to the support system right now."

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
