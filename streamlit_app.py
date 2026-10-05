"""
Streamlit UI – Facilities Request Triage Dashboard.

All provider / LM Studio logic lives in the FastAPI + AnalysisService layers.
This UI only calls the FastAPI REST endpoints.
"""
from __future__ import annotations

import os

import httpx
import streamlit as st

API_BASE = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Facilities Request Triage",
    page_icon="🏛️",
    layout="wide",
)

# ──────────────────────────────────────────────────────────────────────────────
# FULL PREMIUM CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Syne:wght@700;800&display=swap');

/* ── RESET STREAMLIT CHROME ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
.block-container {
    padding-top: 0 !important;
    padding-bottom: 60px !important;
    max-width: 1200px !important;
}

/* ── GLOBAL ── */
html, body, .stApp {
    background: #08100d !important;
    color: #c8d8cc !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── NAVBAR ── */
.navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 0 18px;
    border-bottom: 1px solid #14231b;
    margin-bottom: 0;
}
.navbar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Syne', sans-serif;
    font-size: 1.25rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.01em;
}
.navbar-dot {
    width: 10px; height: 10px;
    background: #00e676;
    border-radius: 50%;
    box-shadow: 0 0 10px #00e676;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: 0.6; transform: scale(1.3); }
}
.navbar-status {
    font-size: 0.8rem;
    color: #00e676;
    background: #0a1f12;
    border: 1px solid #14391f;
    padding: 5px 14px;
    border-radius: 20px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;
}

/* ── HERO SECTION ── */
.hero {
    padding: 72px 0 56px;
    max-width: 800px;
}
.hero-tag {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #0a1f12;
    border: 1px solid #1a4a28;
    color: #00e676;
    font-size: 0.8rem;
    font-weight: 600;
    padding: 6px 16px;
    border-radius: 20px;
    margin-bottom: 28px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.hero h1 {
    font-family: 'Syne', sans-serif !important;
    font-size: clamp(2.8rem, 5vw, 4.2rem) !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    line-height: 1.05 !important;
    letter-spacing: -0.03em !important;
    margin: 0 0 24px !important;
}
.hero h1 span {
    background: linear-gradient(135deg, #00e676 0%, #69f0ae 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero p {
    font-size: 1.15rem !important;
    color: #7a9484 !important;
    line-height: 1.65 !important;
    margin: 0 !important;
    max-width: 580px;
}

/* ── FEATURE CARDS ROW ── */
.cards-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    margin: 48px 0;
}
.feat-card {
    background: #0c1a12;
    border: 1px solid #162a1e;
    border-radius: 16px;
    padding: 24px;
    transition: border-color 0.25s, box-shadow 0.25s;
}
.feat-card:hover {
    border-color: #00e676;
    box-shadow: 0 0 24px rgba(0, 230, 118, 0.08);
}
.feat-icon {
    font-size: 1.6rem;
    margin-bottom: 12px;
    display: block;
}
.feat-card h4 {
    font-family: 'Syne', sans-serif !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 0 8px !important;
}
.feat-card p {
    font-size: 0.875rem !important;
    color: #5a7a67 !important;
    line-height: 1.55 !important;
    margin: 0 !important;
}

/* ── SECTION DIVIDER ── */
.section-divider {
    border: none;
    border-top: 1px solid #14231b;
    margin: 0 0 40px;
}

/* ── FORM CARD ── */
.form-card {
    background: #0c1a12;
    border: 1px solid #162a1e;
    border-radius: 20px;
    padding: 36px 40px;
    margin-bottom: 40px;
}
.form-card h2 {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.5rem !important;
    font-weight: 800 !important;
    color: #ffffff !important;
    margin: 0 0 8px !important;
}
.form-card .form-sub {
    font-size: 0.9rem;
    color: #5a7a67;
    margin-bottom: 28px;
}

/* ── INPUT FIELDS ── */
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    background: #0a1510 !important;
    border: 1px solid #1c3326 !important;
    border-radius: 10px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
div[data-baseweb="input"] > div:focus-within,
div[data-baseweb="textarea"] > div:focus-within {
    border-color: #00e676 !important;
    box-shadow: 0 0 0 3px rgba(0, 230, 118, 0.12) !important;
}
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background: transparent !important;
    color: #e2ffe8 !important;
    font-size: 0.95rem !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-baseweb="input"] input::placeholder,
div[data-baseweb="textarea"] textarea::placeholder {
    color: #2e4a38 !important;
}

/* ── LABELS ── */
label[data-testid="stWidgetLabel"] p,
.stTextInput label, .stTextArea label {
    color: #8aab96 !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin-bottom: 6px !important;
}

/* ── SUBMIT BUTTON ── */
.stButton > button {
    background: linear-gradient(135deg, #00e676 0%, #00c853 100%) !important;
    color: #021509 !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    letter-spacing: 0.02em !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 32px !important;
    width: 100% !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 20px rgba(0, 230, 118, 0.25) !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(0, 230, 118, 0.4) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #00e676 !important; }

/* ── RESULT CARD ── */
.result-wrap {
    background: #0c1a12;
    border: 1px solid #00e676;
    border-radius: 20px;
    padding: 32px 36px;
    margin-top: 24px;
    box-shadow: 0 0 40px rgba(0, 230, 118, 0.07);
    animation: fadeInUp 0.4s ease;
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to   { opacity: 1; transform: translateY(0); }
}
.result-wrap h3 {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.15rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    margin: 0 0 20px !important;
}
.result-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 24px;
}
.tag {
    font-size: 0.8rem;
    font-weight: 600;
    padding: 5px 14px;
    border-radius: 20px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.tag-electrical { background: #0d2d5a; color: #60a5fa; border: 1px solid #1e4a8a; }
.tag-plumbing   { background: #062b1f; color: #34d399; border: 1px solid #0d5c3a; }
.tag-heating    { background: #3b0d0d; color: #f87171; border: 1px solid #7a1d1d; }
.tag-low        { background: #062b1f; color: #34d399; border: 1px solid #0d5c3a; }
.tag-medium     { background: #3b2200; color: #fbbf24; border: 1px solid #7a4c00; }
.tag-high       { background: #3b0d0d; color: #f87171; border: 1px solid #7a1d1d; }
.tag-review     { background: #1a0a3b; color: #a78bfa; border: 1px solid #3b1e7a; }

.result-block {
    background: #081210;
    border: 1px solid #142a1c;
    border-radius: 12px;
    padding: 18px 20px;
    margin-bottom: 14px;
}
.result-block-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #00e676;
    margin-bottom: 8px;
}
.result-block-text {
    font-size: 0.95rem;
    color: #c8d8cc;
    line-height: 1.6;
}

/* ── REVIEW ALERT ── */
.review-alert {
    background: #0a1a10;
    border: 1px solid #1a4a28;
    border-left: 4px solid #00e676;
    border-radius: 10px;
    padding: 14px 20px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.88rem;
    color: #69f0ae;
    font-weight: 500;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #14231b !important;
    gap: 4px !important;
    padding-bottom: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #4a6a58 !important;
    border: none !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    padding: 10px 20px !important;
    border-radius: 8px 8px 0 0 !important;
    transition: color 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: #0c1a12 !important;
    color: #00e676 !important;
    border-bottom: 2px solid #00e676 !important;
}

/* ── EXPANDER (history) ── */
.streamlit-expander {
    background: #0c1a12 !important;
    border: 1px solid #162a1e !important;
    border-radius: 12px !important;
    margin-bottom: 10px !important;
}
.streamlit-expander summary {
    color: #c8d8cc !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

/* ── ERROR / WARNING boxes ── */
div[data-testid="stAlert"] {
    background: #0f1e14 !important;
    border-radius: 10px !important;
    border-left-color: #00e676 !important;
    color: #c8d8cc !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# NAVBAR
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div class="navbar-brand">
        <span>🏛️</span>
        <span>FacilitiesAI</span>
    </div>
    <div class="navbar-status">
        <span class="navbar-dot" style="width:8px;height:8px;background:#00e676;border-radius:50%;box-shadow:0 0 8px #00e676;display:inline-block;"></span>
        AI Engine Live
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-tag">✦ AI-Powered Triage</div>
    <h1>Campus Facilities<br><span>Request Triage</span></h1>
    <p>Submit a maintenance request and receive an instant AI-assisted classification — category, priority, and recommended next action — powered by Qwen3 running locally via LM Studio.</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# FEATURE CARDS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="cards-row">
    <div class="feat-card">
        <span class="feat-icon">⚡</span>
        <h4>Instant Classification</h4>
        <p>AI categorises every request into Electrical, Plumbing, or Heating within seconds.</p>
    </div>
    <div class="feat-card">
        <span class="feat-icon">🔒</span>
        <h4>100% Local &amp; Private</h4>
        <p>Qwen3-VL-8B runs entirely on-premise via LM Studio. No data leaves your network.</p>
    </div>
    <div class="feat-card">
        <span class="feat-icon">📋</span>
        <h4>Always Human-Reviewed</h4>
        <p>Every AI suggestion is flagged for supervisor approval before any action is taken.</p>
    </div>
</div>
<hr class="section-divider">
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────────────────────────────────────
tab_submit, tab_history = st.tabs(["🚀  Submit Request", "📋  History"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Submit
# ══════════════════════════════════════════════════════════════════════════════
with tab_submit:
    st.markdown("""
    <div class="form-card">
        <h2>New Facilities Request</h2>
        <div class="form-sub">Fill in the details below. Our AI will classify and prioritise your request automatically.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("request_form", clear_on_submit=False):
        subject = st.text_input(
            "Subject",
            placeholder="e.g. Meeting room B3 lights are out",
            max_chars=100,
        )
        request_text = st.text_area(
            "Request Description",
            placeholder="Describe the problem in as much detail as possible — location, duration, impact…",
            height=180,
            max_chars=4000,
        )
        submitted = st.form_submit_button("🚀  Submit for Triage", use_container_width=True)

    if submitted:
        errors = []
        if len(subject) < 3:
            errors.append("Subject must be at least 3 characters.")
        if len(request_text) < 10:
            errors.append("Request description must be at least 10 characters.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            with st.spinner("Analysing with Qwen3… this may take a moment."):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/api/analyze",
                        json={"subject": subject, "request_text": request_text},
                        timeout=120,
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        cat  = data.get("category", "unknown")
                        pri  = data.get("priority", "unknown")
                        rev  = data.get("requires_review", True)

                        st.markdown(f"""
                        <div class="result-wrap">
                            <h3>✅ Analysis Complete</h3>
                            <div class="review-alert">
                                ⚠️&nbsp; <strong>Requires Human Review</strong> — This is an AI-generated suggestion only. Do not act without supervisor approval.
                            </div>
                            <div class="result-meta">
                                <span class="tag tag-{cat}">📂 {cat.upper()}</span>
                                <span class="tag tag-{pri}">🔥 Priority: {pri.upper()}</span>
                                <span class="tag tag-review">👁 Human Review Required</span>
                            </div>
                            <div class="result-block">
                                <div class="result-block-label">Summary</div>
                                <div class="result-block-text">{data.get('summary', '')}</div>
                            </div>
                            <div class="result-block">
                                <div class="result-block-label">Recommended Next Action</div>
                                <div class="result-block-text">{data.get('next_action', '')}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    elif resp.status_code == 422:
                        st.error(f"Input validation error: {resp.json().get('detail', 'Unknown error')}")
                    elif resp.status_code == 502:
                        st.error(f"AI inference error: {resp.json().get('detail', 'Inference failed')}")
                    else:
                        st.error(f"Unexpected API response {resp.status_code}: {resp.text[:200]}")

                except httpx.ConnectError:
                    st.error(f"Cannot connect to the API at {API_BASE}. Make sure the FastAPI server is running.")
                except httpx.TimeoutException:
                    st.error("The API request timed out. The model may be loading — please try again.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – History
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown("<h3 style='font-family:Syne,sans-serif;color:#fff;font-size:1.4rem;margin:16px 0 20px;'>Previous Triage Records</h3>", unsafe_allow_html=True)
    with col_btn:
        if st.button("🔄 Refresh"):
            st.rerun()

    try:
        hist_resp = httpx.get(f"{API_BASE}/api/history", timeout=10)
        if hist_resp.status_code == 200:
            records = hist_resp.json()
            if not records:
                st.info("No records yet. Submit a request first.")
            else:
                for rec in records:
                    cat  = rec.get("category", "")
                    pri  = rec.get("priority", "")
                    created = rec.get("created_at", "")[:19].replace("T", " ")
                    with st.expander(
                        f"#{rec['id']} — {rec['subject']}   |   {cat.upper()} · {pri.upper()}   |   {created}",
                        expanded=False,
                    ):
                        st.markdown(f"""
                        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
                            <span class="tag tag-{cat}">📂 {cat.upper()}</span>
                            <span class="tag tag-{pri}">🔥 {pri.upper()}</span>
                            <span class="tag tag-review">👁 Review Required</span>
                        </div>
                        <div class="result-block">
                            <div class="result-block-label">Summary</div>
                            <div class="result-block-text">{rec.get('summary', '')}</div>
                        </div>
                        <div class="result-block">
                            <div class="result-block-label">Next Action</div>
                            <div class="result-block-text">{rec.get('next_action', '')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        with st.expander("Original request text", expanded=False):
                            st.write(rec.get("request_text", ""))
        else:
            st.error(f"Failed to load history: {hist_resp.status_code}")
    except httpx.ConnectError:
        st.warning(f"Cannot connect to API at {API_BASE} to load history.")
    except Exception as exc:
        st.error(f"Error loading history: {exc}")
