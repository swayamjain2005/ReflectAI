import solara
import requests
import os
import uuid
from typing import List, Dict, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from core.therapy_engine_groq import TherapyEngine

# Mount FastAPI endpoints into the same Solara server process
try:
    from solara.server.fastapi import app as fastapi_app
except Exception:
    fastapi_app = FastAPI(title="ReflectAI API (embedded)")

load_dotenv()

# --- CONFIGURATION ---
_explicit_url = os.environ.get("FASTAPI_CHAT_URL")
_render_base = os.environ.get("RENDER_EXTERNAL_URL")
_port = os.environ.get("PORT", "7860")
USE_INTERNAL_BACKEND = os.environ.get("USE_INTERNAL_BACKEND", "1")
if _explicit_url:
    FASTAPI_CHAT_URL = _explicit_url
elif _render_base:
    FASTAPI_CHAT_URL = _render_base.rstrip("/") + "/chat"
else:
    FASTAPI_CHAT_URL = f"http://127.0.0.1:{_port}/chat"

# --- Embedded FastAPI routes ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@fastapi_app.get("/healthz")
def healthz():
    return {"status": "ok"}

@fastapi_app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message or not req.user_id:
        raise HTTPException(status_code=400, detail="user_id and message are required")
    try:
        engine = TherapyEngine(req.user_id)
        reply = engine.process(req.message)
        if not isinstance(reply, str) or not reply:
            raise ValueError("Empty response from engine")
        return ChatResponse(response=reply)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to process message: {exc}")

# --- STATE MANAGEMENT ---
class AppState:
    """Manages the application's global state using reactive variables."""
    is_authenticated: solara.Reactive[bool] = solara.Reactive(False)
    username: solara.Reactive[Optional[str]] = solara.Reactive(None)
    show_login_modal: solara.Reactive[bool] = solara.Reactive(True)
    session_id: solara.Reactive[str] = solara.Reactive(str(uuid.uuid4()))
    messages: solara.Reactive[List[Dict[str, str]]] = solara.Reactive([])
    loading: solara.Reactive[bool] = solara.Reactive(False)
    user_input: solara.Reactive[str] = solara.Reactive("")
    current_view: solara.Reactive[str] = solara.Reactive("chat")

state = AppState()

# --- UTILITY FUNCTIONS ---
def get_initial_greeting():
    return "Hello there. I'm ReflectAI, your digital wellness companion. I'm here to listen without judgment. How are you genuinely feeling today, and what's on your mind?"

def start_new_session():
    state.messages.value = []
    state.session_id.value = str(uuid.uuid4())
    greeting = get_initial_greeting()
    state.messages.value = [{"role": "assistant", "content": greeting}]

if not state.messages.value:
    start_new_session()

# --- CHAT LOGIC ---
def process_message():
    input_text = state.user_input.value.strip()
    if not input_text or state.loading.value:
        return

    state.messages.value = state.messages.value + [{"role": "user", "content": input_text}]
    state.user_input.value = ""
    state.loading.value = True

    try:
        if USE_INTERNAL_BACKEND == "1":
            engine = TherapyEngine(state.session_id.value)
            ai_response = engine.process(input_text)
            state.messages.value = state.messages.value + [{"role": "assistant", "content": ai_response}]
        else:
            payload = {"user_id": state.session_id.value, "message": input_text}
            response = requests.post(FASTAPI_CHAT_URL, json=payload, timeout=20)
            response.raise_for_status()
            ai_response = response.json().get("response", "Error: Received empty response from the AI.")
            state.messages.value = state.messages.value + [{"role": "assistant", "content": ai_response}]
    except requests.exceptions.RequestException as e:
        error_msg = f"⚠️ Connection error: {str(e)}"
        state.messages.value = state.messages.value + [{"role": "system", "content": error_msg}]
    except Exception as e:
        state.messages.value = state.messages.value + [{"role": "system", "content": f"⚠️ Error: {e}"}]
    finally:
        state.loading.value = False

# --- UI COMPONENTS ---
@solara.component
def ChatBubble(message: Dict[str, str], index: int):
    """Enhanced message bubble with improved styling."""
    role = message["role"]
    content = message["content"]
    is_user = role == "user"
    
    # Animation delay based on index
    animation_delay = min(index * 0.05, 0.3)
    
    bubble_style = {
        "max-width": "75%",
        "padding": "16px 20px",
        "border-radius": "18px",
        "margin": "10px 0",
        "word-wrap": "break-word",
        "font-size": "0.95rem",
        "line-height": "1.6",
        "animation": f"slideIn 0.3s ease-out {animation_delay}s both",
    }
    
    if is_user:
        bubble_style.update({
            "background": "linear-gradient(135deg, #FF7500 0%, #FF9500 100%)",
            "color": "white",
            "align-self": "flex-end",
            "margin-left": "auto",
            "box-shadow": "0 4px 12px rgba(255, 117, 0, 0.3)",
        })
    elif role == "system":
        bubble_style.update({
            "background": "#FEF2F2",
            "color": "#991B1B",
            "border": "1px solid #FCA5A5",
            "align-self": "center",
            "font-size": "0.85rem",
        })
    else:
        bubble_style.update({
            "background": "white",
            "color": "#1A202C",
            "align-self": "flex-start",
            "margin-right": "auto",
            "box-shadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
            "border": "1px solid #E2E8F0",
        })
    
    with solara.Column(style={"width": "100%"}):
        if role == "system":
            solara.Text(content, style=bubble_style)
        else:
            solara.Markdown(content, style=bubble_style)

@solara.component
def TypingIndicator():
    """Animated typing indicator."""
    with solara.Row(style={
        "padding": "16px 20px",
        "background": "white",
        "border-radius": "18px",
        "max-width": "75px",
        "box-shadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
        "border": "1px solid #E2E8F0",
    }):
        solara.HTML(unsafe_innerHTML="""
            <style>
                @keyframes bounce {
                    0%, 60%, 100% { transform: translateY(0); }
                    30% { transform: translateY(-8px); }
                }
                .dot {
                    width: 8px;
                    height: 8px;
                    margin: 0 3px;
                    background: #CBD5E0;
                    border-radius: 50%;
                    display: inline-block;
                    animation: bounce 1.4s infinite ease-in-out;
                }
                .dot:nth-child(1) { animation-delay: -0.32s; }
                .dot:nth-child(2) { animation-delay: -0.16s; }
            </style>
            <div style="display: flex; align-items: center;">
                <span class="dot"></span>
                <span class="dot"></span>
                <span class="dot"></span>
            </div>
        """)

@solara.component
def ChatInterface():
    """Enhanced chat interface with modern design."""
    
    # Auto-scroll effect
    scroll_ref = solara.use_ref(None)
    
    # Chat Display Area
    with solara.Card(
        elevation=0,
        style={
            "height": "calc(100vh - 280px)",
            "min-height": "400px",
            "overflow-y": "auto",
            "padding": "24px",
            "background": "linear-gradient(180deg, #F7FAFC 0%, #EDF2F7 100%)",
            "border-radius": "20px",
            "border": "1px solid #E2E8F0",
        }
    ):
        with solara.Column(align="stretch", gap="8px"):
            for idx, msg in enumerate(state.messages.value):
                ChatBubble(msg, idx)
            
            if state.loading.value:
                TypingIndicator()
    
    # Input Area with Enter key support
    with solara.Card(
        elevation=2,
        style={
            "padding": "16px",
            "background": "white",
            "border-radius": "20px",
            "margin-top": "16px",
            "border": "1px solid #E2E8F0",
        }
    ):
        with solara.Row(style={"align-items": "center", "gap": "12px"}):
            # Input Field
            with solara.Column(style={"flex": "1"}):
                solara.InputText(
                    label="",
                    value=state.user_input,
                    on_value=state.user_input.set,
                    placeholder="Type your message here... (Click Send button)",
                    disabled=state.loading.value,
                    continuous_update=True,
                    style={
                        "width": "100%",
                        "border-radius": "12px",
                        "border": "2px solid #E2E8F0",
                        "padding": "12px 16px",
                        "font-size": "0.95rem",
                        "transition": "border-color 0.2s",
                    }
                )
            
            # Send Button
            solara.Button(
                label="Send ➤" if not state.loading.value else "Sending...",
                on_click=process_message,
                disabled=state.loading.value,
                style={
                    "background": "linear-gradient(135deg, #4FD1C5 0%, #38B2AC 100%)" if not state.loading.value else "#CBD5E0",
                    "color": "white",
                    "border": "none",
                    "border-radius": "12px",
                    "padding": "12px 28px",
                    "font-weight": "600",
                    "cursor": "pointer" if not state.loading.value else "not-allowed",
                    "box-shadow": "0 4px 12px rgba(79, 209, 197, 0.3)" if not state.loading.value else "none",
                    "transition": "all 0.2s",
                    "min-width": "120px",
                }
            )

@solara.component
def StaticPage(title, content_markdown):
    """Enhanced static pages."""
    with solara.Card(
        elevation=0,
        style={
            "padding": "32px",
            "max-width": "900px",
            "margin": "0 auto",
            "background": "white",
            "border-radius": "20px",
            "border": "1px solid #E2E8F0",
        }
    ):
        solara.HTML(unsafe_innerHTML=f"<h1 style='color: #FF7500; font-size: 2.5rem; margin-bottom: 24px;'>{title}</h1>")
        solara.Markdown(content_markdown)
        solara.Button(
            "⬅ Back to Chat",
            on_click=lambda: state.current_view.set("chat"),
            style={
                "background": "#4299E1",
                "color": "white",
                "border-radius": "10px",
                "padding": "10px 20px",
                "margin-top": "24px",
            }
        )

@solara.component
def LoginModal():
    """Enhanced login modal with modern design."""
    temp_username: solara.Reactive[str] = solara.Reactive("")
    login_error: solara.Reactive[str] = solara.Reactive("")
    
    def handle_login():
        if not temp_username.value.strip():
            login_error.set("Please enter a username to continue")
            return
        state.username.set(temp_username.value.strip())
        state.is_authenticated.set(True)
        state.show_login_modal.set(False)
        start_new_session()

    with solara.Column(align="center", gap="20px"):
        solara.HTML(unsafe_innerHTML="""
            <div style="text-align: center;">
                <div style="font-size: 3rem; margin-bottom: 16px;">🧠</div>
                <h1 style="color: #FF7500; font-size: 2rem; margin: 0;">Welcome to ReflectAI</h1>
                <p style="color: #718096; margin-top: 8px;">Your compassionate wellness companion</p>
            </div>
        """)
        
        solara.InputText(
            label="Choose Your Username",
            value=temp_username,
            on_value=temp_username.set,
            placeholder="e.g., MindfulJourney123",
            style={"width": "100%", "font-size": "1rem"}
        )
        
        if login_error.value:
            solara.Error(login_error.value)
        
        solara.Button(
            "Start Your Journey",
            on_click=handle_login,
            style={
                "width": "100%",
                "background": "linear-gradient(135deg, #FF7500 0%, #FF9500 100%)",
                "color": "white",
                "border-radius": "12px",
                "padding": "14px",
                "font-size": "1rem",
                "font-weight": "600",
                "box-shadow": "0 4px 12px rgba(255, 117, 0, 0.3)",
            }
        )

# --- MAIN APP LAYOUT ---
@solara.component
def Page():
    # Global CSS for animations
    solara.HTML(unsafe_innerHTML="""
        <style>
            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            }
        </style>
    """)
    
    # Show Login Modal
    if state.show_login_modal.value:
        with solara.Div(style={
            "position": "fixed",
            "top": "0",
            "left": "0",
            "width": "100%",
            "height": "100%",
            "background": "rgba(0, 0, 0, 0.5)",
            "backdrop-filter": "blur(8px)",
            "z-index": "1000",
            "display": "flex",
            "align-items": "center",
            "justify-content": "center",
            "animation": "fadeIn 0.3s ease-out",
        }):
            with solara.Card(
                elevation=20,
                style={
                    "width": "450px",
                    "padding": "40px",
                    "background": "white",
                    "border-radius": "24px",
                    "animation": "slideIn 0.4s ease-out",
                }
            ):
                LoginModal()
        return

    # Sidebar
    with solara.Sidebar():
        with solara.Column(gap="16px"):
            solara.HTML(unsafe_innerHTML=f"""
                <div style="padding: 20px; background: linear-gradient(135deg, #1A202C 0%, #2D3748 100%); border-radius: 16px; color: white; text-align: center;">
                    <div style="font-size: 2rem; margin-bottom: 8px;">👤</div>
                    <div style="font-size: 1.1rem; font-weight: 600;">{state.username.value}</div>
                    <div style="font-size: 0.75rem; color: #A0AEC0; margin-top: 4px;">Session: {state.session_id.value[:8]}...</div>
                </div>
            """)
            
            solara.Button(
                "💬 New Conversation",
                on_click=start_new_session,
                style={
                    "width": "100%",
                    "background": "linear-gradient(135deg, #4299E1 0%, #3182CE 100%)",
                    "color": "white",
                    "border-radius": "12px",
                    "padding": "12px",
                    "font-weight": "600",
                }
            )
            
            solara.Button(
                "📄 Ethics & Safety",
                on_click=lambda: state.current_view.set("ethics"),
                style={"width": "100%", "border-radius": "12px", "padding": "12px"}
            )
            
            solara.Button(
                "ℹ️ About ReflectAI",
                on_click=lambda: state.current_view.set("about"),
                style={"width": "100%", "border-radius": "12px", "padding": "12px"}
            )

    # Main Content
    ethics_content = """
    ## Our Commitment to You

    ### 🔒 Your Privacy is Our Priority
    Your conversations are private and encrypted. We do not share your personal data with third parties.

    ### 🤝 Our Ethical Guidelines
    ReflectAI uses evidence-based techniques from CBT and Motivational Interviewing.
    - We offer guidance, not medical diagnosis
    - We maintain professional boundaries
    - We promote user autonomy and empowerment

    <div style="background: #FEEBCF; color: #9C4221; padding: 20px; border-radius: 12px; margin-top: 24px; border-left: 5px solid #FF7500;">
        <strong>🚨 Crisis Support</strong><br>
        If you're in crisis or having thoughts of self-harm, please contact emergency services or call 988 (US/Canada).
    </div>
    """
    
    about_content = """
    ## About ReflectAI

    ReflectAI is your compassionate digital wellness companion, designed to make supportive mental health conversations accessible to everyone.

    ### Our Mission
    We empower individuals on their wellness journey by providing:
    - **24/7 Availability**: Support whenever you need it
    - **Evidence-Based Approach**: Grounded in CBT and therapeutic principles
    - **Non-Judgmental Space**: A safe environment to explore your thoughts
    - **Privacy First**: Your conversations remain confidential

    ReflectAI is a supportive tool to complement, not replace, professional mental health care.
    """
    
    if state.current_view.value == "ethics":
        StaticPage(title="Ethics & Safety Guide", content_markdown=ethics_content)
    elif state.current_view.value == "about":
        StaticPage(title="About ReflectAI", content_markdown=about_content)
    else:
        with solara.Column(style={"padding": "24px", "max-width": "1200px", "margin": "0 auto"}, gap="16px"):
            solara.HTML(unsafe_innerHTML="""
                <div style="text-align: center; margin-bottom: 16px;">
                    <h1 style="color: #FF7500; font-size: 2.5rem; margin: 0; font-weight: 700;">🧠 ReflectAI</h1>
                    <p style="color: #718096; font-size: 1.1rem; margin-top: 8px;">Your compassionate digital wellness companion</p>
                </div>
            """)
            ChatInterface()