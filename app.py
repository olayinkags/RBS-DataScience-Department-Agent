import streamlit as st
from src.agents import build_agent, run_agent

# ── Page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="RBS Nigeria · AI Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.main { background: #0f0f0f; color: #e8e0d0; }
.block-container { padding: 2rem 2rem 4rem; max-width: 1200px; }

/* Header */
.rbs-header {
    background: linear-gradient(135deg, #1a1208 0%, #2c1e08 50%, #1a1208 100%);
    border: 1px solid #c9a84c44;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.rbs-header::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, transparent, #c9a84c, transparent);
}
.rbs-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2rem; font-weight: 700;
    color: #c9a84c; margin: 0 0 0.3rem;
}
.rbs-header p { color: #a09070; font-size: 0.95rem; margin: 0; font-weight: 300; }

/* Chat bubbles */
[data-testid="chat-message-user"] > div {
    background: #1c1c1c !important;
    border: 1px solid #333 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}
[data-testid="chat-message-assistant"] > div {
    background: #171209 !important;
    border: 1px solid #c9a84c33 !important;
    border-radius: 12px !important;
    padding: 1rem !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0d0d0d !important;
    border-right: 1px solid #c9a84c22;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100%;
    background: #1c1508;
    border: 1px solid #c9a84c44;
    color: #c9a84c;
    border-radius: 8px;
    font-family: 'DM Sans', sans-serif;
    font-size: 0.82rem;
    text-align: left;
    padding: 0.5rem 0.8rem;
    margin-bottom: 4px;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2c2010;
    border-color: #c9a84c;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background: #1c1c1c !important;
    border: 1px solid #c9a84c44 !important;
    color: #e8e0d0 !important;
    border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 2px #c9a84c22 !important;
}

/* Expander (admin reasoning panel) */
.streamlit-expanderHeader {
    background: #111 !important;
    border: 1px solid #c9a84c22 !important;
    border-radius: 8px !important;
    color: #555 !important;
    font-size: 0.78rem !important;
}
.streamlit-expanderContent {
    background: #0d0d0d !important;
    border: 1px solid #c9a84c11 !important;
    font-size: 0.8rem;
    color: #666;
}

/* Step card inside reasoning panel */
.step-card {
    background: #141414;
    border-left: 3px solid #c9a84c55;
    padding: 0.5rem 0.8rem;
    margin: 0.3rem 0;
    border-radius: 0 6px 6px 0;
    font-size: 0.78rem;
    font-family: 'Courier New', monospace;
    color: #666;
}

hr { border-color: #c9a84c22 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Cached agent ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to AI knowledge base…")
def load_agent():
    return build_agent()


with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem;'>
        <div style='font-family: Playfair Display, serif; font-size: 1.3rem;
                    color: #c9a84c; font-weight: 700;'>RBS Nigeria</div>
        <div style='color: #555; font-size: 0.75rem; margin-top: 4px;'>
            Executive Master in Data Science Management
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    # What I can help with — friendly, not technical
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.75rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>
        I Can Help You With
    </div>
    <div style='color: #777; font-size: 0.82rem; line-height: 2;'>
        📚 &nbsp;Programme overview & curriculum<br>
        💰 &nbsp;Tuition fees & payment plans<br>
        📋 &nbsp;Admission requirements<br>
        ⚖️ &nbsp;Nigeria vs Italy comparison<br>
        🎯 &nbsp;Career outcomes & support<br>
        🌐 &nbsp;Latest news & updates
    </div>
    <hr>
    """, unsafe_allow_html=True)

    # Quick questions
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.75rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>
        Quick Questions
    </div>
    """, unsafe_allow_html=True)

    quick_questions = [
        "What is the programme duration?",
        "Compare Nigeria vs Italy campus fees",
        "What are the admission requirements?",
        "What modules are in the curriculum?",
        "Is the degree internationally accredited?",
        "What career support is provided?",
        "Can I study online or part-time?",
        "What is the latest news about RBS Nigeria?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"qq_{q}"):
            st.session_state.pending = q

    st.markdown("<hr>", unsafe_allow_html=True)

    # Contact info
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.75rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px;'>
        Contact Admissions
    </div>
    <div style='color: #666; font-size: 0.8rem; line-height: 1.8;'>
        🌍 <a href="https://romebusinessschool.ng" style="color:#c9a84c; text-decoration:none;">
            romebusinessschool.ng</a><br>
        🇮🇹 <a href="https://romebusinessschool.com" style="color:#c9a84c; text-decoration:none;">
            romebusinessschool.com</a>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    # Admin panel — hidden behind a toggle, not visible by default
    with st.expander("⚙️ Admin", expanded=False):
        show_reasoning = st.toggle("Show agent reasoning", value=False)
        st.session_state.show_reasoning = show_reasoning

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Re-index", use_container_width=True):
                with st.spinner("Re-scraping & re-indexing…"):
                    import asyncio
                    from src.scraper  import scrape_all
                    from src.loader   import prepare_all_chunks
                    from src.embedder import upload_to_pinecone
                    asyncio.run(scrape_all())
                    chunks = prepare_all_chunks()
                    upload_to_pinecone(chunks, namespace="rbs")
                    st.cache_resource.clear()
                st.success("Done!")
        with col2:
            if st.button("🗑️ Clear chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()


st.markdown("""
<div class="rbs-header">
    <h1>🎓 Executive Master in Data Science</h1>
    <p>Rome Business School Nigeria · AI Admissions Advisor · Available 24/7</p>
</div>
""", unsafe_allow_html=True)

# Session state defaults
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "Hello! 👋 I'm your RBS Admissions Advisor.\n\n"
            "I can answer any question about the **Executive Master in Data Science Management** "
            "at Rome Business School — including fees, curriculum, admission requirements, "
            "and how the Nigeria campus compares to Italy.\n\n"
            "What would you like to know?"
        ),
        "steps": [],
    })

if "show_reasoning" not in st.session_state:
    st.session_state.show_reasoning = False

# Load agent
agent_executor = load_agent()

# ── Display chat history ──────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Agent reasoning — only shown if admin toggle is ON
        if (
            msg["role"] == "assistant"
            and st.session_state.show_reasoning
            and msg.get("steps")
        ):
            with st.expander(f"Agent reasoning · {len(msg['steps'])} step(s)"):
                for i, step in enumerate(msg["steps"], 1):
                    st.markdown(
                        f'<div class="step-card">'
                        f'Step {i} &nbsp;→&nbsp; <strong>{step["tool"]}</strong>'
                        f'<br><span style="color:#444">{step["input"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

# ── Handle input ──────────────────────────────────────────────────────
user_input = None

if "pending" in st.session_state:
    user_input = st.session_state.pop("pending")

typed = st.chat_input("Ask anything about the RBS Data Science programme…")
if typed:
    user_input = typed

# ── Generate response ─────────────────────────────────────────────────
if user_input:
    st.session_state.messages.append({
        "role": "user", "content": user_input, "steps": []
    })
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Looking that up for you…"):
            result = run_agent(agent_executor, user_input)

        answer = result["answer"]
        steps  = result["steps"]

        st.markdown(answer)

        # Reasoning only shown if admin toggle is ON
        if st.session_state.show_reasoning and steps:
            with st.expander(f"Agent reasoning · {len(steps)} step(s)"):
                for i, step in enumerate(steps, 1):
                    st.markdown(
                        f'<div class="step-card">'
                        f'Step {i} &nbsp;→&nbsp; <strong>{step["tool"]}</strong>'
                        f'<br><span style="color:#444">{step["input"]}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "steps": steps,
    })