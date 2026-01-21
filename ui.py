import streamlit as st
from rag.graph import app
from rag.generate_ui import generate_answer_stream_ui
from dotenv import load_dotenv
import time
import re

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
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');
    
    /* Global styles - Dark theme */
    * {
        font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    }

    /* IMPORTANT: Don’t override icon fonts (prevents "arrow_drop_down" text showing) */
    .material-icons,
    .material-icons-outlined,
    .material-icons-round,
    .material-icons-sharp,
    .material-icons-two-tone,
    span[class*="material-icons"] {
        font-family: "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: "liga" !important;
        -webkit-font-smoothing: antialiased !important;
    }

    .material-symbols-outlined,
    .material-symbols-rounded,
    .material-symbols-sharp,
    span[class*="material-symbols"] {
        font-family: "Material Symbols Outlined", "Material Symbols Rounded", "Material Symbols Sharp", "Material Icons" !important;
        font-weight: normal !important;
        font-style: normal !important;
        letter-spacing: normal !important;
        text-transform: none !important;
        display: inline-block !important;
        white-space: nowrap !important;
        word-wrap: normal !important;
        direction: ltr !important;
        -webkit-font-feature-settings: "liga" !important;
        -webkit-font-smoothing: antialiased !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
    }

    /* Streamlit expander toggle icon (extra-specific) */
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary i {
        font-family: "Material Symbols Outlined", "Material Icons" !important;
        -webkit-font-feature-settings: "liga" !important;
        font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24 !important;
    }
    
    html, body {
        margin: 0;
        padding: 0;
        overflow: hidden;
    }

    /* Mobile/tablet: allow scrolling and prevent fixed elements overlap */
    @media (max-width: 768px) {
        html, body {
            overflow: auto;
        }
        .block-container {
            height: auto !important;
            min-height: 100vh !important;
            overflow-y: auto !important;
        }
        /* Reserve space for the fixed chat input */
        div[data-testid="stAppViewContainer"] > .main {
            padding-bottom: calc(120px + env(safe-area-inset-bottom)) !important;
        }
    }

    @media (max-width: 480px) {
        div[data-testid="stAppViewContainer"] > .main {
            padding-bottom: calc(140px + env(safe-area-inset-bottom)) !important;
        }
    }

    /* Ensure background covers ALL Streamlit root containers (prevents bottom band) */
    html, body,
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] > .main {
        height: 100% !important;
        background-color: #0a0a0a !important;
    }

    /* Apply the SAME background image once (prevents seams / color shifts) */
    div[data-testid="stAppViewContainer"],
    div[data-testid="stAppViewContainer"] > .main {
        background-image:
            radial-gradient(circle at 20% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.1) 0%, transparent 50%),
            url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.4'/%3E%3C/svg%3E") !important;
        background-repeat: repeat !important;
        background-attachment: fixed !important;
        background-position: center center !important;
    }

    /* Bottom container should be transparent so the same background shows through */
    div[data-testid="stBottomBlockContainer"] {
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    .main {
        padding: 0;
        margin: 0;
        height: 100vh;
        overflow: hidden;
    }
    
    .stApp {
        background: transparent;
    }
    
    .block-container {
        padding: 0;
        margin: 0;
        max-width: 100%;
        height: 100vh;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
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
        padding: 1rem 1.5rem 160px 1.5rem;
        display: flex;
        flex-direction: column;
        flex: 1;
        overflow-y: auto;
        box-sizing: border-box;
        position: relative;
    }
    
    @media (max-width: 768px) {
        .chat-container {
            padding-bottom: 150px;
        }
    }
    
    @media (max-width: 480px) {
        .chat-container {
            padding-bottom: 140px;
        }
    }
    
    /* Empty screen wrapper (prevents overlap) */
    .empty-screen {
        width: 100%;
        min-height: calc(100vh - 120px); /* leaves room for fixed input (closer gap) */
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        align-items: center;
        position: relative;
        padding: 1.75rem 1rem 0 1rem; /* top aligned (more breathing room) */
        box-sizing: border-box;
    }

    /* Hero (empty state) */
    .hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        width: 100%;
        max-width: 980px;
        text-align: center;
        padding: 0 1rem;
        box-sizing: border-box;
        position: relative;
        margin: 0 auto; /* top aligned, no negative offsets */
    }
    
    @media (max-width: 768px) {
        .hero {
            max-width: 100%;
            margin-top: 0;
        }
    }
    
    @media (max-width: 480px) {
        .hero {
            padding: 0 0.75rem;
            margin-top: 0;
        }
    }
    
    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.35rem 0.75rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #d1d5db;
        font-size: 0.85rem;
        font-weight: 500;
        backdrop-filter: blur(12px);
        margin-bottom: 1.25rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin: 0 0 1rem 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 100%;
    }
    
    .hero-title .grad {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .hero-subtitle {
        color: #9ca3af;
        font-size: 1rem;
        line-height: 1.6;
        max-width: 760px;
        margin: 0 0 0.6rem 0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* If subtitle is empty, remove its spacing entirely */
    .hero-subtitle:empty {
        display: none !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .hero-hints {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.65rem;
        width: 100%;
        max-width: 920px;
        margin-top: 1.4rem;
        align-items: stretch;
    }

    @media (max-width: 768px) {
        .hero-hints {
            grid-template-columns: 1fr;
        }
    }
    
    .hint {
        text-align: left;
        padding: 1.15rem 1.15rem;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.10);
        color: #e5e7eb;
        backdrop-filter: blur(10px);
    }
    
    .hint-title {
        font-size: 0.9rem;
        font-weight: 650;
        margin-bottom: 0.5rem;
        color: #f3f4f6;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .hint-desc {
        font-size: 0.85rem;
        color: #9ca3af;
        margin: 0;
        line-height: 1.5;
        /* Make long descriptions visible (no single-line truncation) */
        white-space: normal;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
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
        max-width: 920px;
        margin: 0 auto 1rem auto;
        padding: 0 1.25rem; /* left/right breathing room */
        box-sizing: border-box;
    }

    @media (max-width: 768px) {
        .message-wrapper {
            padding: 0 1rem;
        }
    }

    @media (max-width: 480px) {
        .message-wrapper {
            padding: 0 0.75rem;
        }
    }

    /* Shared content width so all 3 boxes are identical */
    :root {
        --content-w-desktop: 75%;
        --content-w-tablet: 92%;
        --content-w-mobile: 95%;
    }

    /* Mobile typography + spacing (desktop unchanged) */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.7rem;
        }
        .hero-badge {
            font-size: 0.8rem;
        }
        .hero-hints {
            gap: 0.6rem;
        }
        .hint {
            padding: 0.95rem 1rem;
        }
    }

    @media (max-width: 480px) {
        .hero-title {
            font-size: 1.45rem;
        }
        .hero-hints {
            gap: 0.55rem;
        }
        .hint {
            padding: 0.9rem 0.95rem;
        }
    }

    /* Expander wrapper: no extra padding that changes perceived width */
    div[data-testid="stExpander"] {
        margin: 0 auto 1rem auto;
        padding: 0 !important;
        box-sizing: border-box;
        position: relative;
        z-index: 200;
    }

    /* Remove Streamlit's icon text like "_arrow_right/_arrow_down" and draw our own caret */
    div[data-testid="stExpander"] details > summary::-webkit-details-marker {
        display: none !important;
    }
    div[data-testid="stExpander"] details > summary::marker {
        content: "" !important;
    }
    /* Streamlit usually renders the toggle icon as a direct <span> child of <summary> */
    div[data-testid="stExpander"] details > summary > span {
        display: none !important;
    }
    div[data-testid="stExpander"] details > summary {
        position: relative;
        padding-left: 1.1rem !important;
    }
    div[data-testid="stExpander"] details > summary::before {
        content: "▸";
        position: absolute;
        left: 0.25rem;
        top: 50%;
        transform: translateY(-50%);
        color: rgba(229, 231, 235, 0.85);
        font-size: 0.95rem;
        line-height: 1;
    }
    div[data-testid="stExpander"] details[open] > summary::before {
        content: "▾";
    }

    /* Mobile: ensure the expander header never overlaps */
    @media (max-width: 480px) {
        div[data-testid="stExpander"] details > summary {
            padding-left: 1.35rem !important;
        }
        div[data-testid="stExpander"] details > summary::before {
            left: 0.35rem;
        }
    }
    
    .message-wrapper.user {
        justify-content: center;
    }
    
    .message-wrapper.assistant {
        justify-content: center;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%);
        color: #ffffff;
        padding: 0.9rem 1.2rem;
        border-radius: 16px 16px 4px 16px;
        margin: 0;
        max-width: var(--content-w-desktop);
        min-width: 80px;
        text-align: left;
        width: var(--content-w-desktop);
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
        animation: slideInRight 0.3s ease-out;
        font-family: 'Montserrat', sans-serif;
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
        max-width: var(--content-w-desktop);
        min-width: 80px;
        text-align: left;
        width: var(--content-w-desktop);
        margin-left: auto;
        margin-right: auto;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        animation: slideInLeft 0.3s ease-out;
        line-height: 1.6;
        word-wrap: break-word;
        font-family: 'Montserrat', sans-serif;
        font-weight: 400;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }

    /* Make the visible expander (<details>) match bubble width exactly */
    div[data-testid="stExpander"] > details {
        width: var(--content-w-desktop) !important;
        max-width: var(--content-w-desktop) !important;
        margin-left: auto !important;
        margin-right: auto !important;
        box-sizing: border-box;
    }

    @media (max-width: 768px) {
        .user-message,
        .assistant-message,
        div[data-testid="stExpander"] > details {
            width: var(--content-w-tablet) !important;
            max-width: var(--content-w-tablet) !important;
        }
    }

    @media (max-width: 480px) {
        .user-message,
        .assistant-message,
        div[data-testid="stExpander"] > details {
            width: var(--content-w-mobile) !important;
            max-width: var(--content-w-mobile) !important;
        }
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
    
    /* Input bar (always bottom, centered, half-width) */
    .input-wrapper {
        position: fixed;
        bottom: 1.25rem;
        top: auto;
        left: 0;
        right: 0;
        transform: none;
        width: 90vw;
        max-width: 640px;
        background: transparent;
        border: none;
        padding: 0 1.25rem;
        z-index: 10000;
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
        max-width: 640px;
        width: 100%;
        margin: 0 auto;
        padding: 0.65rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        box-sizing: border-box;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.10);
        border: 1px solid rgba(255, 255, 255, 0.18);
        backdrop-filter: blur(18px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
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
    
    /* Shadcn-like input styling for Streamlit text_input (robust selectors) */
    .stTextInput input {
        color: #e5e7eb !important;
    }

    /* BaseWeb input container (Streamlit uses BaseWeb under the hood) */
    .stTextInput div[data-baseweb="input"] > div {
        background: rgba(10, 10, 10, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 10px !important;
        box-shadow: none !important;
    }

    .stTextInput div[data-baseweb="input"] input {
        background: transparent !important;
        border: none !important;
        padding: 0.7rem 0.9rem !important;
        min-height: 44px !important;
        font-size: 0.95rem !important;
        line-height: 1.4 !important;
    }

    /* Fallback selector (older Streamlit DOM) */
    .stTextInput > div > div > input {
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        padding: 0.7rem 0.9rem !important;
        min-height: 44px !important;
        font-size: 0.95rem !important;
        transition: box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease;
        background: rgba(10, 10, 10, 0.45) !important;
        color: #e5e7eb !important;
        width: 100% !important;
        box-sizing: border-box;
        line-height: 1.4 !important;
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
    
    .stTextInput div[data-baseweb="input"] > div:focus-within {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.22) !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.22) !important;
        outline: none;
        background: rgba(10, 10, 10, 0.55) !important;
    }

    /* Shadcn-like styling for Streamlit chat_input */
    div[data-testid="stChatInput"] {
        max-width: 640px;
        margin-left: auto;
        margin-right: auto;
    }

    /* Single-box chat input: outer container is the box */
    div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }

    /* Remove any extra inner wrappers that can look like a second box */
    div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div > div {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
    }

    div[data-testid="stChatInput"] textarea {
        /* Remove inner box look: keep only the outer container */
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        outline: none !important;
        color: #e5e7eb !important;
        font-size: 0.95rem !important;
        line-height: 1.4 !important;
    }

    /* Prevent any default focus ring / red focus border on the inner textarea */
    div[data-testid="stChatInput"] textarea:focus,
    div[data-testid="stChatInput"] textarea:focus-visible {
        outline: none !important;
        border: none !important;
        box-shadow: none !important;
    }

    div[data-testid="stChatInput"] div[data-baseweb="textarea"] > div:focus-within {
        /* focus ring applied to outer container (in the inline style below) */
        border-color: transparent !important;
        box-shadow: none !important;
    }

    /* Also neutralize focus styling on inner BaseWeb wrappers (can show red line) */
    div[data-testid="stChatInput"] div[data-baseweb="textarea"] *:focus,
    div[data-testid="stChatInput"] div[data-baseweb="textarea"] *:focus-visible {
        outline: none !important;
        box-shadow: none !important;
        border-color: transparent !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(156, 163, 175, 0.85);
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
        border-radius: 14px;
        padding: 0.55rem;
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
        padding: 0.35rem 0.65rem !important;
        min-width: auto !important;
        width: auto !important;
        height: auto !important;
        border-radius: 12px !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.15);
        transform: translateY(-1px);
    }

    /* Mobile: keep "New chat" pinned top-right */
    @media (max-width: 768px) {
        .stButton > button[kind="secondary"] {
            position: fixed !important;
            top: 0.75rem !important;
            right: 0.75rem !important;
            z-index: 10001 !important;
        }
    }

    @media (max-width: 480px) {
        .stButton > button[kind="secondary"] {
            top: 0.6rem !important;
            right: 0.6rem !important;
        }
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
    
    /* Citation badges */
    .citation-badge {
        background: rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        padding: 0.15rem 0.4rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 500;
        cursor: pointer;
        margin: 0 0.15rem;
        border: 1px solid rgba(59, 130, 246, 0.3);
        transition: all 0.2s;
    }
    
    .citation-badge:hover {
        background: rgba(59, 130, 246, 0.3);
        transform: scale(1.05);
    }
    
    /* Removed tech badges */
</style>
""", unsafe_allow_html=True)

# Helper functions for formatting (defined before use)
def _format_answer_with_citations(answer: str) -> str:
    """Format answer with clickable citations."""
    import re
    def replace_citation(match):
        doc_num = match.group(1)
        return f'<span class="citation-badge" data-doc="{doc_num}">[Doc {doc_num}]</span>'
    
    formatted = re.sub(r'\[Doc (\d+)\]', replace_citation, answer)
    formatted = formatted.replace('\n', '<br>')
    return formatted

def _format_answer_with_metadata(answer: str, metadata: dict) -> str:
    """Format answer with citations (no raw HTML panels)."""
    import re
    
    def replace_citation(match):
        doc_num = match.group(1)
        return f'<span class="citation-badge" data-doc="{doc_num}">[Doc {doc_num}]</span>'
    
    formatted_answer = re.sub(r'\[Doc (\d+)\]', replace_citation, answer)
    formatted_answer = formatted_answer.replace('\n', '<br>')
    return f'<div class="assistant-message">{formatted_answer}</div>'

def _build_why_panel(metadata: dict) -> str:
    """Deprecated: previously returned raw HTML. Kept for compatibility."""
    return ""

def _format_error_ux(error_msg: str) -> str:
    """Format error messages with better UX."""
    if "don't know" in error_msg.lower() or "no context" in error_msg.lower():
        return """
**I don't have enough verified context to answer this safely.**

*Options:*
- 🔍 **Try rephrasing your question**
- 📄 **Upload a relevant document**
- 🌐 **Enable web search** (if configured)

This safety feature prevents hallucination and ensures accurate answers.
"""
    
    return f"""
**Something went wrong**

*Error:* {error_msg}

*What you can do:*
- Check that Ollama is running (`ollama serve`)
- Verify Qdrant is accessible
- Try rephrasing your question
"""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False

# Top-right: “New chat”
top_left, top_right = st.columns([0.9, 0.1])
with top_right:
    if st.button("New chat", help="Clear chat", key="clear_btn", type="secondary", use_container_width=False):
        st.session_state.messages = []
        st.session_state.processing = False
        st.rerun()

# Show hero (empty) or messages
if not st.session_state.messages:
    # Suggested prompts (pure UI convenience)
    st.markdown("""
    <div class="empty-screen">
        <div class="hero">
            <div class="hero-badge">Deterministic · Auditable · Zero-Hallucination</div>
            <div class="hero-title">Enterprise Compliance Intelligence</div>
            <div class="hero-subtitle">
                Ask questions that require verified sources. Every answer includes evidence, confidence, and an audit trail.
            </div>
            <div class="hero-hints">
                <div class="hint">
                    <div class="hint-title">Try a verified question</div>
                    <p class="hint-desc">Ask about certifications, standards, controls, and evidence.</p>
                </div>
                <div class="hint">
                    <div class="hint-title">How to verify</div>
                    <p class="hint-desc">Review claims → sources, decision path, and confidence. If evidence is missing, it refuses.</p>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Golden prompts (click-to-run)
    st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.markdown("**Try a verified question**")
        b1, b2, b3 = st.columns(3)
        prompt_1 = "What compliance certifications does AWS have?"
        prompt_2 = "Is AWS compliant with GDPR?"
        prompt_3 = "What security standards does AWS follow?"

        clicked = None
        if b1.button("AWS certifications", use_container_width=True):
            clicked = prompt_1
        if b2.button("GDPR compliance", use_container_width=True):
            clicked = prompt_2
        if b3.button("Security standards", use_container_width=True):
            clicked = prompt_3

        if clicked and not st.session_state.processing:
            st.session_state.processing = True
            st.session_state.messages.append({"role": "user", "content": clicked})
            st.rerun()

        st.caption("⚠️ Opinion, speculation, or unsupported questions will be refused by design.")
else:
    # Always-visible verification block (trust signaling)
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        st.markdown("**How to know this answer is correct**")
        st.caption(
            "This system answers only what can be proven from retrieved sources. "
            "Each response includes evidence (sources), claim-to-source mapping, a decision path, and a confidence score. "
            "If evidence is missing or policy blocks the request, it refuses."
        )

    for message in st.session_state.messages:
        # IMPORTANT: Keep all elements (bubble + expander) in the same centered column.
        # Mixing HTML wrapper divs with Streamlit widgets causes misalignment.
        _, mid, _ = st.columns([1, 3, 1])
        with mid:
            if message["role"] == "user":
                st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                if "metadata" in message:
                    st.markdown(
                        _format_answer_with_metadata(message["content"], message["metadata"]),
                        unsafe_allow_html=True,
                    )

                    # Space between answer bubble and expander
                    st.markdown("<div style='height: 0.6rem;'></div>", unsafe_allow_html=True)

                    meta = message.get("metadata") or {}
                    decision_path = meta.get("decision_path", "rag")
                    documents = meta.get("documents", []) or []
                    claims = meta.get("claims", []) or []
                    sources_used = meta.get("sources_used", []) or []
                    confidence = meta.get("confidence", 0.0)
                    confidence_reason = meta.get("confidence_reason", "")
                    refusal_reason = meta.get("refusal_reason")

                    with st.expander("🔍 Audit & Evidence"):
                        st.markdown(f"**Decision path**  \n`{decision_path}`")

                        if refusal_reason:
                            st.markdown(f"**Refusal reason**  \n`{refusal_reason}`")

                        # Claims
                        st.markdown("**Claims**")
                        if isinstance(claims, list) and claims:
                            for c in claims:
                                if isinstance(c, dict):
                                    st.markdown(f"- {c.get('text','').strip()}  \n  `source: {c.get('source_doc','')}`")
                        else:
                            st.caption("No claims (refusal or insufficient evidence).")

                        # Sources
                        st.markdown("**Sources**")
                        if isinstance(documents, list) and documents:
                            # Render only sources_used (if present), else show first N docs
                            shown = []
                            if isinstance(sources_used, list) and sources_used:
                                for s in sources_used:
                                    shown.append(s)
                            for idx, d in enumerate(documents[:6], 1):
                                if not isinstance(d, dict):
                                    continue
                                doc_id = d.get("document_id") or d.get("source") or f"Doc {idx}"
                                ver = d.get("version")
                                url = d.get("url")
                                extra = f" (v{ver})" if ver else ""
                                line = f"- {doc_id}{extra}"
                                if url:
                                    line += f"  \n  `{url}`"
                                st.markdown(line)
                        else:
                            st.caption("No sources (refusal or no retrieval).")

                        # Confidence
                        st.markdown("**Confidence**")
                        st.markdown(f"`{confidence:.2f}` — {confidence_reason}")
                else:
                    content = _format_answer_with_citations(message["content"])
                    st.markdown(f'<div class="assistant-message">{content}</div>', unsafe_allow_html=True)

            # Space between message blocks
            st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

#
# INPUT
# Use a single native chat input (always visible).
# We dynamically position it closer to the hero on the empty screen.
#

# Empty state: lift input up to sit right under the tiles (responsive)
chat_bottom = "clamp(220px, 26vh, 360px)" if not st.session_state.messages else "1.25rem"
chat_z = "10000" if not st.session_state.messages else "50"
st.markdown(
    f"""
    <style>
      div[data-testid="stChatInput"] {{
        position: fixed !important;
        left: 50% !important;
        transform: translateX(-50%) !important;
        bottom: {chat_bottom} !important;
        width: min(640px, 90vw) !important;
        z-index: {chat_z} !important;
        background: rgba(10, 10, 10, 0.55) !important;
        border: 1px solid rgba(255, 255, 255, 0.22) !important;
        border-radius: 14px !important;
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.35) !important;
        backdrop-filter: blur(18px) !important;
        padding: 0.35rem 0.4rem !important;
      }}

      div[data-testid="stChatInput"]:focus-within {{
        border-color: rgba(139, 92, 246, 0.6) !important;
        box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.22), 0 12px 30px rgba(0, 0, 0, 0.35) !important;
      }}

      /* Refusal education (always visible under the input) */
      div[data-testid="stChatInput"]::after {{
        content: "⚠️ Opinion, speculation, or unsupported questions will be refused by design.";
        display: block;
        margin-top: 0.35rem;
        padding: 0 0.35rem;
        color: rgba(156, 163, 175, 0.95);
        font-size: 0.8rem;
        line-height: 1.25;
        text-align: left;
        pointer-events: none;
      }}

      /* Mobile/tablet: keep chat input from overlapping content */
      @media (max-width: 768px) {{
        div[data-testid="stChatInput"] {{
          width: min(94vw, 640px) !important;
        }}
      }}

      @media (max-width: 480px) {{
        div[data-testid="stChatInput"] {{
          width: 94vw !important;
          bottom: calc(0.9rem + env(safe-area-inset-bottom)) !important;
        }}
      }}
    </style>
    """,
    unsafe_allow_html=True,
)

prompt = st.chat_input("Ask a grounded question (sources required)…")

if prompt and not st.session_state.processing:
    st.session_state.processing = True
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.rerun()

elif st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.processing:
    # Process the last user message with streaming
    user_query = st.session_state.messages[-1]["content"]

    # Center streaming UI in the same column as messages
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        status_placeholder = st.empty()
        answer_placeholder = st.empty()
        why_placeholder = st.empty()
    
    try:
        # Initialize answer state
        if "current_answer" not in st.session_state:
            st.session_state.current_answer = ""
        if "metadata" not in st.session_state:
            st.session_state.metadata = {}
        
        # Stream answer with metadata
        for chunk in generate_answer_stream_ui(user_query):
            if chunk["type"] == "status":
                # Update status indicator
                status_text = chunk["data"]
                status_placeholder.markdown(
                    f'<div class="status-badge">{status_text}<span class="loading-dots"></span></div>',
                    unsafe_allow_html=True
                )
            
            elif chunk["type"] == "metadata":
                # Store metadata for "Why this answer?" panel
                metadata = chunk["data"]
                st.session_state.metadata = metadata
                
                decision_path = metadata.get("decision_path", "rag")
                status_map = {
                    "rag": "🔍 Retrieving documents",
                    "web_search": "🌐 Searching the web",
                    "roll_dice": "🎲 Calculating"
                }
                status_text = status_map.get(decision_path, "🔍 Processing")
                status_placeholder.markdown(
                    f'<div class="status-badge">{status_text}<span class="loading-dots"></span></div>',
                    unsafe_allow_html=True
                )
            
            elif chunk["type"] == "token":
                # Append token and update display
                st.session_state.current_answer += chunk["data"]
                answer_placeholder.markdown(
                    f'<div class="assistant-message">{_format_answer_with_citations(st.session_state.current_answer)}</div>',
                    unsafe_allow_html=True
                )
            
            elif chunk["type"] == "done":
                # Final answer with metadata
                final_data = chunk["data"]
                final_answer = final_data.get("answer", st.session_state.current_answer)
                citations = final_data.get("citations", [])
                
                # Update status
                status_placeholder.markdown(
                    '<div class="status-badge">✅ Complete</div>',
                    unsafe_allow_html=True
                )
                
                # Final answer bubble
                answer_placeholder.markdown(
                    _format_answer_with_metadata(final_answer, st.session_state.metadata),
                    unsafe_allow_html=True
                )

                # Native expander (no raw HTML tags)
                meta = st.session_state.metadata or {}
                research_notes = meta.get("research_notes", []) or []
                tool_calls = meta.get("tool_calls", []) or []
                decision_path = meta.get("decision_path", "rag")
                tool_name = tool_calls[0].get("tool") if tool_calls else None

                with why_placeholder.container():
                    with st.expander("Why this answer?"):
                        st.markdown(f"**Decision path**: `{decision_path}`")
                        if tool_name:
                            st.markdown(f"**Tool**: `{tool_name}`")
                        st.markdown(f"**Documents used**: `{len(research_notes)}`")
                        if research_notes:
                            st.markdown("**Source previews**:")
                            for i, note in enumerate(research_notes[:3], 1):
                                preview = note[:180] + ("..." if len(note) > 180 else "")
                                st.caption(f"{i}. {preview}")
                
                # Store final message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_answer,
                    "metadata": st.session_state.metadata
                })
                
                # Cleanup
                del st.session_state.current_answer
                del st.session_state.metadata
                st.session_state.processing = False
                
                # Clear status after brief delay
                time.sleep(0.5)
                status_placeholder.empty()
                why_placeholder.empty()
                st.rerun()
        
    except Exception as e:
        error_message = _format_error_ux(str(e))
        st.session_state.messages.append({"role": "assistant", "content": error_message})
        st.session_state.processing = False
        status_placeholder.empty()
        answer_placeholder.empty()
        why_placeholder.empty()
        
        # Cleanup
        if "current_answer" in st.session_state:
            del st.session_state.current_answer
        if "metadata" in st.session_state:
            del st.session_state.metadata
        
        st.rerun()

else:
    pass  # No-op
