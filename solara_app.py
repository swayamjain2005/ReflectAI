import solara
import requests
import os
import uuid
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# NOTE: Replace this with the URL of your deployed FastAPI backend (e.g., on Render)
# Fallback to localhost for local development to avoid None URL
FASTAPI_CHAT_URL = os.environ.get("FASTAPI_CHAT_URL") or "http://localhost:8765/chat"

# --- MOCK AUTHENTICATION & STATE ---
# In a real app, this state would be managed by Supabase/WeWeb
class AppState:
    """Manages the application's global state using reactive variables."""
    # Auth State
    is_authenticated: solara.Reactive[bool] = solara.Reactive(False)
    username: solara.Reactive[Optional[str]] = solara.Reactive(None)
    show_login_modal: solara.Reactive[bool] = solara.Reactive(True)
    
    # Chat State
    session_id: solara.Reactive[str] = solara.Reactive(str(uuid.uuid4()))
    messages: solara.Reactive[List[Dict[str, str]]] = solara.Reactive([])
    loading: solara.Reactive[bool] = solara.Reactive(False)
    user_input: solara.Reactive[str] = solara.Reactive("")
    current_view: solara.Reactive[str] = solara.Reactive("chat")

state = AppState()

# --- UTILITY FUNCTIONS ---

def get_initial_greeting():
    """Initial greeting for a new or first-time chat."""
    return "Hello there. I'm ReflectAI, your digital wellness companion. I'm here to listen without judgment. How are you genuinely feeling today, and what's on your mind?"

def start_new_session():
    """Resets the chat state for a new session."""
    state.messages.value = []
    state.session_id.value = str(uuid.uuid4())
    
    # Add the initial greeting
    greeting = get_initial_greeting()
    state.messages.value = [{"role": "assistant", "content": greeting}]

# Initialize chat on first load or manual reset
if not state.messages.value:
    start_new_session()

# --- CHAT LOGIC ---

def process_message():
    """Handles message sending and API call (triggered by button or enter)."""
    input_text = state.user_input.value.strip()

    if not input_text or state.loading.value:
        return

    # 1. Add User Message
    state.messages.value = state.messages.value + [{"role": "user", "content": input_text}]
    state.user_input.value = ""  # Clear input box
    state.loading.value = True

    try:
        # NOTE: This is where you would integrate REAL Supabase token/ID.
        # For this example, we use a mock session_id for continuity.
        
        # 2. Prepare the payload for the FastAPI Backend
        payload = {
            "user_id": state.session_id.value,
            "message": input_text,
            # In production, you would add an auth token here
            # "token": "your_user_jwt" 
        }

        # 3. Call the FastAPI Backend
        response = requests.post(FASTAPI_CHAT_URL, json=payload, timeout=20)
        response.raise_for_status()
        
        # 4. Extract and Add AI Response
        ai_response = response.json().get("response", "Error: Received empty response from the AI.")
        state.messages.value = state.messages.value + [{"role": "assistant", "content": ai_response}]

    except requests.exceptions.RequestException as e:
        error_msg = f"API Error. Please check if your FastAPI backend is running at {FASTAPI_CHAT_URL}. Details: {e}"
        state.messages.value = state.messages.value + [{"role": "system", "content": error_msg}]
    except Exception as e:
        state.messages.value = state.messages.value + [{"role": "system", "content": f"An unexpected error occurred: {e}"}]
    finally:
        state.loading.value = False

# --- UI COMPONENTS ---

@solara.component
def SeparatorLine():
    """Custom component to reliably render a horizontal divider."""
    solara.Div(
        style={
            "width": "100%",
            "height": "1px",
            "background-color": "#e0e0e0",
            "margin": "10px 0"
        }
    )

@solara.component
def ChatBubble(message: Dict[str, str]):
    """A single message bubble with style based on role."""
    role = message["role"]
    content = message["content"]
    
    is_user = role == "user"
    
    # Tailwind/Material-like styling for Solara components
    style_common = {
        "max-width": "70%",
        "padding": "12px 18px",
        "border-radius": "20px",
        "margin": "8px 0",
        "word-wrap": "break-word",
        "box-shadow": "0 2px 4px rgba(0,0,0,0.1)",
        "font-size": "0.95rem",
    }
    
    if is_user:
        style = {
            **style_common,
            "background-color": "#FF7500",  # Primary Orange
            "color": "white",
            "align-self": "flex-end",
            "margin-left": "auto",
        }
    else:
        style = {
            **style_common,
            "background-color": "#E0E0E0",  # Light Grey
            "color": "#2D3748", # Dark Text
            "align-self": "flex-start",
            "margin-right": "auto",
        }
        
    solara.Markdown(content, style=style)

@solara.component
def ChatInterface():
    """Renders the main chat view."""
    
    # Chat Display Area
    with solara.Card(
        elevation=2, 
        style={"height": "70vh", "overflow-y": "auto", "padding": "15px", "flex-grow": 1}
    ):
        with solara.Column(align="stretch"):
            for msg in state.messages.value:
                ChatBubble(msg)
            
            if state.loading.value:
                solara.ProgressLinear(color="#FF7500")
                solara.Text("ReflectAI is thinking...", style={"color": "#FF7500"})

    # Input Area with Enter key support
    def handle_input_change(value):
        # Check if Enter was pressed (value contains newline)
        if '\n' in value and not state.loading.value:
            # Remove the newline and process
            clean_value = value.replace('\n', '').strip()
            if clean_value:
                state.user_input.value = clean_value
                process_message()
        else:
            state.user_input.value = value
    
    with solara.Row(style={"width": "100%", "align-items": "center", "display": "flex"}):
        # Input Field
        solara.InputText(
            label="",
            value=state.user_input,
            on_value=handle_input_change,
            placeholder="Share what's on your mind... (Press Enter to send)",
            disabled=state.loading.value,
            style={"flex-grow": "1", "border-radius": "20px"}
        )
        
        # Send Button
        solara.Button(
            label="Send",
            on_click=process_message,
            color="#4FD1C5", # Teal accent
            disabled=state.loading.value or not state.user_input.value.strip(),
            style={"border-radius": "20px", "padding": "10px 20px"}
        )

@solara.component
def StaticPage(title, content_markdown):
    """Template for static pages (Ethics, About)."""
    with solara.Column(style={"padding": "20px", "max-width": "800px"}):
        solara.Title(title)
        solara.Markdown(content_markdown)
        solara.Button("⬅ Back to Chat", on_click=lambda: state.current_view.set("chat"), color="secondary")

@solara.component
def LoginModal():
    """Modal component to capture username and simulate login."""
    
    temp_username: solara.Reactive[str] = solara.Reactive("")
    login_error: solara.Reactive[str] = solara.Reactive("")
    
    def handle_login():
        if not temp_username.value.strip():
            login_error.set("Please enter a username to start your session.")
            return

        # --- MOCK LOGIN SUCCESS ---
        # In production, this would be a full Supabase sign-in, 
        # and on success, you would store the JWT/user_id/username
        
        state.username.set(temp_username.value.strip())
        state.is_authenticated.set(True)
        state.show_login_modal.set(False)
        start_new_session() # Start chat with greeting

    with solara.Column(align="center"):
        solara.Markdown("# 🤝 Welcome to ReflectAI")
        solara.Markdown("To ensure your conversation history is saved and optimized, please create a unique username. (This simulates logging in to a persistent account.)")
        
        solara.InputText(
            label="Choose Your Username",
            value=temp_username,
            on_value=temp_username.set,
            placeholder="e.g., WellnessExplorer99",
            style={"width": "100%"}
        )
        
        if login_error.value:
            solara.Error(login_error.value)
            
        solara.Button("Start Session", on_click=handle_login, color="#FF7500", style={"margin-top": "20px"})
        
# --- MAIN APP LAYOUT ---

@solara.component
def Page():
    # Show Login Modal if not authenticated
    if state.show_login_modal.value:
        # FIX: Converted the style list back into a single Python dictionary for solara.Div
        with solara.Div(
            style={
                "position": "fixed", 
                "top": "0", 
                "left": "0", 
                "width": "100%", 
                "height": "100%", 
                "background": "rgba(0,0,0,0.6)", 
                "z-index": "1000", 
                "display": "flex", 
                "align-items": "center", 
                "justify-content": "center"
            }
        ):
            with solara.Card(elevation=20, style={"width": "400px", "padding": "20px", "background": "white"}):
                LoginModal()
        return

    # --- Sidebar Navigation ---
    with solara.Sidebar(): # FIX: Removed style keyword argument
        solara.Markdown(f"**Hello, {state.username.value}**", style={"padding": "10px"})
        SeparatorLine() # Using the new robust component
        
        solara.Button("💬 Start New Chat", on_click=start_new_session, color="secondary", style={"width": "100%", "margin-bottom": "10px"})
        SeparatorLine() # Using the new robust component
        
        solara.Button("📄 Ethics & Safety Guide", on_click=lambda: state.current_view.set("ethics"), color="secondary", style={"width": "100%", "margin-bottom": "10px"})
        solara.Button("🖤 About ReflectAI", on_click=lambda: state.current_view.set("about"), color="secondary", style={"width": "100%", "margin-bottom": "10px"})
        SeparatorLine() # Using the new robust component
        
        solara.Text(f"Session ID: {state.session_id.value[:8]}...")
        solara.Text(f"User: {state.username.value}", style={"font-size": "0.8em"})

    # --- Main Content Renderer ---
    
    # Define Content for Static Pages
    ethics_content = """
    ## Our Commitment to You

    ### Your Privacy is Our Priority
    Your conversations are private and encrypted. We do not share your personal data with third parties. All chat history is securely stored and linked only to your permanent user account (Username/ID).

    ### Our Ethical Guidelines
    ReflectAI is built on principles of compassion, non-judgment, and support, utilizing techniques from CBT and Motivational Interviewing.
    - We offer guidance, not diagnosis or medical advice.
    - We maintain professional boundaries and will redirect conversations that go out of scope.
    - We ensure responses are balanced, empathetic, and promote user autonomy.

    <div style="background: #FEEBCF; color: #9C4221; padding: 15px; border-radius: 8px; margin-top: 20px; border-left: 5px solid #FF7500;">
        **🚨 Crisis Support: Immediate Attention Required**
        <p>If you are in immediate crisis, have thoughts of self-harm, or are in danger, please do not use this app. Contact your local emergency services or a dedicated crisis hotline immediately.</p>
        <p><strong>Example Crisis Hotline:</strong> Call or text 988 (US/Canada)</p>
    </div>
    """
    
    about_content = """
    ## About ReflectAI
    Our mission is to make supportive mental health conversations accessible and safe for everyone. ReflectAI is a supportive tool designed to help you explore your thoughts, navigate complex emotions, and find moments of peace. We are a digital companion, dedicated to empowering you on your wellness journey by applying proven therapeutic frameworks without the barriers of cost or scheduling.
    """
    
    # Render the current view
    if state.current_view.value == "ethics":
        StaticPage(title="Ethics & Safety Guide", content_markdown=ethics_content)
    elif state.current_view.value == "about":
        StaticPage(title="About ReflectAI", content_markdown=about_content)
    else:
        # Chat View
        with solara.Column(style={"padding": "20px"}, gap="15px", align="stretch"):
            solara.Markdown(f"# 🖤 ReflectAI", style={"color": "#FF7500", "font-weight": "700"})
            solara.Markdown("Your compassionate digital wellness companion", style={"margin-bottom": "20px"})
            ChatInterface()
