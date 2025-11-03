import streamlit as st
import uuid
from datetime import datetime, timezone
from core.therapy_engine_groq import TherapyEngine
from core.chat_memory import load_user_conversation
from dotenv import load_dotenv
load_dotenv()  # Make sure this is at the top of your app.py
import os



st.set_page_config(
    page_title="ReflectAI - Digital Therapist",
    page_icon="🖤",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def apply_custom_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    /* Hide Streamlit defaults */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }

    .main-header {
        background: linear-gradient(135deg, #FF7500 0%, #FFB347 100%);
        padding: 1rem 2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        text-align: center;
        box-shadow: 0 5px 12px rgba(255, 117, 0, 0.6);
    }

    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header p {
        color: #FFE5B4;
        margin-top: 0.4rem;
        font-size: 1rem;
    }

    .chat-container {
        background: #1E1E1E;
        border-radius: 15px;
        padding: 1rem 1.5rem;
        max-height: 550px;
        overflow-y: auto;
        margin-bottom: 1.5rem;
        box-shadow: 0 0 10px rgba(255, 119, 0, 0.22);
        scroll-behavior: smooth;
    }

    .chat-container::-webkit-scrollbar {
        width: 7px;
    }

    .chat-container::-webkit-scrollbar-track {
        background: #121212;
        border-radius: 10px;
    }

    .chat-container::-webkit-scrollbar-thumb {
        background: #FF7500;
        border-radius: 10px;
    }

    .chat-container::-webkit-scrollbar-thumb:hover {
        background: #FFB347;
    }

    .message {
        max-width: 75%;
        margin: 12px 0;
        padding: 11px 15px;
        border-radius: 20px;
        line-height: 1.5;
        animation: fadeIn 0.3s ease;
        word-wrap: break-word;
        font-size: 0.95rem;
    }

    @keyframes fadeIn {
        from {opacity: 0; transform: translateY(5px);}
        to {opacity: 1; transform: translateY(0);}
    }

    .user-message {
        background: linear-gradient(135deg, #FF7500 0%, #FFB347 100%);
        color: #FFF;
        margin-left: auto;
        text-align: right;
        box-shadow: 0 4px 10px rgba(255, 117, 0, 0.7);
    }

    .assistant-message {
        background: #2C2C2C;
        color: #E0E0E0;
        margin-right: auto;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
    }

    .message-label {
        font-size: 0.76rem;
        font-weight: 600;
        opacity: 0.65;
        margin-bottom: 3px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .timestamp {
        font-size: 0.65rem;
        opacity: 0.5;
        margin-top: 3px;
    }

    /* Button style inside form */
    .stButton > button {
        background: linear-gradient(135deg, #FF7500 0%, #FFB347 100%);
        color: #FFF;
        font-weight: 600;
        border-radius: 20px;
        padding: 8px 24px;
        font-size: 1rem;
        box-shadow: 0 4px 12px rgba(255, 117, 0, 0.6);
        border: none;
        transition: all 0.3s ease;
        cursor: pointer;
        width: 100%;
    }

    .stButton > button:hover {
        box-shadow: 0 6px 16px rgba(255, 179, 71, 0.8);
        transform: translateY(-2px);
    }

    .stButton > button:active {
        transform: translateY(0);
    }

    /* Loading dots */
    .loading-dots {
        display: inline-block;
        padding: 12px;
    }

    .loading-dots span {
        display: inline-block;
        width: 7px;
        height: 7px;
        margin: 0 3px;
        background: #FF7500;
        border-radius: 50%;
        animation: bounce 1.4s infinite ease-in-out both;
    }

    .loading-dots span:nth-child(1) { animation-delay: -0.32s; }
    .loading-dots span:nth-child(2) { animation-delay: -0.16s; }

    @keyframes bounce {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }

    /* Session info */
    .session-info {
        text-align: center;
        padding: 1rem;
        color: #888;
        font-size: 0.8rem;
        font-family: monospace;
        user-select: all;
    }

    /* Responsive */
    @media (max-width: 768px) {
        .chat-container {
            max-height: 400px;
        }
        .message {
            max-width: 90%;
            font-size: 0.9rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = str(uuid.uuid4())
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    if 'engine' not in st.session_state:
        st.session_state['engine'] = TherapyEngine(st.session_state['user_id'])
    if 'loading' not in st.session_state:
        st.session_state['loading'] = False

def load_conversation_history():
    try:
        if not st.session_state['messages']:
            history = load_user_conversation(st.session_state['user_id'])
            st.session_state['messages'] = history if history else []
    except Exception as e:
        st.error(f"Error loading conversation: {str(e)}")


def format_time(timestamp_str):
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime("%I:%M %p")
    except:
        return ""

def display_messages():
    if not st.session_state['messages']:
        st.markdown("""
        <div style="text-align: center; color: #777; margin-top: 3rem;">
            <h3>Welcome to ReflectAI</h3>
            <p>I'm here to listen and support you. How are you feeling today?</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state['messages']:
            role = msg.get('role', 'assistant')
            content = msg.get('content', '[No content available]')
            timestamp = msg.get('timestamp', '')
            label = "You" if role=="user" else "ReflectAI"
            css_class = "user-message" if role=="user" else "assistant-message"

            st.markdown(f"""
            <div class="message {css_class}">
                <div class="message-label">{label}</div>
                {content}
                <div class="timestamp">{format_time(timestamp)}</div>
            </div>
            """, unsafe_allow_html=True)

def process_message(user_input):
    if user_input and user_input.strip():
        st.session_state['loading'] = True
        st.session_state['messages'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

        try:
            response = st.session_state['engine'].process(user_input)
            if response:
                st.session_state['messages'].append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            else:
                st.error("Received empty response from the assistant.")
        except Exception as e:
            st.error(f"Error processing message: {str(e)}")

        st.session_state['loading'] = False
        # st.experimental_rerun()  # Force UI refresh to show new messages promptly

def main():
    apply_custom_css()
    init_session_state()
    if len(st.session_state['messages']) == 0:
        load_conversation_history()

    st.markdown("""
    <div class="main-header">
        <h1>🖤 ReflectAI</h1>
        <p>Your compassionate digital therapist</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        display_messages()
        if st.session_state['loading']:
            st.markdown("""
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Use form for input which clears input on submit automatically
    with st.form(key="input_form", clear_on_submit=True):
        user_input = st.text_input(
            "", placeholder="Share what's on your mind...",
            label_visibility="collapsed",
            disabled=st.session_state['loading']
        )
        send_button = st.form_submit_button("Send")

        if send_button and user_input.strip():
            process_message(user_input)
            st.rerun()

    st.markdown(f"""
    <div class="session-info">
        Session ID: {st.session_state['user_id'][:8]}... | Your conversations are private and secure
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
