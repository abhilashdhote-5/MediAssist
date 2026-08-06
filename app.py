import io
import os
import hashlib
from datetime import datetime
import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import build_mediassist_graph
from utils.helpers import load_json_file
from tools.appointment_tool import AppointmentTool
from tools.doctor_lookup import DoctorLookupTool

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediAssist AI",
    page_icon="⚕",
    layout="centered",
)

# ─── Global Design System & Custom CSS ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink: #007979;
    --ink-soft: #4A4A4A;
    --ink-muted: #8A8A8A;
    --paper: #FFFFFF;
    --panel: #FAFAFA;
    --line: #E7E7E5;
    --line-strong: #007979;
    --shadow-sm: 0 1px 2px rgba(0,121,121,0.05);
    --shadow-md: 0 4px 16px rgba(0,121,121,0.07);
    --primary-color: #007979 !important;
}

html, body, [class*="css"], .stApp, .main, section.main {
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, 'Segoe UI Emoji', 'Noto Color Emoji', sans-serif !important;
    color: var(--ink) !important;
}

/* ── Top signature rule ── */
[data-testid="stAppViewContainer"]::before {
    content: "";
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: var(--ink);
    z-index: 999999;
}

/* ── Page background ── */
.stApp, .main, section.main, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stMain"] {
    background-color: var(--paper) !important;
}
[data-testid="stHeader"] { background-color: transparent !important; }

/* ── Generic buttons ── */
button, .stButton > button, div[data-testid="stButton"] button,
button[kind="secondary"], button[kind="primary"], button[kind^="header"] {
    background-color: var(--paper) !important;
    color: var(--ink) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}
button:hover, .stButton > button:hover {
    background-color: var(--ink) !important;
    color: var(--paper) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* Primary "confirm" buttons (first column) */
div[data-testid="column"]:first-of-type .stButton button {
    background-color: var(--ink) !important;
    color: var(--paper) !important;
}
div[data-testid="column"]:first-of-type .stButton button:hover {
    background-color: #005f5f !important;
    color: var(--paper) !important;
}

/* ── Generic inputs ── */
input, textarea, select,
div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="base-input"] {
    border-color: var(--line) !important;
    border-radius: 6px !important;
    color: var(--ink) !important;
    background-color: var(--paper) !important;
}

a { color: var(--ink) !important; }
*:focus { outline-color: var(--ink) !important; }

/* ══════════════════════════════════════
   HERO
   ══════════════════════════════════════ */
.hero { margin-bottom: 2.2rem; }
.hero-eyebrow {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--ink-muted);
    margin: 0 0 0.6rem 0;
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.5rem;
    letter-spacing: -0.03em;
    line-height: 1.1;
    color: var(--ink);
    margin: 0 0 0.75rem 0;
}
.hero-rule {
    width: 46px;
    height: 3px;
    background: var(--ink);
    border-radius: 2px;
    margin-bottom: 0.9rem;
}
.hero-sub {
    font-size: 0.95rem;
    color: var(--ink-soft);
    max-width: 34rem;
    line-height: 1.5;
    margin: 0;
}

/* ══════════════════════════════════════
   EMPTY STATE
   ══════════════════════════════════════ */
.empty-state {
    border: 1px dashed var(--line);
    border-radius: 10px;
    padding: 2.4rem 1.5rem;
    text-align: center;
    color: var(--ink-muted);
    font-size: 0.88rem;
    margin: 1.5rem 0 2rem 0;
    background: var(--panel);
}
.empty-state strong {
    display: block;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1rem;
    color: var(--ink);
    font-weight: 600;
    margin-bottom: 0.4rem;
}

/* ══════════════════════════════════════
   SIDEBAR
   ══════════════════════════════════════ */
[data-testid="stSidebar"] {
    background-color: var(--panel);
    border-right: 1px solid var(--line);
}
[data-testid="stSidebar"] .block-container { padding-top: 2rem; }
[data-testid="stSidebar"] h3 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--ink-soft) !important;
    font-weight: 500 !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stSidebar"] .stTextInput input {
    font-family: 'IBM Plex Mono', monospace;
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
    background-color: var(--paper);
}
[data-testid="stSidebar"] hr {
    border-color: var(--line);
    margin: 1.4rem 0;
}

/* Patient info card */
.pat-card {
    background: var(--paper);
    border: 1px solid var(--line);
    border-radius: 10px;
    padding: 13px;
    margin: 8px 0;
    box-shadow: var(--shadow-sm);
}
.pat-card-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.76rem;
    padding: 4px 0;
    color: var(--ink-soft);
    border-bottom: 1px solid var(--line);
}
.pat-card-row:last-child { border-bottom: none; }
.pat-card-row span { color: var(--ink-muted); }
.pat-card-row strong { color: var(--ink); font-weight: 600; }

/* Agent pipeline */
.pipeline-section { margin-top: 0.5rem; }
.pipeline-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.63rem;
    font-weight: 500;
    color: var(--ink-muted);
    text-transform: uppercase;
    letter-spacing: 0.09em;
    margin-bottom: 8px;
}
.dag-pipeline { padding: 4px 0; }
.dag-step {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 0;
    font-size: 0.72rem;
    color: var(--ink-soft);
}
.dag-step-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--ink);
    flex-shrink: 0;
}
.dag-connector { width: 1px; height: 8px; background: var(--line); margin-left: 2px; }

/* Agent status readout */
.agent-status {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--ink-soft);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.75rem 0.85rem;
    margin-top: 0.4rem;
    background: var(--paper);
    box-shadow: var(--shadow-sm);
}
.agent-status .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--ink);
    flex-shrink: 0;
    animation: pulse 2s ease-in-out infinite;
}
.agent-status span {
    color: var(--ink);
    font-weight: 600;
}
@keyframes pulse {
    0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0,121,121,0.25); }
    50% { opacity: 0.55; box-shadow: 0 0 0 4px rgba(0,121,121,0); }
}
@media (prefers-reduced-motion: reduce) {
    .agent-status .dot { animation: none; }
}

/* ══════════════════════════════════════
   CHAT MESSAGES
   ══════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background-color: var(--paper);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.7rem;
    max-width: 82%;
    box-shadow: var(--shadow-sm);
}

/* User bubble — teal */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    margin-left: auto;
    background-color: var(--ink);
    border-color: var(--ink);
    border-bottom-right-radius: 3px;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) li,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) span,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) li,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) span,
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
    color: var(--paper) !important;
}

/* Assistant bubble — white */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]),
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
    margin-right: auto;
    background-color: var(--paper);
    border-color: var(--line);
    border-bottom-left-radius: 3px;
}

/* User avatar — teal with "U" */
[data-testid="stChatMessageAvatarUser"],
[data-testid="chatAvatarIcon-user"] {
    background-color: var(--ink) !important;
    position: relative;
    color: transparent !important;
    font-size: 0 !important;
}
[data-testid="stChatMessageAvatarUser"] img,
[data-testid="stChatMessageAvatarUser"] svg,
[data-testid="stChatMessageAvatarUser"] span,
[data-testid="chatAvatarIcon-user"] img,
[data-testid="chatAvatarIcon-user"] svg {
    display: none !important;
}
[data-testid="stChatMessageAvatarUser"]::after,
[data-testid="chatAvatarIcon-user"]::after {
    content: "U";
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--paper);
}

/* Assistant avatar — white with teal border and "AI" */
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="chatAvatarIcon-assistant"] {
    background-color: var(--paper) !important;
    border: 1px solid var(--ink) !important;
    position: relative;
    color: transparent !important;
    font-size: 0 !important;
}
[data-testid="stChatMessageAvatarAssistant"] img,
[data-testid="stChatMessageAvatarAssistant"] svg,
[data-testid="stChatMessageAvatarAssistant"] span,
[data-testid="chatAvatarIcon-assistant"] img,
[data-testid="chatAvatarIcon-assistant"] svg {
    display: none !important;
}
[data-testid="stChatMessageAvatarAssistant"]::after,
[data-testid="chatAvatarIcon-assistant"]::after {
    content: "AI";
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    color: var(--ink);
}

/* Node tag for agent info */
.node-tag {
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--paper); border: 1px solid var(--ink); color: var(--ink);
    font-family: 'IBM Plex Mono', monospace;
    padding: 2px 9px; border-radius: 99px; font-size: 0.63rem; font-weight: 500;
    letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px;
}

/* ══════════════════════════════════════
   CHAT INPUT
   ══════════════════════════════════════ */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"],
[data-testid="stChatInput"] textarea {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
}
[data-testid="stChatInput"] {
    border: 1px solid var(--ink) !important;
    border-radius: 14px !important;
    box-shadow: var(--shadow-md) !important;
}
[data-testid="stChatInput"] textarea {
    font-family: 'Inter', sans-serif;
    color: #0F0F0F !important;
}
[data-testid="stChatInput"] button {
    background-color: var(--ink) !important;
    border-radius: 50% !important;
    border: none !important;
}
[data-testid="stChatInput"] button svg {
    color: var(--paper) !important;
    fill: var(--paper) !important;
}

/* Bottom gradient fade */
html body [data-testid="stBottom"],
html body [data-testid="stBottom"] > div {
    background: linear-gradient(180deg, rgba(255,255,255,0) 0%, #FFFFFF 45%) !important;
    border-top: none !important;
}
html body [data-testid="stBottomBlockContainer"] {
    background: transparent !important;
    padding: 6px 18px 18px 18px !important;
}

/* ══════════════════════════════════════
   VOICE EXPANDER
   ══════════════════════════════════════ */
.voice-expander [data-testid="stExpander"] {
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    background-color: var(--panel);
    box-shadow: var(--shadow-sm);
}
.voice-expander [data-testid="stExpander"] summary {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    color: var(--ink-soft);
    padding: 0.55rem 0.85rem;
}
[data-testid="stAudioInput"] {
    border-radius: 10px !important;
    background-color: var(--paper) !important;
    border: 1px solid var(--line) !important;
}
[data-testid="stAudioInput"] button {
    background-color: var(--ink) !important;
    color: var(--paper) !important;
    border: none !important;
    border-radius: 50% !important;
}
[data-testid="stAudioInput"] button:hover {
    background-color: #005f5f !important;
    color: var(--paper) !important;
}

/* ══════════════════════════════════════
   HITL / PENDING ACTION CONTAINER
   ══════════════════════════════════════ */
[data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid var(--ink) !important;
    border-radius: 12px !important;
    background-color: var(--panel);
    box-shadow: var(--shadow-sm);
}

/* ══════════════════════════════════════
   ALERTS
   ══════════════════════════════════════ */
[data-testid="stAlert"], .stAlert, div[role="alert"] {
    background-color: var(--ink) !important;
    color: var(--paper) !important;
    border-radius: 8px !important;
}
[data-testid="stAlert"] p, .stAlert p, div[role="alert"] p,
[data-testid="stAlert"] *, .stAlert *, div[role="alert"] * {
    color: var(--paper) !important;
    font-weight: 500;
    letter-spacing: 0.01em;
}

/* ══════════════════════════════════════
   FORM LABELS & INPUTS
   ══════════════════════════════════════ */
label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--ink-soft) !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox [data-baseweb="select"] {
    border: 1px solid var(--line) !important;
    border-radius: 6px !important;
}
.stCheckbox label { text-transform: none; }
.stRadio label { text-transform: none; }

hr { border-color: var(--line); }

/* ══════════════════════════════════════
   QUICK ACTION BUTTONS
   ══════════════════════════════════════ */
.qa-btn .stButton > button {
    background: var(--paper) !important;
    border: 1px solid var(--line) !important;
    border-radius: 10px !important;
    padding: 14px !important;
    text-align: left !important;
    height: auto !important;
    white-space: normal !important;
    box-shadow: var(--shadow-sm) !important;
    font-size: 0.82rem !important;
}
.qa-btn .stButton > button:hover {
    border-color: var(--ink) !important;
    background: var(--ink) !important;
    color: var(--paper) !important;
}

/* ══════════════════════════════════════
   PDF BANNER
   ══════════════════════════════════════ */
.pdf-banner {
    display: flex; align-items: center; gap: 8px;
    background: var(--panel); border: 1px solid var(--ink);
    border-radius: 10px; padding: 9px 13px; margin-bottom: 12px;
    font-size: 0.78rem; color: var(--ink); font-weight: 600;
}

/* ══════════════════════════════════════
   PDF UPLOAD BUTTON — FIXED BESIDE CHAT INPUT
   ══════════════════════════════════════ */
[data-testid="stElementContainer"]:has(#pdf-upload-btn),
div:has(> #pdf-upload-btn),
.stMarkdown:has(#pdf-upload-btn) {
    position: fixed !important;
    bottom: 23px !important;
    left: max(18px, calc(50% - 345px)) !important;
    z-index: 999999 !important;
    width: auto !important;
    margin: 0 !important;
    padding: 0 !important;
}

.pdf-upload-row .stPopover > button,
.pdf-upload-row [data-testid="stPopover"] button {
    background: var(--paper) !important;
    border: 1px solid var(--ink) !important;
    border-radius: 50% !important;
    color: var(--ink) !important;
    font-size: 1.1rem !important;
    height: 2.4rem !important;
    width: 2.4rem !important;
    min-width: 2.4rem !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: background-color 0.15s ease, color 0.15s ease !important;
    box-shadow: var(--shadow-sm) !important;
}
.pdf-upload-row .stPopover > button:hover,
.pdf-upload-row [data-testid="stPopover"] button:hover {
    background: var(--ink) !important;
    border-color: var(--ink) !important;
    color: var(--paper) !important;
}

/* Make room for the fixed PDF button beside chat input */
html body [data-testid="stChatInput"] {
    margin-left: 50px !important;
}

/* File uploader inside popover */
[data-testid="stFileUploader"] {
    background: var(--paper) !important;
    border: 1px dashed var(--ink) !important;
    border-radius: 10px !important;
    padding: 10px !important;
}
[data-testid="stFileUploader"] label {
    color: var(--ink-soft) !important;
    font-size: 0.8rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--ink); border-radius: 99px; }
</style>
""", unsafe_allow_html=True)


# ─── Session State Bootstrap ────────────────────────────────────────────────────
if "graph_app" not in st.session_state:
    st.session_state.graph_app = build_mediassist_graph()

if "current_patient_id" not in st.session_state:
    st.session_state.current_patient_id = "PAT0001"

if "user_sessions" not in st.session_state:
    st.session_state.user_sessions = {}

if "queued_prompt" not in st.session_state:
    st.session_state.queued_prompt = None

if "processed_audio_hash" not in st.session_state:
    st.session_state.processed_audio_hash = None


def get_current_session() -> dict:
    pid = st.session_state.current_patient_id
    if pid not in st.session_state.user_sessions:
        st.session_state.user_sessions[pid] = {
            "chat_history": [],
            "hitl_pending": None,
            "active_agent": "Supervisor",
            "rag_pipeline": None,
            "uploaded_pdf_name": None,
        }
    return st.session_state.user_sessions[pid]


curr_session = get_current_session()


# ─── Hero Section ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <div class="hero">
        <p class="hero-eyebrow">Appointments · Symptoms · Medications · Reports</p>
        <h1 class="hero-title">MediAssist AI</h1>
        <div class="hero-rule"></div>
        <p class="hero-sub">Your intelligent assistant for appointments, symptoms, medications &amp; lab report analysis.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("Session Settings")

    patients = load_json_file("data/patients.json", default=[])
    patient_options = {
        f"{p['full_name']} ({p['patient_id']})": p["patient_id"] for p in patients
    }
    selected_label = st.selectbox(
        "Active Patient",
        options=list(patient_options.keys()),
        index=0,
    )
    new_pid = patient_options.get(selected_label, "PAT0001")
    if st.session_state.current_patient_id != new_pid:
        st.session_state.current_patient_id = new_pid
        st.rerun()

    # Patient info card
    curr_p = next(
        (p for p in patients if p["patient_id"] == st.session_state.current_patient_id),
        {},
    )
    if curr_p:
        allergies = ", ".join(curr_p.get("known_allergies", [])) or "None"
        conditions = ", ".join(curr_p.get("chronic_conditions", [])) or "None"
        st.markdown(
            f"""
        <div class="pat-card">
            <div class="pat-card-row"><span>Age / Sex</span><strong>{curr_p.get('age')} / {curr_p.get('gender')}</strong></div>
            <div class="pat-card-row"><span>Blood Group</span><strong>{curr_p.get('blood_group')}</strong></div>
            <div class="pat-card-row"><span>Allergies</span><strong>{allergies}</strong></div>
            <div class="pat-card-row"><span>Conditions</span><strong>{conditions}</strong></div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    if st.button("Clear Conversation"):
        curr_session["chat_history"] = []
        curr_session["hitl_pending"] = None
        curr_session["active_agent"] = "Supervisor"
        curr_session["rag_pipeline"] = None
        curr_session["uploaded_pdf_name"] = None
        st.rerun()

    st.divider()

    # Agent Pipeline
    st.markdown(
        """
    <div class="pipeline-section">
        <div class="pipeline-label">Agent Pipeline</div>
        <div class="dag-pipeline">
            <div class="dag-step"><div class="dag-step-dot"></div>Supervisor Router</div>
            <div class="dag-connector"></div>
            <div class="dag-step"><div class="dag-step-dot"></div>Appointment Agent</div>
            <div class="dag-connector"></div>
            <div class="dag-step"><div class="dag-step-dot"></div>Symptom Agent</div>
            <div class="dag-connector"></div>
            <div class="dag-step"><div class="dag-step-dot"></div>Medication Agent</div>
            <div class="dag-connector"></div>
            <div class="dag-step"><div class="dag-step-dot"></div>Report Agent</div>
            <div class="dag-connector"></div>
            <div class="dag-step"><div class="dag-step-dot"></div>Safety Reflection Node</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    active_agent = curr_session.get("active_agent", "Supervisor")
    st.markdown(
        f'<div class="agent-status"><span class="dot"></span>Active Agent&nbsp;<span>{active_agent}</span></div>',
        unsafe_allow_html=True,
    )


# ─── Chat Area ────────────────────────────────────────────────────────────────
patient_name = curr_p.get("full_name", "there") if curr_p else "there"
messages = curr_session["chat_history"]
chat_is_empty = len(messages) == 0

if chat_is_empty:
    st.markdown(
        """
        <div class="empty-state">
            <strong>No conversation yet</strong>
            Ask about appointments, symptoms, medications, or upload a lab report to get started.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Quick Actions
    qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)
    quick_actions = [
        (qa_col1, "📅", "Book Appointment", "I'd like to book a doctor's appointment.", "qa-appt"),
        (qa_col2, "🩺", "Check Symptoms", "I've been feeling unwell, can you help me understand my symptoms?", "qa-symp"),
        (qa_col3, "💊", "Medication Info", "Can you tell me about my current medications and possible interactions?", "qa-med"),
        (qa_col4, "📋", "Analyze Report", "I want to upload and analyze my lab report.", "qa-report"),
    ]
    for col, icon, label, prompt_text, key in quick_actions:
        with col:
            st.markdown('<div class="qa-btn">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=key, use_container_width=True):
                st.session_state.queued_prompt = prompt_text
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

# Chat History
for msg in messages:
    role = msg["role"]
    content = msg["content"]
    agent_info = msg.get("agent_info", None)
    with st.chat_message(role):
        if agent_info and role == "assistant":
            st.markdown(
                f"<div class='node-tag'>⬡ {agent_info}</div>", unsafe_allow_html=True
            )
        st.markdown(content)


# ─── HITL Appointment Confirmation ────────────────────────────────────────────
pending = curr_session.get("hitl_pending")
if pending:
    patient_id = pending.get("patient_id") or st.session_state.get(
        "current_patient_id"
    )
    action = pending.get("action", "book").capitalize()
    doctor = pending.get("doctor_name", "Unknown Doctor")
    specialty = pending.get("specialty", "")
    date_str = pending.get("date", "2026-08-10")
    time_slot = pending.get("time_slot", "")
    patient_nm = pending.get("patient_name", "")
    avail_slots = pending.get("available_slots", [])
    avail_days = pending.get("available_days", [])
    fee = pending.get("consultation_fee", 0)
    currency = pending.get("currency", "USD")
    days_str = ", ".join(avail_days) if avail_days else "All Week"

    try:
        default_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        default_date = datetime.now().date()

    with st.container(border=True):
        st.warning(f"📋 Confirm Appointment — {action}")
        st.caption(
            f"Patient: {patient_nm} · Doctor: {doctor} ({specialty}) · Available: {days_str} · Fee: {currency} {fee}"
        )

        # Doctor selection
        available_doctors = pending.get("available_doctors", [])
        chosen_doctor = None

        show_all_key = f"hitl_show_all_{patient_id}"
        try:
            show_all = st.checkbox("Show all doctors", key=show_all_key)
        except Exception:
            show_all = False

        if show_all:
            all_docs = DoctorLookupTool().search_doctors()
            if all_docs:
                available_doctors = all_docs

        filter_key = f"hitl_filter_{patient_id}"
        filter_text = st.text_input(
            "Filter doctors by name or specialty", key=filter_key
        )
        filtered_docs = available_doctors
        if filter_text:
            ft = filter_text.strip().lower()
            filtered_docs = [
                d
                for d in available_doctors
                if ft in d.get("full_name", "").lower()
                or ft in d.get("specialty", "").lower()
                or ft in d.get("qualification", "").lower()
            ]

        if filtered_docs:
            doc_labels = {
                d["doctor_id"]: f"{d.get('full_name')} — {d.get('qualification', '')} ({d.get('currency', '')}{d.get('consultation_fee', 0)})"
                for d in filtered_docs
            }
            doc_options = [d["doctor_id"] for d in filtered_docs]
            chosen_doc_id = st.radio(
                "👨‍⚕️ Choose preferred doctor",
                options=doc_options,
                format_func=lambda did: doc_labels.get(did, did),
                key=f"hitl_doctor_{patient_id}",
            )
            chosen_doctor = next(
                (d for d in filtered_docs if d.get("doctor_id") == chosen_doc_id),
                None,
            )
            if chosen_doctor:
                doctor = chosen_doctor.get("full_name", doctor)
                avail_slots = chosen_doctor.get("available_slots", avail_slots)
                avail_days = chosen_doctor.get("available_days", avail_days)

        col_slot, col_date = st.columns(2)
        with col_slot:
            chosen_slot = st.selectbox(
                "⏰ Choose time slot",
                options=avail_slots if avail_slots else [time_slot],
                key=f"hitl_slot_{st.session_state.current_patient_id}",
            )
        with col_date:
            chosen_date_obj = st.date_input(
                "📅 Appointment date",
                value=default_date,
                min_value=datetime.now().date(),
                key=f"hitl_date_{st.session_state.current_patient_id}",
            )
            chosen_date = chosen_date_obj.strftime("%Y-%m-%d")

        is_date_valid = bool(chosen_date_obj >= datetime.now().date())

        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button(
                "✅ Confirm Appointment",
                type="primary",
                use_container_width=True,
                disabled=not is_date_valid,
            ):
                with st.spinner("Processing..."):
                    tool = AppointmentTool()
                    if action.lower() == "cancel":
                        appts = tool.list_appointments(
                            patient_id=pending["patient_id"]
                        )
                        scheduled = [
                            a for a in appts if a.get("status") == "Scheduled"
                        ]
                        result = (
                            tool.cancel_appointment(scheduled[0]["appointment_id"])
                            if scheduled
                            else {
                                "status": "Error",
                                "message": "No scheduled appointment found.",
                            }
                        )
                    elif action.lower() == "reschedule":
                        appts = tool.list_appointments(
                            patient_id=pending["patient_id"]
                        )
                        scheduled = [
                            a
                            for a in appts
                            if a.get("status") in ("Scheduled", "Rescheduled")
                        ]
                        result = (
                            tool.reschedule_appointment(
                                scheduled[0]["appointment_id"],
                                chosen_date,
                                chosen_slot,
                            )
                            if scheduled
                            else {
                                "status": "Error",
                                "message": "No appointment to reschedule.",
                            }
                        )
                    else:
                        doctor_id_to_book = (
                            chosen_doctor.get("doctor_id")
                            if chosen_doctor
                            else pending.get("doctor_id", "DOC001")
                        )
                        result = tool.book_appointment(
                            patient_id=pending["patient_id"],
                            doctor_id=doctor_id_to_book,
                            date=chosen_date,
                            time_slot=chosen_slot,
                            reason="Patient requested via MediAssist AI",
                            patient_name=patient_nm,
                            doctor_name=doctor,
                        )

                    if result.get("status") == "Success":
                        appt = result.get("appointment", {})
                        confirm_msg = (
                            f"✅ **Appointment {action}d Successfully!**\n\n"
                            f"**ID:** `{appt.get('appointment_id', 'N/A')}`  |  "
                            f"**Doctor:** {appt.get('doctor_name', doctor)}\n"
                            f"**Date:** {appt.get('appointment_date', chosen_date)}  |  "
                            f"**Time:** {appt.get('time_slot', chosen_slot)}\n"
                            f"**Status:** {appt.get('status', 'Confirmed')}"
                        )
                        st.toast("Appointment confirmed!", icon="🎉")
                    else:
                        confirm_msg = f"❌ **{action} Failed:** {result.get('message', 'Unknown error.')}"
                        st.toast("Action failed.", icon="❌")

                    curr_session["chat_history"].append(
                        {
                            "role": "assistant",
                            "content": confirm_msg,
                            "agent_info": "Appointment Agent (Confirmed)",
                        }
                    )
                    curr_session["hitl_pending"] = None
                    st.rerun()

        with col_cancel:
            if st.button("✕ Decline", use_container_width=True):
                curr_session["chat_history"].append(
                    {
                        "role": "assistant",
                        "content": "Appointment action was **declined**. No changes were made to your records.",
                        "agent_info": "Appointment Agent (Declined)",
                    }
                )
                curr_session["hitl_pending"] = None
                st.toast("Declined.", icon="ℹ️")
                st.rerun()

# ─── PDF Banner ────────────────────────────────────────────────────────────────
if curr_session.get("uploaded_pdf_name"):
    st.markdown(
        f'<div class="pdf-banner">📄 <b>Attached:</b> {curr_session.get("uploaded_pdf_name")}'
        f" — Indexed with SentenceTransformers &amp; FAISS</div>",
        unsafe_allow_html=True,
    )


# ─── Core Message Processing Pipeline ─────────────────────────────────────────
def process_user_message(prompt: str):
    if not isinstance(prompt, str) or not prompt.strip():
        return

    session = get_current_session()
    session["chat_history"].append({"role": "user", "content": prompt.strip()})
    with st.chat_message("user"):
        st.markdown(prompt.strip())

    messages_history = [
        HumanMessage(content=str(m["content"]))
        if m["role"] == "user"
        else AIMessage(content=str(m["content"]))
        for m in session["chat_history"]
        if isinstance(m.get("content"), str)
    ]

    pdf_context = ""
    if session.get("rag_pipeline"):
        pdf_context = session["rag_pipeline"].query(prompt, top_k=4)

    initial_state = {
        "messages": messages_history,
        "patient_id": st.session_state.current_patient_id,
        "current_intent": "",
        "next_node": "",
        "agent_outputs": {},
        "final_response": "",
        "is_safe": True,
        "reflection_feedback": "",
        "pdf_context": pdf_context,
    }

    with st.chat_message("assistant"):
        with st.spinner(""):
            try:
                final_state = st.session_state.graph_app.invoke(initial_state)
                response = final_state.get(
                    "final_response",
                    "I'm unable to process your request at the moment.",
                )
                routed_node = (
                    final_state.get("current_intent", "Supervisor Routed").capitalize()
                    + " Agent"
                )
                session["active_agent"] = routed_node
                agent_outputs = final_state.get("agent_outputs", {})
                pending_action = agent_outputs.get("appointment_pending")

                st.markdown(
                    f"<div class='node-tag'>⬡ {routed_node}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(response)

                session["chat_history"].append(
                    {
                        "role": "assistant",
                        "content": response,
                        "agent_info": routed_node,
                    }
                )

                if pending_action:
                    session["hitl_pending"] = pending_action

                st.rerun()

            except Exception as e:
                st.error(f"LangGraph error: {str(e)}")


# ─── Bottom Input Bar ───────────────────────────────────────────────────────────
chat_prompt = None

if curr_session.get("hitl_pending"):
    st.info(
        "⏳ Please **confirm or decline** the appointment above before sending a new message."
    )
else:
    # Voice Input Expander
    st.markdown('<div class="voice-expander">', unsafe_allow_html=True)
    with st.expander("🎙️ Voice Input", expanded=False):
        st.caption("Record your message, then stop. Transcription is automatic.")
        audio_value = st.audio_input(
            label="Microphone",
            label_visibility="collapsed",
            key=f"voice_input_{st.session_state.current_patient_id}",
        )
        if audio_value is not None:
            raw_bytes = audio_value.read()
            audio_hash = hashlib.md5(raw_bytes).hexdigest()
            if st.session_state.processed_audio_hash != audio_hash:
                from utils.voice_input import transcribe_audio

                with st.spinner("🎙️ Transcribing…"):
                    transcribed = transcribe_audio(raw_bytes, filename="audio.webm")
                if transcribed:
                    st.session_state.queued_prompt = transcribed
                    st.session_state.processed_audio_hash = audio_hash
                    st.toast(f"🎙️ Heard: *{transcribed}*", icon="🎤")
                    st.rerun()
                else:
                    st.session_state.processed_audio_hash = None
                    st.caption("Could not transcribe audio — please try again.")
    st.markdown("</div>", unsafe_allow_html=True)

    # PDF Upload Button — fixed beside chat input
    st.markdown(
        '<div id="pdf-upload-btn" class="pdf-upload-row">', unsafe_allow_html=True
    )
    with st.popover("📎", help="Upload a medical PDF"):
        st.markdown("**📄 Upload Medical PDF**")
        st.caption("Lab reports, blood work, prescriptions")
        uploaded_file = st.file_uploader(
            "PDF",
            type=["pdf"],
            key=f"pdf_uploader_{st.session_state.current_patient_id}",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            if curr_session.get("uploaded_pdf_name") != uploaded_file.name:
                with st.spinner("Indexing with SentenceTransformers + FAISS…"):
                    from utils.rag_pipeline import AdvancedRAGPipeline

                    rag = AdvancedRAGPipeline()
                    res = rag.process_pdf_bytes(
                        uploaded_file.getvalue(), filename=uploaded_file.name
                    )
                    if res.get("status") == "Success":
                        curr_session["rag_pipeline"] = rag
                        curr_session["uploaded_pdf_name"] = uploaded_file.name
                        st.success(f"Indexed {res.get('num_chunks')} chunks ✓")
                        curr_session["chat_history"].append(
                            {
                                "role": "assistant",
                                "content": (
                                    f"📄 **Lab Report Indexed:** `{uploaded_file.name}` "
                                    f"({res.get('num_chunks')} semantic chunks).\n\n"
                                    "Ask me to explain, summarize, or flag abnormal values!"
                                ),
                                "agent_info": "Report RAG Pipeline",
                            }
                        )
                        st.toast(f"'{uploaded_file.name}' indexed!", icon="📄")
                        st.rerun()
                    else:
                        st.error(f"Failed: {res.get('message')}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Chat Input
    chat_prompt = st.chat_input("Ask MediAssist AI anything about your health…")


# ─── Process Prompt ───────────────────────────────────────────────────────────
final_prompt = None
if st.session_state.get("queued_prompt"):
    final_prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
elif isinstance(chat_prompt, str) and chat_prompt.strip():
    final_prompt = chat_prompt

if isinstance(final_prompt, str) and final_prompt.strip():
    process_user_message(final_prompt)