import streamlit as st
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ------------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Ask About Yogesh",
    page_icon=":robot_face:",
    layout="centered",
    initial_sidebar_state="collapsed",
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
MODEL        = "llama-3.3-70b-versatile"
ME_FILE      = Path(__file__).parent / "me.txt"

# ------------------------------------------------------------------------------
# LOAD PROFILE
# ------------------------------------------------------------------------------
def load_profile() -> str:
    if ME_FILE.exists():
        content = ME_FILE.read_text(encoding="utf-8").strip()
        if content:
            return content
        return "[me.txt exists but is empty — please fill it in]"
    return "[me.txt not found — make sure it is in the same folder as app.py]"

profile = load_profile()

# ------------------------------------------------------------------------------
# SYSTEM PROMPT
# ------------------------------------------------------------------------------
SYSTEM_PROMPT = f"""You are representing Yogesh, an AI/ML Engineer based in Tamil Nadu, India.

STRICT RULES:
- Answer ONLY using the profile information provided below
- Speak in first person ("I") as Yogesh
- Be confident, clear, and direct
- If information is not in the profile, say: "I haven't shared that detail here — feel free to reach out to me directly!"
- NEVER invent projects, skills, or experience not listed in the profile
- NEVER hallucinate. If unsure, say you don't have that info

{'=' * 40}
YOGESH'S COMPLETE PROFILE
{'=' * 40}
{profile}
{'=' * 40}

Remember: Only answer from the profile above. Do not make anything up.
"""

# ------------------------------------------------------------------------------
# GROQ API
# ------------------------------------------------------------------------------
def call_groq(messages: list[dict]) -> str:
    if not GROQ_API_KEY:
        return (
            "API key missing. Add GROQ_API_KEY=your_key to your .env file. "
            "Get a free key at: https://console.groq.com/keys"
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model":       MODEL,
        "messages":    messages,
        "max_tokens":  800,
        "temperature": 0.3,
        "top_p":       0.9,
    }

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return "Request timed out. Please try again."
    except requests.exceptions.HTTPError:
        code = resp.status_code
        if code == 401:
            return "Invalid API key. Check your GROQ_API_KEY in .env."
        if code == 429:
            return "Rate limit hit. Wait a moment and try again."
        return f"API error {code}: {resp.text}"
    except Exception as e:
        return f"Unexpected error: {e}"

# ------------------------------------------------------------------------------
# SESSION STATE
# ------------------------------------------------------------------------------
if "messages"         not in st.session_state:
    st.session_state.messages         = []
if "input_text"       not in st.session_state:
    st.session_state.input_text       = ""
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""

# ------------------------------------------------------------------------------
# CALLBACKS
# ------------------------------------------------------------------------------
def handle_send():
    question = st.session_state.input_text.strip()
    if not question:
        return
    st.session_state.pending_question = question
    st.session_state.input_text       = ""

def handle_suggestion(q: str):
    st.session_state.pending_question = q
    st.session_state.input_text       = ""

def handle_clear():
    st.session_state.messages   = []
    st.session_state.input_text = ""

# ------------------------------------------------------------------------------
# PROCESS PENDING QUESTION  (runs before any widget is rendered)
# ------------------------------------------------------------------------------
if st.session_state.pending_question:
    question = st.session_state.pending_question
    st.session_state.pending_question = ""

    st.session_state.messages.append({"role": "user", "content": question})

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state.messages[-12:]:
        api_messages.append({"role": m["role"], "content": m["content"]})

    with st.spinner("Thinking..."):
        reply = call_groq(api_messages)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ------------------------------------------------------------------------------
# CSS  (UI unchanged)
# ------------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: #0c0c10; color: #e8e8f0; }
header[data-testid="stHeader"] { display: none; }
.block-container { padding-top: 0 !important; max-width: 780px; }

.hero {
    text-align: center;
    padding: 2.8rem 1rem 1.8rem;
    border-bottom: 1px solid #1a1a28;
    margin-bottom: 1.8rem;
}
.hero .badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #13132a; border: 1px solid #2a2a50; color: #9090c8;
    font-size: 0.72rem; font-family: 'DM Mono', monospace;
    padding: 0.28rem 0.85rem; border-radius: 100px;
    margin-bottom: 1.1rem; letter-spacing: 0.06em; text-transform: uppercase;
}
.hero h1 {
    font-size: 2rem; font-weight: 600; color: #ffffff;
    margin: 0 0 0.4rem; letter-spacing: -0.6px; line-height: 1.2;
}
.hero .subtitle { font-size: 0.88rem; color: #55557a; margin: 0; }

.msg-user { display: flex; justify-content: flex-end; margin: 1rem 0; }
.msg-user .bubble {
    background: #252580; color: #dde0ff;
    padding: 0.8rem 1.15rem; border-radius: 20px 20px 4px 20px;
    max-width: 76%; font-size: 0.9rem; line-height: 1.55;
    box-shadow: 0 2px 12px rgba(60,60,180,0.18);
}

.msg-ai { display: flex; justify-content: flex-start; margin: 1rem 0; align-items: flex-start; gap: 0.65rem; }
.msg-ai .avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #3535b8, #7535b8);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 600; color: #fff;
    flex-shrink: 0; margin-top: 2px; box-shadow: 0 2px 8px rgba(100,50,200,0.3);
}
.msg-ai .bubble {
    background: #13131e; border: 1px solid #1e1e30; color: #cccce8;
    padding: 0.8rem 1.15rem; border-radius: 4px 20px 20px 20px;
    max-width: 80%; font-size: 0.9rem; line-height: 1.65;
}

.suggest-label {
    text-align: center; font-size: 0.72rem; color: #383850;
    text-transform: uppercase; letter-spacing: 0.1em; margin: 0.5rem 0 0.6rem;
}

.stTextInput > div > div > input {
    background: #13131e !important; border: 1px solid #252538 !important;
    border-radius: 14px !important; color: #e0e0f0 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important; padding: 0.85rem 1.1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4545b0 !important;
    box-shadow: 0 0 0 3px rgba(70,70,180,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #383858 !important; }

div[data-testid="column"]:last-child .stButton > button {
    background: linear-gradient(135deg, #3535a8, #5535b8) !important;
    color: #fff !important; border: none !important; border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    font-size: 0.9rem !important; padding: 0.7rem 1rem !important; width: 100% !important;
}
div[data-testid="column"]:last-child .stButton > button:hover { opacity: 0.88 !important; }

.pill-btn .stButton > button {
    background: #13131e !important; border: 1px solid #22223a !important;
    color: #6868a0 !important; border-radius: 100px !important;
    font-size: 0.78rem !important; padding: 0.3rem 0.85rem !important;
    white-space: nowrap !important; width: 100% !important;
}
.pill-btn .stButton > button:hover {
    background: #1a1a30 !important; border-color: #35356a !important; color: #9090c8 !important;
}

.clear-btn .stButton > button {
    background: transparent !important; border: 1px solid #1e1e30 !important;
    color: #383858 !important; border-radius: 8px !important;
    font-size: 0.78rem !important; padding: 0.3rem 0.8rem !important;
}
.clear-btn .stButton > button:hover { border-color: #2e2e50 !important; color: #5555a0 !important; }

hr { border-color: #1a1a28 !important; margin: 1.2rem 0 !important; }

.footer {
    text-align: center; margin-top: 2.5rem; padding-bottom: 2rem;
    color: #22223a; font-size: 0.72rem;
    font-family: 'DM Mono', monospace; letter-spacing: 0.04em;
}
.footer span { color: #2e2e50; }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SIDEBAR  (debug info)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Debug Panel")
    st.markdown(f"**me.txt found:** `{ME_FILE.exists()}`")
    st.markdown(f"**Profile length:** `{len(profile)} chars`")
    st.markdown(f"**API key set:** `{'Yes' if GROQ_API_KEY else 'No'}`")
    st.divider()
    st.markdown("**Profile preview:**")
    st.code(profile[:300], language=None)

# ------------------------------------------------------------------------------
# HERO
# ------------------------------------------------------------------------------
st.markdown("""
<div class="hero">
    <div class="badge">AI/ML Engineer · Tamil Nadu, India</div>
    <h1>Ask Anything About Yogesh</h1>
    <p class="subtitle">Skills &nbsp;·&nbsp; Projects &nbsp;·&nbsp; Experience &nbsp;·&nbsp; MLOps &nbsp;·&nbsp; RAG Systems &nbsp;·&nbsp; Availability</p>
</div>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SUGGESTED QUESTIONS
# ------------------------------------------------------------------------------
SUGGESTIONS = [
    "What are your core skills?",
    "Tell me about your RAG projects",
    "What do you do at Justo Global?",
    "What makes you different?",
]

if not st.session_state.messages:
    st.markdown('<p class="suggest-label">Try asking</p>', unsafe_allow_html=True)
    cols = st.columns(len(SUGGESTIONS))
    for i, (col, q) in enumerate(zip(cols, SUGGESTIONS)):
        with col:
            st.markdown('<div class="pill-btn">', unsafe_allow_html=True)
            st.button(q, key=f"sug_{i}", on_click=handle_suggestion, args=(q,))
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# CHAT HISTORY
# ------------------------------------------------------------------------------
with st.container():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="msg-user">
                <div class="bubble">{msg["content"]}</div>
            </div>""", unsafe_allow_html=True)
        else:
            content = msg["content"].replace("\n", "<br>")
            st.markdown(f"""
            <div class="msg-ai">
                <div class="avatar">Y</div>
                <div class="bubble">{content}</div>
            </div>""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# INPUT
# ------------------------------------------------------------------------------
st.markdown("<hr>", unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    st.text_input(
        label="question",
        placeholder="Ask anything about Yogesh...",
        label_visibility="collapsed",
        key="input_text",
    )
with col2:
    st.button("Send", use_container_width=True, on_click=handle_send)

# ------------------------------------------------------------------------------
# CLEAR
# ------------------------------------------------------------------------------
if st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([3, 1, 3])
    with mid:
        st.markdown('<div class="clear-btn">', unsafe_allow_html=True)
        st.button("Clear", key="clear", on_click=handle_clear)
        st.markdown('</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------------------------
st.markdown("""
<div class="footer">
    Powered by <span>Groq · Llama 3.3 70B</span> &nbsp;·&nbsp; Built by Yogesh
</div>
""", unsafe_allow_html=True)