import streamlit as st
from rag.graph import app
from dotenv import load_dotenv
import time

load_dotenv()

# Page config
st.set_page_config(
    page_title="RAG Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dark theme with grain texture
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles - Dark theme */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }
    
    html, body {
        margin: 0;
        padding: 0;
        overflow: hidden;
    }
    
    .main {
        padding: 0;
        margin: 0;
        background: #0a0a0a;
        height: 100vh;
        overflow: hidden;
    }
    
    .stApp {
        background: #0a0a0a;
        background-image: 
            radial-gradient(circle at 20% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.4'/%3E%3C/svg%3E");
    }
    
    .block-container {
        padding: 0;
        margin: 0;
        max-width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        overflow: hidden;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Minimal header - removed */
    
    /* Chat container - responsive, centered */
    .chat-container {
        max-width: 768px;
        width: 100%;
        margin: 0 auto;
        padding: 1rem 1.5rem 100px 1.5rem;
        display: flex;
        flex-direction: column;
        flex: 1;
        overflow-y: auto;
        box-sizing: border-box;
        position: relative;
    }
    
    @media (max-width: 768px) {
        .chat-container {
            padding-bottom: 90px;
        }
    }
    
    @media (max-width: 480px) {
        .chat-container {
            padding-bottom: 85px;
        }
    }
    
    /* When messages exist, move input to bottom */
    .has-messages.input-wrapper {
        position: fixed;
        bottom: 0;
        top: auto;
        left: 0;
        right: 0;
        transform: none;
        background: #0a0a0a;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.25rem 0;
        width: 100vw;
        max-width: 100%;
    }
    
    .has-messages .input-inner {
        max-width: 500px;
        padding: 0 3rem;
    }
    
    @media (max-width: 768px) {
        .has-messages .input-inner {
            max-width: 85%;
            padding: 0 2rem;
        }
    }
    
    @media (max-width: 480px) {
        .has-messages .input-inner {
            max-width: 90%;
            padding: 0 1.5rem;
        }
    }
    
    /* Empty state - Grok-style positioning (heading at 1/3 from top) */
    .empty-state {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-start;
        width: 100%;
        max-width: 768px;
        text-align: center;
        padding: 0;
        box-sizing: border-box;
        position: absolute;
        top: 30%;
        left: 50%;
        transform: translate(-50%, -30%);
        margin: 0;
    }
    
    @media (max-width: 768px) {
        .empty-state {
            top: 25%;
            transform: translate(-50%, -25%);
            max-width: 100%;
            padding: 0 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .empty-state {
            top: 20%;
            transform: translate(-50%, -20%);
            padding: 0 0.75rem;
        }
    }
    
    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1;
    }
    
    .empty-state-title {
        font-size: 2rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 2rem;
        font-family: 'Inter', sans-serif;
        letter-spacing: -0.02em;
    }
    
    .empty-state-subtitle {
        display: none;
    }
    
    @media (max-width: 768px) {
        .empty-state-icon {
            font-size: 2.5rem;
            margin-bottom: 1.25rem;
        }
        
        .empty-state-title {
            font-size: 1.75rem;
            margin-bottom: 1.5rem;
        }
    }
    
    @media (max-width: 480px) {
        .empty-state-icon {
            font-size: 2rem;
            margin-bottom: 1rem;
        }
        
        .empty-state-title {
            font-size: 1.5rem;
            margin-bottom: 1.25rem;
        }
    }
    
    /* Message wrapper - centered container */
    .message-wrapper {
        display: flex;
        width: 100%;
        max-width: 768px;
        margin: 0 auto 1rem auto;
        box-sizing: border-box;
    }
    
    .message-wrapper.user {
        justify-content: flex-end;
    }
    
    .message-wrapper.assistant {
        justify-content: flex-start;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: #ffffff;
        padding: 0.9rem 1.2rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0;
        max-width: 75%;
        min-width: 80px;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        animation: slideInRight 0.3s ease-out;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        line-height: 1.5;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .assistant-message {
        background: rgba(255, 255, 255, 0.05);
        color: #e5e7eb;
        padding: 1rem 1.3rem;
        border-radius: 16px 16px 16px 4px;
        margin: 0;
        max-width: 75%;
        min-width: 80px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        animation: slideInLeft 0.3s ease-out;
        line-height: 1.6;
        word-wrap: break-word;
        font-family: 'Inter', sans-serif;
        font-weight: 400;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    
    .assistant-message p {
        margin: 0.5rem 0;
    }
    
    .assistant-message p:first-child {
        margin-top: 0;
    }
    
    .assistant-message p:last-child {
        margin-bottom: 0;
    }
    
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    /* Input area */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #e5e7eb;
        padding: 1.5rem;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
    }
    
    /* Input container - Grok-style positioning (below heading, centered) */
    .input-wrapper {
        position: fixed;
        bottom: auto;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 100%;
        max-width: 500px;
        background: transparent;
        border: none;
        padding: 0 3rem;
        z-index: 100;
        display: flex;
        justify-content: center;
        align-items: center;
        box-sizing: border-box;
        margin: 0;
    }
    
    @media (max-width: 768px) {
        .input-wrapper {
            max-width: 85%;
            padding: 0 2rem;
        }
    }
    
    @media (max-width: 480px) {
        .input-wrapper {
            max-width: 90%;
            padding: 0 1.5rem;
        }
    }
    
    .input-inner {
        max-width: 500px;
        width: 100%;
        margin: 0 auto;
        padding: 0 3rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-sizing: border-box;
    }
    
    @media (max-width: 768px) {
        .input-inner {
            max-width: 85%;
            padding: 0 2rem;
        }
    }
    
    @media (max-width: 480px) {
        .input-inner {
            max-width: 90%;
            padding: 0 1.5rem;
        }
    }
    
    .stTextInput > div > div > input {
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.1rem 1.5rem;
        min-height: 52px;
        font-size: 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s;
        background: rgba(255, 255, 255, 0.1);
        color: #e5e7eb;
        backdrop-filter: blur(20px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
        width: 100%;
        box-sizing: border-box;
        line-height: 1.5;
    }
    
    @media (max-width: 768px) {
        .stTextInput > div > div > input {
            padding: 1rem 1.25rem;
            min-height: 50px;
            font-size: 0.95rem;
        }
    }
    
    @media (max-width: 480px) {
        .stTextInput > div > div > input {
            padding: 0.95rem 1.1rem;
            min-height: 48px;
            font-size: 0.9rem;
        }
    }
    
    .stTextInput > div > div > input:focus {
        border-color: rgba(139, 92, 246, 0.5);
        box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2), 0 4px 16px rgba(0, 0, 0, 0.3);
        outline: none;
        background: rgba(255, 255, 255, 0.1);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: #6b7280;
    }
    
    /* Send button inside input */
    .input-button-wrapper {
        position: relative;
    }
    
    .send-button-absolute {
        position: absolute;
        right: 0.5rem;
        top: 50%;
        transform: translateY(-50%);
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        border: none;
        border-radius: 16px;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s;
        z-index: 10;
    }
    
    .send-button-absolute:hover {
        transform: translateY(-50%) scale(1.05);
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 0.5rem;
        font-weight: 600;
        font-size: 1rem;
        font-family: 'Inter', sans-serif;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
        min-width: 52px;
        width: 52px;
        height: 52px;
        flex-shrink: 0;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
    }
    
    @media (max-width: 768px) {
        .stButton > button {
            min-width: 50px;
            width: 50px;
            height: 50px;
        }
    }
    
    @media (max-width: 480px) {
        .stButton > button {
            min-width: 48px;
            width: 48px;
            height: 48px;
        }
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .chat-container {
            padding: 0.75rem 1rem;
        }
        
        .empty-state {
            min-height: calc(100vh - 180px);
            padding: 1.5rem 1rem;
        }
        
        .empty-state-icon {
            font-size: 2rem;
            margin-bottom: 0.75rem;
        }
        
        .empty-state-title {
            font-size: 1.25rem;
        }
        
        .empty-state-subtitle {
            font-size: 0.85rem;
            max-width: 100%;
        }
        
        .input-inner {
            padding: 0 1rem;
        }
        
        .input-wrapper {
            padding: 1rem 0;
        }
        
        .user-message, .assistant-message {
            max-width: 85%;
        }
        
        .stTextInput > div > div > input {
            font-size: 0.9rem;
            padding: 0.85rem 1.25rem;
        }
        
        .stButton > button {
            min-width: 40px;
            width: 40px;
            height: 40px;
            font-size: 0.9rem;
        }
    }
    
    @media (max-width: 480px) {
        .chat-container {
            padding: 0.5rem 0.75rem;
        }
        
        .empty-state {
            min-height: calc(100vh - 160px);
            padding: 1rem 0.75rem;
        }
        
        .empty-state-icon {
            font-size: 1.75rem;
            margin-bottom: 0.5rem;
        }
        
        .empty-state-title {
            font-size: 1.1rem;
        }
        
        .empty-state-subtitle {
            font-size: 0.8rem;
        }
        
        .input-inner {
            padding: 0 0.75rem;
            gap: 0.25rem;
        }
        
        .input-wrapper {
            padding: 0.75rem 0;
        }
        
        .user-message, .assistant-message {
            max-width: 90%;
            padding: 0.75rem 1rem;
            font-size: 0.9rem;
        }
        
        .stTextInput > div > div > input {
            font-size: 0.85rem;
            padding: 0.75rem 1rem;
        }
        
        .stButton > button {
            min-width: 36px;
            width: 36px;
            height: 36px;
            font-size: 0.85rem;
        }
    }
    
    @media (min-width: 769px) and (max-width: 1024px) {
        .chat-container {
            max-width: 700px;
        }
        
        .input-wrapper {
            max-width: 700px;
        }
        
        .message-wrapper {
            max-width: 700px;
        }
    }
    
    @media (min-width: 1025px) {
        .chat-container {
            max-width: 768px;
        }
        
        .input-wrapper {
            max-width: 768px;
        }
        
        .message-wrapper {
            max-width: 768px;
        }
    }
    
    /* Secondary button (clear) */
    .stButton > button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.1);
        color: #e5e7eb;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-1px);
    }
    
    /* Loading animation */
    .loading-dots {
        display: inline-block;
    }
    
    .loading-dots::after {
        content: '...';
        animation: dots 1.5s steps(4, end) infinite;
    }
    
    @keyframes dots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60%, 100% { content: '...'; }
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        background: rgba(139, 92, 246, 0.2);
        color: #c4b5fd;
        padding: 0.4rem 0.9rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 500;
        font-family: 'Inter', sans-serif;
        margin-bottom: 1rem;
        border: 1px solid rgba(139, 92, 246, 0.3);
        backdrop-filter: blur(10px);
    }
    
    /* Removed tech badges */
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# Minimal header - just clear button (positioned absolutely, responsive)
st.markdown("""
<style>
.clear-btn-container {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 200;
    }
    
    @media (max-width: 768px) {
        .clear-btn-container {
            top: 0.75rem;
            right: 0.75rem;
        }
    }
    
    @media (max-width: 480px) {
        .clear-btn-container {
            top: 0.5rem;
            right: 0.5rem;
        }
    }
</style>
<div class="clear-btn-container">
""", unsafe_allow_html=True)

if st.button("🗑️", help="Clear chat", key="clear_btn"):
    st.session_state.messages = []
    st.session_state.processing = False
    st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Chat container
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Show empty state or messages
if not st.session_state.messages:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">✨</div>
        <div class="empty-state-title">RAG</div>
    </div>
    """, unsafe_allow_html=True)
else:
    for message in st.session_state.messages:
        role_class = "user" if message["role"] == "user" else "assistant"
        st.markdown(f'<div class="message-wrapper {role_class}">', unsafe_allow_html=True)
        
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
        else:
            content = message["content"].replace("\n", "\n\n")
            st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Close chat container
st.markdown("</div>", unsafe_allow_html=True)

# Fixed input area - Grok-style: centered when no messages, bottom when messages exist
input_wrapper_class = "input-wrapper has-messages" if st.session_state.messages else "input-wrapper"
st.markdown(f'<div class="{input_wrapper_class}">', unsafe_allow_html=True)
st.markdown('<div class="input-inner">', unsafe_allow_html=True)

# Centered input with send button - responsive columns
input_col1, input_col2 = st.columns([12, 1], gap="small")

with input_col1:
    query = st.text_input(
        "Message",
        value="",
        placeholder="Ask anything...",
        label_visibility="collapsed",
        key="query_input"
    )

with input_col2:
    submit_button = st.button("➤", type="primary", use_container_width=True, help="Send")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# Process query
if submit_button and query and not st.session_state.processing:
    st.session_state.processing = True
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": query})
    st.rerun()
    
elif st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.processing:
    # Process the last user message
    user_query = st.session_state.messages[-1]["content"]
    
    status_placeholder = st.empty()
    status_placeholder.markdown(
        '<div class="status-badge">🔄 Retrieving documents and generating answer<span class="loading-dots"></span></div>',
        unsafe_allow_html=True
    )
    
    try:
        # Run RAG pipeline
        result = app.invoke({"question": user_query})
        answer = result.get("answer", "I couldn't generate an answer.")
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.processing = False
        status_placeholder.empty()
        st.rerun()
        
    except Exception as e:
        error_message = f"❌ **Error:** {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.session_state.processing = False
        status_placeholder.empty()
        st.rerun()

elif submit_button and not query:
    pass  # Silent, no warning needed
