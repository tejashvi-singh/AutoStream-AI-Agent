import streamlit as st
import requests
import uuid

# ─── Configuration ────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000/chat"

st.set_page_config(
    page_title="AutoStream AI Agent",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global reset & base */
    * { box-sizing: border-box; }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0a0d14;
        color: #e2e8f0;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding: 0 !important; }
    .stApp { background: linear-gradient(135deg, #0a0d14 0%, #0f1520 50%, #0a0d14 100%); }

    /* ── Hero Header ── */
    .hero {
        background: linear-gradient(135deg, #1a0533 0%, #0d1b3e 50%, #0a1628 100%);
        border-bottom: 1px solid rgba(99, 102, 241, 0.3);
        padding: 28px 48px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0;
    }
    .hero-left { display: flex; flex-direction: column; gap: 4px; }
    .hero-logo {
        font-size: 26px;
        font-weight: 800;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
    }
    .hero-sub {
        font-size: 13px;
        color: #94a3b8;
        font-weight: 400;
        letter-spacing: 0.2px;
    }
    .hero-badge {
        background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.2));
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #c4b5fd;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }

    /* ── Main layout ── */
    .main-layout {
        display: flex;
        height: calc(100vh - 90px);
        overflow: hidden;
    }

    /* ── Chat area ── */
    .chat-area {
        flex: 1;
        display: flex;
        flex-direction: column;
        padding: 24px 32px;
        overflow-y: auto;
        max-width: 860px;
        margin: 0 auto;
        width: 100%;
    }

    /* ── Messages ── */
    .message-row-user {
        display: flex;
        justify-content: flex-end;
        margin: 8px 0;
    }
    .message-row-bot {
        display: flex;
        justify-content: flex-start;
        align-items: flex-start;
        gap: 10px;
        margin: 8px 0;
    }
    .avatar-bot {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        flex-shrink: 0;
        margin-top: 2px;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    .bubble-user {
        background: linear-gradient(135deg, #6366f1, #4f46e5);
        color: white;
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 70%;
        font-size: 14px;
        line-height: 1.6;
        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.35);
        word-wrap: break-word;
    }
    .bubble-bot {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #e2e8f0;
        padding: 12px 18px;
        border-radius: 4px 18px 18px 18px;
        max-width: 70%;
        font-size: 14px;
        line-height: 1.7;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
        word-wrap: break-word;
    }
    .bubble-bot strong { color: #a78bfa; }

    /* ── Welcome state ── */
    .welcome-card {
        background: rgba(99, 102, 241, 0.06);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 20px;
        padding: 36px;
        text-align: center;
        margin: 20px 0 28px;
    }
    .welcome-icon { font-size: 52px; margin-bottom: 14px; }
    .welcome-title {
        font-size: 22px;
        font-weight: 700;
        color: #f1f5f9;
        margin-bottom: 8px;
    }
    .welcome-subtitle {
        font-size: 14px;
        color: #94a3b8;
        margin-bottom: 24px;
        line-height: 1.6;
    }
    .chip-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        justify-content: center;
    }
    .chip {
        background: rgba(99, 102, 241, 0.12);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #a5b4fc;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12.5px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s;
        white-space: nowrap;
    }
    .chip:hover {
        background: rgba(99, 102, 241, 0.25);
        border-color: rgba(99, 102, 241, 0.6);
        color: white;
    }

    /* ── Lead success card ── */
    .lead-success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(5, 150, 105, 0.08));
        border: 1px solid rgba(16, 185, 129, 0.35);
        border-radius: 16px;
        padding: 20px 24px;
        margin: 16px 0;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .lead-success-icon { font-size: 36px; }
    .lead-success-text { flex: 1; }
    .lead-success-title {
        font-size: 15px;
        font-weight: 700;
        color: #34d399;
        margin-bottom: 4px;
    }
    .lead-success-sub { font-size: 13px; color: #6ee7b7; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: rgba(15, 21, 32, 0.95) !important;
        border-right: 1px solid rgba(255,255,255,0.07) !important;
        min-width: 280px !important;
    }
    [data-testid="stSidebar"] .stMarkdown { padding: 0; }

    .sidebar-section {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .sidebar-label {
        font-size: 10px;
        font-weight: 700;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 10px;
    }
    .sidebar-value {
        font-size: 13px;
        color: #cbd5e1;
        font-weight: 500;
        word-break: break-all;
    }
    .intent-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(99,102,241,0.2), rgba(139,92,246,0.15));
        border: 1px solid rgba(139, 92, 246, 0.4);
        color: #c4b5fd;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 11.5px;
        font-weight: 600;
    }
    .lead-badge {
        display: inline-block;
        background: linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.15));
        border: 1px solid rgba(16,185,129,0.4);
        color: #34d399;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 11.5px;
        font-weight: 600;
    }
    .demo-step {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .demo-step:last-child { border-bottom: none; }
    .step-num {
        background: rgba(99,102,241,0.2);
        color: #a78bfa;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 10px;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }
    .step-text { font-size: 12px; color: #94a3b8; line-height: 1.5; }
    .step-text code {
        background: rgba(99,102,241,0.15);
        color: #a5b4fc;
        padding: 1px 5px;
        border-radius: 4px;
        font-size: 11px;
    }

    /* ── Input area ── */
    .stChatInput > div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
        border-radius: 16px !important;
        padding: 4px 8px !important;
    }
    .stChatInput textarea {
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        background: transparent !important;
    }
    div[data-testid="stChatMessage"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ───────────────────────────────────────────────────────
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_intent" not in st.session_state:
    st.session_state.current_intent = None
if "lead_captured" not in st.session_state:
    st.session_state.lead_captured = False

# ─── Hero Header ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-left">
        <div class="hero-logo">🎬 AutoStream AI Agent</div>
        <div class="hero-sub">Convert creator conversations into qualified leads — powered by LangGraph + Groq</div>
    </div>
    <div class="hero-badge">⚡ LIVE DEMO</div>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Thread ID card
    st.markdown(f"""
    <div class="sidebar-section">
        <div class="sidebar-label">🔗 Session Thread ID</div>
        <div class="sidebar-value">{st.session_state.thread_id[:20]}...</div>
    </div>
    """, unsafe_allow_html=True)

    # Intent + Lead status
    intent_display = st.session_state.current_intent or "Awaiting input..."
    st.markdown(f"""
    <div class="sidebar-section">
        <div class="sidebar-label">🧠 Agent Memory State</div>
        <div style="margin-bottom: 8px;">
            <div class="sidebar-label" style="margin-bottom:4px;">Current Intent</div>
            <span class="intent-badge">{intent_display}</span>
        </div>
        <div>
            <div class="sidebar-label" style="margin-bottom:4px;">Lead Status</div>
            {"<span class='lead-badge'>✅ Lead Captured!</span>" if st.session_state.lead_captured else "<span style='color:#64748b;font-size:12px;'>Not yet captured</span>"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Demo flow steps
    st.markdown("""
    <div class="sidebar-section">
        <div class="sidebar-label">📋 Demo Conversation Flow</div>
        <div class="demo-step">
            <div class="step-num">1</div>
            <div class="step-text">Type <code>Hi there!</code> — greeting detection</div>
        </div>
        <div class="demo-step">
            <div class="step-num">2</div>
            <div class="step-text">Ask <code>Tell me about your pricing</code> — RAG knowledge base retrieval</div>
        </div>
        <div class="demo-step">
            <div class="step-num">3</div>
            <div class="step-text">Say <code>I want to try Pro for my YouTube channel</code> — high intent detected</div>
        </div>
        <div class="demo-step">
            <div class="step-num">4</div>
            <div class="step-text">Provide your <code>name</code> → <code>email</code> → <code>platform</code></div>
        </div>
        <div class="demo-step">
            <div class="step-num">5</div>
            <div class="step-text">🎉 Lead captured! <code>mock_lead_capture</code> executes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Reset button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Reset Session", use_container_width=True):
        for key in ["messages", "current_intent", "lead_captured"]:
            del st.session_state[key]
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

# ─── Chat Area ───────────────────────────────────────────────────────────────
chat_container = st.container()

with chat_container:
    # Lead captured success banner
    if st.session_state.lead_captured:
        st.markdown("""
        <div class="lead-success">
            <div class="lead-success-icon">🎊</div>
            <div class="lead-success-text">
                <div class="lead-success-title">Lead Successfully Captured!</div>
                <div class="lead-success-sub">mock_lead_capture() executed · Team will follow up shortly</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Welcome state
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-card">
            <div class="welcome-icon">🚀</div>
            <div class="welcome-title">Welcome to AutoStream AI</div>
            <div class="welcome-subtitle">
                I'm your AI-powered sales assistant. Ask me about our plans,<br>
                features, or get started on your creator journey today.
            </div>
            <div class="chip-grid">
                <div class="chip">💰 What are your pricing plans?</div>
                <div class="chip">🎬 Tell me about the Pro plan</div>
                <div class="chip">📋 What's your refund policy?</div>
                <div class="chip">🚀 I want to sign up!</div>
                <div class="chip">🤖 What is AutoStream?</div>
                <div class="chip">🎙️ Do you support AI captions?</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Render chat history with custom bubbles
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="message-row-user">
                <div class="bubble-user">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            formatted = msg["content"].replace("\n", "<br>").replace("**", "<strong>").replace("**", "</strong>")
            st.markdown(f"""
            <div class="message-row-bot">
                <div class="avatar-bot">✨</div>
                <div class="bubble-bot">{msg["content"]}</div>
            </div>
            """, unsafe_allow_html=True)

# ─── Chat Input ───────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask about pricing, plans, or say 'I want to sign up'..."):
    # Append user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call FastAPI backend
    with st.spinner(""):
        try:
            response = requests.post(
                API_URL,
                json={"thread_id": st.session_state.thread_id, "message": prompt},
                timeout=30,
            )
            if response.status_code == 200:
                data = response.json()
                bot_reply = data["response"]
                st.session_state.current_intent = data.get("intent")
                st.session_state.lead_captured = data.get("lead_captured", False)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
            else:
                error_msg = f"Backend error ({response.status_code}): {response.text}"
                st.session_state.messages.append({"role": "assistant", "content": f"⚠️ {error_msg}"})
        except requests.exceptions.ConnectionError:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "⚠️ **Cannot reach the backend.** Make sure FastAPI is running on port 8000:\n```\npython3 -m uvicorn app.main:fastapi_app --reload --port 8000\n```"
            })
        except Exception as e:
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Unexpected error: {str(e)}"})

    st.rerun()
