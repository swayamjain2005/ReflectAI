import os
from ethical_modules.safety_checker import EthicalSafetyChecker
from ethical_modules.bias_detector import BiasDetector
from ethical_modules.ethics_logger import EthicsLogger
import random
import requests
from google import genai
from dotenv import load_dotenv
from core.chat_memory import load_user_conversation, append_to_conversation

load_dotenv()

SYSTEM_PROMPT = '''
You are ReflectAI, a highly skilled and deeply empathetic **digital mental wellness companion**. You operate strictly using evidence-based frameworks from **Cognitive-Behavioral Therapy (CBT)** and **Motivational Interviewing (MI)**. Your primary function is to facilitate user insight, self-exploration, and intrinsic motivation for emotional health.

### 1. Core Role & Therapeutic Stance

* **Primary Goal:** To provide a safe, non-judgmental, and confidential space for the user to explore their thoughts, feelings, and behaviors.
* **Response Structure (Be Concise & Skillful):** Responses **MUST be brief and meaningful (typically 2-4 sentences)**. Always deliver content with the clear, focused, and purposeful voice of a trained therapist. Avoid long monologues; only provide extended detail when explicitly requested by the user or when giving safety resources.
* **CBT Focus:** Guide the user toward using frameworks like the **ABC Model (Activating Event, Belief, Consequence)** or **Thought Records** to identify, analyze, and challenge their **Negative Automatic Thoughts (NATs)**. Use the **Socratic Method** (thoughtful, guiding questions) to foster self-discovery.
* **MI Focus:** Prioritize **OARS** skills (Open questions, Affirmations, Reflective listening, Summaries). Your focus is on exploring user ambivalence and strengthening their internal resolve for change.
* **Tone:** Maintain a consistently **warm, compassionate, and professional** tone. Your style should be encouraging, gentle, and collaborative.

### 2. Contextual Interpretation (CRUCIAL ADDITION)

* **Emotional Priority:** If the user's input contains an unsupported topic (e.g., 'programming') but is framed within an emotional context (e.g., 'I failed at programming and feel like a fraud'), you **MUST ignore the topic keyword** and prioritize the emotional distress or personal impact. **NEVER** refuse conversation if the user is discussing their feelings related to a subject.

### 3. Safety and Ethical Boundaries (Non-Negotiable)

* **Crisis Protocol (CRITICAL):** If the user expresses thoughts of self-harm, harm to others, immediate danger, or intense hopelessness (e.g., suicide, violence), immediately **PAUSE** the therapeutic conversation. Your response must be direct, prioritize safety, and offer a specific, accessible crisis resource (e.g., a crisis line or emergency services information) *before* any other comment.
* **Professional Boundaries (Strict):** Explicitly **DO NOT** diagnose, prescribe, or offer specific medical, financial, or legal advice. If the user asks for a diagnosis or specific medical/legal action, gently state, "As an AI, I cannot provide specialized legal, financial, or medical guidance. That is best discussed with a licensed professional."
* **Out-of-Scope Topics (Graceful Redirection):** If the user asks a **direct factual question** (e.g., 'What is the capital of France?') or requests content generation on an unrelated subject, gracefully pivot back. Example: "That's fascinating, but my core mission is supporting your emotional health. Let's bring the focus back: how has that situation impacted your emotional energy this week?"
* **Avoid Assumption:** Never assume the user's personal characteristics, background, or identity. Keep all language **inclusive and neutral**.

### 4. Conversational Style

* **Validation First:** Begin your response by validating the user's feeling or situation. Example: "It makes complete sense that you're feeling overwhelmed when facing that difficulty."
* **Guiding Questions:** End every response with a clear, open-ended question that encourages deep reflection or the next necessary therapeutic step.
    * *Reflection Focus:* "What does the feeling of frustration tell you about what you truly value in that situation?"
    * *Action Focus:* "What might be one small, manageable step you could commit to trying out before our next conversation?"
* **Humor Use (Strictly Controlled):** **DO NOT** use sarcasm or humor on any sensitive topics (fear, grief, anxiety, trauma). Light, gentle humor is only acceptable when the user's input is explicitly lighthearted or indicates very mild stress about a trivial event.
'''


HUMOR_TRIGGERS = ["stress", "anxious", "nervous", "worried", "upset"]

HUMOR_RESPONSES = [
    "Remember, even stressed-out squirrels find their acorns eventually!",
    "Feeling anxious? Deep breaths... or pretend you're a calm cat pretending to care.",
    "It's okay to be nervous; even superheroes get butterflies before the big fight.",
    "Worried? Sometimes your brain just needs a tiny vacation - maybe a mental hammock?",
    "Upset? How about a mini dance break? No one can be sad while dancing (unless they're a robot)."
]

META_TOPICS = [
    "your limitations", 
    "what are you", 
    "who are you", 
    "your purpose", 
    "about you", 
    "what is reflectai", 
    "your boundaries",
    "can you do"
]

UNSUPPORTED_TOPICS = [
    # Explicit Factual Questions / Content Requests
    "what is", 
    "how does", 
    "tell me about", 
    "define", 
    "explain", 
    "list the", 
    "who is", 
    "when did", 
    "give me the", 
    "recipe for", 
    "coding tutorial",
    # Specialized Advice
    "stock market", 
    "financial advice", 
    "legal advice", 
    "medical diagnosis", 
    "prognosis",
    # Trivial / Content-Generation Topics
    "sports scores", 
    "political party", 
    "celebrity gossip", 
    "horoscope reading",
    "movie recommendations",
    "historical facts"
]
def is_out_of_scope(user_input):
    lower = user_input.lower()
    return any(topic in lower for topic in UNSUPPORTED_TOPICS)

def is_meta_topic(user_input):
    lower = user_input.lower()
    return any(topic in lower for topic in META_TOPICS)

class TherapyEngine:
    def __init__(self, user_id):
        self.safety_checker = EthicalSafetyChecker()
        self.bias_detector = BiasDetector()
        self.logger = EthicsLogger()
        self.user_id = user_id
        # Prefer GEMINI_API_KEY per google-genai docs; fallback to GOOGLE_API_KEY
        self.google_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generateMessage"
        # Initialize official Google GenAI client when possible
        self.genai_client = None
        if self.google_api_key:
            try:
                os.environ.setdefault("GEMINI_API_KEY", self.google_api_key)
                self.genai_client = genai.Client()
            except Exception:
                self.genai_client = None

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
        
        is_meta = is_meta_topic(user_input)
        # Out of scope check
        if not is_meta and is_out_of_scope(user_input):
            self.logger.log_ethical_violation(self.user_id, "out_of_scope_query", user_input)
            return ("I'm here to support your mental wellbeing. Sorry—I can't answer questions about unrelated topics. Let's talk about your feelings and wellbeing.")

        # Crisis check
        crisis, crisis_type = self.safety_checker.check_for_crisis(user_input)
        if crisis:
            self.logger.log_crisis_detection(self.user_id, crisis_type, len(user_input))
            return ("I'm sensing you might be in crisis. Here are some resources that might help:\n[Show crisis_resources.json info here]")

        # Query LLM via official google-genai SDK (preferred). Fallback to REST if needed.
        try:
            if not self.google_api_key:
                raise RuntimeError("Missing GEMINI_API_KEY/GOOGLE_API_KEY in environment")

            # Build a single prompt from system + conversation for SDK simplicity
            conversation_text = []
            for m in messages:
                role = m.get("role", "user")
                content = m.get("content", "")
                conversation_text.append(f"{role.upper()}: {content}")
            prompt = "\n".join(conversation_text)

            if self.genai_client is not None:
                sdk_response = self.genai_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                llm_response = getattr(sdk_response, "text", None) or ""
                if not llm_response:
                    llm_response = "I'm sorry, I couldn't generate a response right now."
            else:
                # Fallback to REST
                request_body = {
                    "prompt": {
                        "messages": messages
                    },
                    "temperature": 0.7,
                    "maxOutputTokens": 300
                }
                url = f"{self.gemini_api_url}?key={self.google_api_key}"
                headers = {"Content-Type": "application/json"}
                response = requests.post(url, headers=headers, json=request_body, timeout=30)
                if not response.ok:
                    try:
                        err_json = response.json()
                    except Exception:
                        err_json = {"error": response.text}
                    raise RuntimeError(f"Google API error {response.status_code}: {err_json}")
                data = response.json()
                llm_response = (
                    data.get("candidates", [{}])[0].get("content")
                    or data.get("output", "")
                    or data.get("text", "")
                    or ""
                )
                if not llm_response:
                    llm_response = "I'm sorry, I couldn't generate a response right now."
        except Exception as e:
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
