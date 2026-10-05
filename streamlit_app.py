"""
Streamlit UI – Facilities Request Triage Dashboard.

All provider / LM Studio logic lives in the FastAPI + AnalysisService layers.
This UI only calls the FastAPI REST endpoints.
"""
from __future__ import annotations

import os
from datetime import datetime

import httpx
import streamlit as st

# ---------------------------------------------------------------------------
# Configuration – read API base URL from env (set via Terraform/Docker)
# ---------------------------------------------------------------------------
API_BASE = os.getenv("API_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Facilities Request Triage",
    page_icon="🏛️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Playfair+Display:wght@700;800&display=swap');

    /* ---- global ---- */
    .stApp {
        background-color: #0b110e;
        color: #e2e8f0;
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Playfair Display', serif !important;
        color: #ffffff !important;
    }

    /* ---- header banner ---- */
    .header-banner {
        background: transparent;
        padding: 40px 0px 24px;
        margin-bottom: 24px;
    }
    .header-banner h1 { 
        margin: 0; 
        font-size: 3.5rem !important; 
        line-height: 1.1;
        letter-spacing: -0.02em;
    }
    .header-banner p { 
        margin: 16px 0 0; 
        color: #94a3b8; 
        font-size: 1.1rem; 
        max-width: 600px;
        line-height: 1.5;
    }

    /* ---- review banner ---- */
    .review-banner {
        background: #141b17;
        border-left: 4px solid #00e676;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 16px 0;
        color: #00e676;
        font-size: 1rem;
    }

    /* ---- result card ---- */
    .result-card {
        background: #111a15;
        border: 1px solid #1c2a22;
        border-radius: 12px;
        padding: 24px;
        margin-top: 16px;
    }
    
    /* ---- inputs ---- */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #111a15 !important;
        color: white !important;
        border: 1px solid #1c2a22 !important;
        border-radius: 8px !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #00e676 !important;
        box-shadow: 0 0 0 1px #00e676 !important;
    }
    
    /* ---- submit button ---- */
    .stButton > button {
        background-color: #00e676 !important;
        color: #000000 !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #00c853 !important;
        transform: translateY(-1px);
    }

    /* ---- category badge ---- */
    .badge-electrical { background:#1e3a8a; color:#bfdbfe; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }
    .badge-plumbing   { background:#064e3b; color:#a7f3d0; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }
    .badge-heating    { background:#7f1d1d; color:#fecaca; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }

    /* ---- priority badge ---- */
    .priority-low    { background:#064e3b; color:#a7f3d0; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }
    .priority-medium { background:#78350f; color:#fde68a; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }
    .priority-high   { background:#7f1d1d; color:#fecaca; padding:4px 12px; border-radius:20px; font-size:0.85rem; font-weight: 500; }

    /* ---- history table ---- */
    .hist-row {
        background: #111a15;
        border: 1px solid #1c2a22;
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="header-banner">
        <h1>🏛️ Facilities Request Triage</h1>
        <p>Submit a maintenance request to receive an AI-assisted classification. All results require human review.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_submit, tab_history = st.tabs(["📝 Submit Request", "📋 History"])

# ===========================================================================
# TAB 1 – Submit Request
# ===========================================================================
with tab_submit:
    st.subheader("New Facilities Request")

    with st.form("request_form", clear_on_submit=False):
        subject = st.text_input(
            "Subject *",
            placeholder="e.g. Meeting room lights fail",
            max_chars=100,
        )
        request_text = st.text_area(
            "Request Description *",
            placeholder="Describe the problem in detail…",
            height=160,
            max_chars=4000,
        )
        submitted = st.form_submit_button("🚀 Submit for Triage", use_container_width=True)

    if submitted:
        # Client-side length guard (mirrors API validation)
        errors = []
        if len(subject) < 3:
            errors.append("Subject must be at least 3 characters.")
        if len(request_text) < 10:
            errors.append("Request description must be at least 10 characters.")

        if errors:
            for err in errors:
                st.error(err)
        else:
            with st.spinner("Analysing request… this may take a moment."):
                try:
                    resp = httpx.post(
                        f"{API_BASE}/api/analyze",
                        json={"subject": subject, "request_text": request_text},
                        timeout=90,
                    )
                    if resp.status_code == 200:
                        data = resp.json()

                        # ── REVIEW BANNER ────────────────────────────────
                        st.markdown(
                            """
                            <div class="review-banner">
                            ⚠️ REQUIRES HUMAN REVIEW — This is an AI-generated triage suggestion only.
                            Do not action without supervisor approval.
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        # ── RESULT COLUMNS ───────────────────────────────
                        col1, col2 = st.columns(2)
                        with col1:
                            cat = data.get("category", "")
                            badge_cls = f"badge-{cat}"
                            st.markdown(
                                f"**Category:** <span class='{badge_cls}'>{cat.upper()}</span>",
                                unsafe_allow_html=True,
                            )
                            pri = data.get("priority", "")
                            pri_cls = f"priority-{pri}"
                            st.markdown(
                                f"**Priority:** <span class='{pri_cls}'>{pri.upper()}</span>",
                                unsafe_allow_html=True,
                            )
                        with col2:
                            st.markdown(
                                f"**Requires Review:** {'✅ Yes — human action required' if data.get('requires_review') else '❌ No'}"
                            )

                        st.markdown("---")
                        st.markdown(f"**Summary:**\n\n{data.get('summary','')}")
                        st.markdown(f"**Next Action:**\n\n{data.get('next_action','')}")

                    elif resp.status_code == 422:
                        detail = resp.json().get("detail", "Validation error")
                        st.error(f"Input validation error: {detail}")
                    elif resp.status_code == 502:
                        detail = resp.json().get("detail", "Inference failed")
                        st.error(f"AI inference error: {detail}")
                    else:
                        st.error(f"Unexpected API response {resp.status_code}: {resp.text[:200]}")

                except httpx.ConnectError:
                    st.error(
                        f"Cannot connect to the API at {API_BASE}. "
                        "Make sure the FastAPI server is running."
                    )
                except httpx.TimeoutException:
                    st.error("The API request timed out. The model may be loading — please try again.")
                except Exception as exc:
                    st.error(f"Unexpected error: {exc}")

# ===========================================================================
# TAB 2 – History
# ===========================================================================
with tab_history:
    st.subheader("Previous Triage Records")

    if st.button("🔄 Refresh History"):
        st.rerun()

    try:
        hist_resp = httpx.get(f"{API_BASE}/api/history", timeout=10)
        if hist_resp.status_code == 200:
            records = hist_resp.json()
            if not records:
                st.info("No records yet. Submit a request first.")
            else:
                for rec in records:
                    cat = rec.get("category", "")
                    pri = rec.get("priority", "")
                    badge_cls = f"badge-{cat}"
                    pri_cls = f"priority-{pri}"
                    created = rec.get("created_at", "")[:19].replace("T", " ")
                    with st.expander(
                        f"#{rec['id']} — {rec['subject']} | {cat.upper()} | {pri.upper()} | {created}",
                        expanded=False,
                    ):
                        st.markdown(
                            f"<span class='{badge_cls}'>{cat.upper()}</span>&nbsp;"
                            f"<span class='{pri_cls}'>{pri.upper()}</span>",
                            unsafe_allow_html=True,
                        )
                        st.markdown(f"**Summary:** {rec.get('summary','')}")
                        st.markdown(f"**Next Action:** {rec.get('next_action','')}")
                        st.markdown(
                            f"**Requires Review:** {'✅ Yes' if rec.get('requires_review') else '❌ No'}"
                        )
                        with st.expander("Original request text", expanded=False):
                            st.write(rec.get("request_text", ""))
        else:
            st.error(f"Failed to load history: {hist_resp.status_code}")
    except httpx.ConnectError:
        st.warning(f"Cannot connect to API at {API_BASE} to load history.")
    except Exception as exc:
        st.error(f"Error loading history: {exc}")
