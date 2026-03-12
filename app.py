import streamlit as st
from src.agents import build_agent, run_agent
from src.scheduler import start_scheduler

# ── Page config — MUST be first Streamlit call ───────────────────────────────
st.set_page_config(
    page_title="RBS Nigeria · AI Advisor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — refined dark-gold academic aesthetic ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}
.main { background: #0f0f0f; color: #e8e0d0; }
.block-container { padding: 2rem 2rem 4rem; max-width: 1200px; }

/* ── Header ── */
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
    text-shadow: 0 0 30px #c9a84c44;
}
.rbs-header p { color: #a09070; font-size: 0.95rem; margin: 0; font-weight: 300; }

/* ── Chat messages ── */
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

/* ── Tool badge ── */
.tool-badge {
    display: inline-block;
    background: #c9a84c22;
    border: 1px solid #c9a84c55;
    color: #c9a84c;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.72rem;
    font-family: 'DM Sans', monospace;
    margin: 2px 3px;
    letter-spacing: 0.3px;
}

/* ── Sidebar ── */
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
    font-size: 0.8rem;
    text-align: left;
    padding: 0.5rem 0.8rem;
    margin-bottom: 4px;
    transition: all 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2c2010;
    border-color: #c9a84c;
    color: #e8c870;
}

/* ── Chat input ── */
[data-testid="stChatInput"] textarea {
    background: #1c1c1c !important;
    border: 1px solid #c9a84c44 !important;
    color: #e8e0d0 !important;
    border-radius: 12px !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #c9a84c !important;
    box-shadow: 0 0 0 2px #c9a84c22 !important;
}

/* ── Expander (agent steps) ── */
.streamlit-expanderHeader {
    background: #111 !important;
    border: 1px solid #c9a84c22 !important;
    border-radius: 8px !important;
    color: #a09070 !important;
    font-size: 0.82rem !important;
}
.streamlit-expanderContent {
    background: #0d0d0d !important;
    border: 1px solid #c9a84c11 !important;
    border-radius: 0 0 8px 8px !important;
}

/* ── Step card ── */
.step-card {
    background: #141414;
    border-left: 3px solid #c9a84c;
    padding: 0.7rem 1rem;
    margin: 0.5rem 0;
    border-radius: 0 8px 8px 0;
    font-size: 0.82rem;
}
.step-card .step-tool { color: #c9a84c; font-weight: 600; font-size: 0.78rem; }
.step-card .step-input { color: #888; font-size: 0.75rem; margin-top: 3px; }

/* ── Welcome message ── */
.welcome-card {
    background: linear-gradient(135deg, #171209, #1c1508);
    border: 1px solid #c9a84c33;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.welcome-card h3 { font-family:'Playfair Display',serif; color:#c9a84c; margin:0 0 0.5rem; }
.welcome-card p  { color: #a09070; font-size:0.9rem; line-height:1.6; margin:0; }

/* ── Divider ── */
hr { border-color: #c9a84c22 !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Cached agent (built once per session) ────────────────────────────────────
@st.cache_resource(show_spinner="🔗  Loading AI Agent & connecting to Pinecone…")
def load_agent():
    return build_agent()


with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 1rem 0 0.5rem;'>
        <div style='font-family: Playfair Display, serif; font-size: 1.3rem;
                    color: #c9a84c; font-weight: 700;'>RBS Nigeria</div>
        <div style='color: #666; font-size: 0.75rem; margin-top: 4px;'>
            AI Programme Advisor · Agent Edition
        </div>
    </div>
    <hr>
    """, unsafe_allow_html=True)

    # Agent capabilities
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.78rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom:8px;'>
        Agent Tools
    </div>
    """, unsafe_allow_html=True)

    tool_list = [
        ("🔍", "Programme Search",   "Semantic Pinecone search"),
        ("⚖️", "Campus Comparison",  "Nigeria vs Italy side-by-side"),
        ("💰", "Fee Lookup",         "Tuition & payment plans"),
        ("📋", "Admission Check",    "Requirements & eligibility"),
        ("📚", "Curriculum Lookup",  "Modules & specialisations"),
        ("🎯", "Career Outcomes",    "Jobs, alumni, salary data"),
        ("🌐", "Live Web Search",    "DuckDuckGo for latest news"),
        ("🧠", "General Knowledge",  "Background context"),
    ]

    for icon, name, desc in tool_list:
        st.markdown(
            f"<div style='display:flex; align-items:flex-start; margin:5px 0;'>"
            f"<span style='font-size:1rem; margin-right:8px;'>{icon}</span>"
            f"<div><div style='color:#e8e0d0; font-size:0.8rem;'>{name}</div>"
            f"<div style='color:#555; font-size:0.72rem;'>{desc}</div></div></div>",
            unsafe_allow_html=True
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Quick questions
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.78rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom:8px;'>
        Quick Questions
    </div>
    """, unsafe_allow_html=True)

    quick_questions = [
        "Compare Nigeria vs Italy campus fees",
        "What modules are in the curriculum?",
        "What are the admission requirements?",
        "How long is the programme?",
        "Is the degree internationally accredited?",
        "What career support is provided?",
        "Can I study online or part-time?",
        "What is the latest news about RBS Nigeria?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"qq_{q}"):
            st.session_state.pending = q

    st.markdown("<hr>", unsafe_allow_html=True)

    # Admin panel
    st.markdown("""
    <div style='color: #c9a84c; font-size: 0.78rem; font-weight: 600;
                text-transform: uppercase; letter-spacing: 1px; margin-bottom:8px;'>
        Admin
    </div>
    """, unsafe_allow_html=True)

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
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    # Agent reasoning toggle
    st.markdown("<hr>", unsafe_allow_html=True)
    show_steps = st.toggle("Show agent reasoning", value=True)
    st.session_state.show_steps = show_steps



# Header
st.markdown("""
<div class="rbs-header">
    <h1>🎓 RBS Executive Master in Data Science</h1>
    <p>AI-powered admissions advisor · Nigeria & Italy campuses · Powered by LangChain Agent + Pinecone + Gemini Pro</p>
</div>
""", unsafe_allow_html=True)

# Initialise session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant",
        "content": (
            "**Welcome!** I'm your RBS AI Admissions Advisor — powered by an intelligent agent "
            "with specialised tools for programme search, campus comparison, fee lookup, "
            "admission checking, curriculum exploration, and live web search.\n\n"
            "Unlike a simple chatbot, I **reason through your question** and pick the right "
            "tool (or combination of tools) to give you the most accurate answer.\n\n"
            "What would you like to know about the **Executive Master in Data Science Management**?"
        ),
        "tools_used": [],
        "steps": [],
    })

if "show_steps" not in st.session_state:
    st.session_state.show_steps = True

# Load the agent
agent_executor = load_agent()

# ── Display chat history ──────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show tools used for assistant messages
        if msg["role"] == "assistant" and msg.get("tools_used"):
            badges_html = "".join(
                f'<span class="tool-badge">🔧 {t}</span>'
                for t in msg["tools_used"]
            )
            st.markdown(
                f"<div style='margin-top:8px;'>Tools used: {badges_html}</div>",
                unsafe_allow_html=True
            )

            # Show reasoning steps if enabled
            if st.session_state.show_steps and msg.get("steps"):
                with st.expander(f"🧠 Agent reasoning ({len(msg['steps'])} steps)"):
                    for i, step in enumerate(msg["steps"], 1):
                        st.markdown(
                            f"""<div class="step-card">
                                <div class="step-tool">Step {i}: {step['tool']}</div>
                                <div class="step-input">Input: {step['input']}</div>
                            </div>""",
                            unsafe_allow_html=True
                        )

# ── Handle input ──────────────────────────────────────────────────────────────
user_input = None

if "pending" in st.session_state:
    user_input = st.session_state.pop("pending")

typed = st.chat_input("Ask anything about the RBS Executive Master in Data Science…")
if typed:
    user_input = typed

# ── Process and respond ───────────────────────────────────────────────────────
if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input, "tools_used": [], "steps": []})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate agent response
    with st.chat_message("assistant"):
        status_placeholder = st.empty()

        # Animated status messages while agent is thinking
        status_msgs = [
            "🤔  Reasoning about your question…",
            "🔍  Searching Pinecone knowledge base…",
            "⚖️  Comparing campus information…",
            "✍️  Composing answer…",
        ]
        import time
        with st.spinner(status_msgs[0]):
            result = run_agent(agent_executor, user_input)

        answer     = result["answer"]
        tools_used = result["tools_used"]
        steps      = result["steps"]

        # Display the answer
        st.markdown(answer)

        # Display tool badges
        if tools_used:
            badges_html = "".join(
                f'<span class="tool-badge">🔧 {t}</span>'
                for t in tools_used
            )
            st.markdown(
                f"<div style='margin-top:8px;'>Tools used: {badges_html}</div>",
                unsafe_allow_html=True
            )

        # Display reasoning steps
        if st.session_state.show_steps and steps:
            with st.expander(f"🧠 Agent reasoning ({len(steps)} steps)"):
                for i, step in enumerate(steps, 1):
                    st.markdown(
                        f"""<div class="step-card">
                            <div class="step-tool">Step {i}: {step['tool']}</div>
                            <div class="step-input">Input: {step['input']}</div>
                        </div>""",
                        unsafe_allow_html=True
                    )

    # Save to history
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "tools_used": tools_used,
        "steps": steps,
    })
