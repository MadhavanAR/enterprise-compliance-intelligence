import streamlit as st


st.set_page_config(
    page_title="Documentation · Enterprise Compliance Intelligence",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@300;400;500;600;700;800&display=swap');

  * {
    font-family: 'Montserrat', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  }

  /* Hide Streamlit chrome */
  #MainMenu {visibility: hidden;}
  footer {visibility: hidden;}
  header {visibility: hidden;}

  /* Background */
  html, body,
  div[data-testid="stAppViewContainer"],
  div[data-testid="stAppViewContainer"] > .main {
    background-color: #0a0a0a !important;
    background-image:
      radial-gradient(circle at 20% 30%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
      radial-gradient(circle at 80% 70%, rgba(59, 130, 246, 0.15) 0%, transparent 50%),
      radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.1) 0%, transparent 50%);
    background-attachment: fixed !important;
    background-position: center center !important;
  }

  /* Docs layout */
  .block-container {
    max-width: 980px !important;
    padding: 1.25rem 1rem 4rem 1rem !important;
  }

  /* Match chat page "New chat" button theme/size */
  .stButton > button[kind*="secondary"] {
    background: rgba(255, 255, 255, 0.1) !important;
    color: #e5e7eb !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
    backdrop-filter: blur(10px) !important;
    padding: 0.28rem 0.55rem !important;
    min-width: auto !important;
    width: auto !important;
    height: 34px !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    line-height: 1 !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    white-space: nowrap !important;
  }

  .stButton > button[kind*="secondary"]:hover {
    background: rgba(255, 255, 255, 0.15) !important;
    transform: translateY(-1px);
  }

  a { color: #93c5fd !important; }
  code { color: #e5e7eb !important; }
</style>
""",
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False


# Top-right navigation (no overlays; real page routing)
_, nav = st.columns([0.72, 0.28])
with nav:
    back_col, clear_col = st.columns([1, 1])
    with back_col:
        if st.button("Back to chat", key="back_to_chat", type="secondary", use_container_width=False):
            st.switch_page("ui.py")
    with clear_col:
        if st.button("New chat", key="clear_btn_docs", type="secondary", use_container_width=False):
            st.session_state.messages = []
            st.session_state.processing = False
            st.switch_page("ui.py")


st.title("Documentation")
st.caption("Deterministic · Auditable · Zero-Hallucination")

st.markdown(
    """
### What this product does
This system answers **compliance and policy questions** using your trusted documents.

It is designed to be safe:
- If it can’t prove an answer from sources, it says **"I don't know."**
- It does **not** guess or fill gaps.

### What questions it is designed to answer
Ask questions that can be verified from documents, such as:
- Certifications and standards (SOC, ISO, GDPR, etc.)
- Security or compliance controls described in your documents
- "What does the document say about X?"
- "Which policy/section mentions X?"

### Examples (valid vs invalid)
**Valid questions (good)**
- "What compliance certifications does AWS have?"
- "Is AWS compliant with GDPR based on our compliance document?"
- "What does the AWS compliance document say about AWS Artifact?"

**Invalid questions (will be refused)**
- "Should AWS be trusted?"
- "Is AWS the best cloud?"
- "What should my company do?" (opinion / advice)
- Anything not supported by your documents

### How to verify answers (step-by-step)
After you get an answer, open **🔍 Audit & Evidence** and follow these steps:

**Step 1: Check Decision path**
- Shows what the system did (e.g., "query_router → rag → rag")
- This is for auditability and traceability

**Step 2: Review Claims**
- Each claim is a key statement the answer makes
- Every claim must have a `source` listed
- If a claim has no source, the answer is not verified

**Step 3: Verify Sources**
- Sources are the documents that support the claims
- Check that each claim's source appears in the Sources list
- If sources are missing or don't match claims, treat the answer as unverified

**Step 4: Evaluate Confidence**
- Confidence reflects evidence strength, not model certainty
- Low confidence (below 0.5) means weak or limited evidence
- High confidence (0.8+) means strong, multiple-source support

**When to treat an answer as not verified:**
- Claims do not map to sources
- Confidence is below 0.5
- Sources list is empty
- Decision path shows a refusal

### Understanding confidence scores
**What confidence means:**
- Confidence reflects the strength of evidence from your documents
- It is **not** a measure of model certainty or accuracy
- Low confidence = limited or weak evidence in your documents
- High confidence = strong, multi-source evidence in your documents

**Confidence ranges:**
- **0.8 - 1.0**: Strong evidence (multiple sources, clear support)
- **0.5 - 0.8**: Moderate evidence (some sources, partial support)
- **0.0 - 0.5**: Weak evidence (limited sources, unclear support)

**When to escalate for human review:**
- Confidence below 0.5 and the answer is critical for compliance decisions
- Claims and sources do not align
- The answer seems incomplete or unclear
- You need additional verification beyond what the system provides

### How to check claims and sources
**For each claim:**
1. Read the claim text
2. Find its listed source (e.g., "source: Doc 1")
3. Verify that source appears in the Sources section
4. If the source is missing or doesn't match, the claim is unverified

**For sources:**
1. Review the document names/IDs listed
2. Check that they are relevant to your question
3. Verify that claims reference these sources
4. If sources are generic or don't support claims, the answer is not reliable

### Why refusal is not a failure
**Refusal is a safety feature.** The system refuses when:
- It cannot find relevant documents
- The documents do not clearly support an answer
- The question is opinion/speculation/advice (not verifiable)

**Why this is good:**
- Prevents incorrect answers that could lead to compliance issues
- Ensures you only act on verified information
- Protects against hallucination and guessing
- Maintains audit integrity

**What to do when refused:**
- Check if your question can be rephrased to be more specific
- Verify that relevant documents are available in the system
- Consider whether the question requires opinion or advice (which the system cannot provide)
- For critical questions, consult human experts

### How this compares to normal chatbots / RAG systems
**Normal chatbots**
- Try to be helpful even when they don't know
- May guess or sound confident without proof
- Often provide answers that cannot be verified
- Do not show evidence or sources

**This system**
- Answers **only** when it can point to sources
- Provides an **audit trail** (claims, sources, decision path, confidence)
- Refuses when evidence is missing (zero-hallucination behavior)
- Every answer can be verified step-by-step

**Key difference:**
This system prioritizes **safety and verifiability** over being helpful. It will refuse rather than guess, which is essential for compliance and audit requirements.
"""
)

