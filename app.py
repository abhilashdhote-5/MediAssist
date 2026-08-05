import io
import os
import re
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage, AIMessage
from graph import build_mediassist_graph
from utils.helpers import load_json_file
from tools.appointment_tool import AppointmentTool
from tools.doctor_lookup import DoctorLookupTool

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediAssist AI",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Global Design System & Custom CSS ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap');

    /* ── Design Tokens (Soft Powder Blue & Sky Blue theme with Peach/Cream accents) ── */
    :root {
        --bg:            #BFDDF0;
        --bg-glow-a:     #8CC0EB;
        --bg-glow-b:     #FFEBCC;
        --surface:       #D2E6F5;
        --surface-2:     #EBF4FB;
        --surface-3:     #FFFFFF;
        --border:        rgba(140, 192, 235, 0.45);
        --border-md:     #8CC0EB;
        --border-strong: #5296CC;
        --accent:        #8CC0EB;
        --accent-2:      #5296CC;
        --accent-dim:    rgba(140, 192, 235, 0.30);
        --accent-glow:   rgba(140, 192, 235, 0.50);
        --cream:         #FFF9D2;
        --peach:         #FFEBCC;
        --teal:          #1F7199;
        --teal-dim:      rgba(140, 192, 235, 0.25);
        --green:         #169B62;
        --green-dim:     rgba(22, 155, 98, 0.15);
        --amber:         #D97706;
        --red:           #E11D48;
        --text-1:        #0C2336;
        --text-2:        #234B6E;
        --text-3:        #457096;
        --user-bubble:   linear-gradient(135deg, #FFEBCC 0%, #FFF9D2 100%);
        --ai-bubble:     #FFFFFF;
    }

    /* ── Global Reset ── */
    html, body, [class*="css"], .stApp {
        background:
            radial-gradient(1100px 620px at 15% -10%, var(--bg-glow-a) 0%, transparent 55%),
            radial-gradient(900px 700px at 100% 10%, var(--bg-glow-b) 0%, transparent 50%),
            var(--bg) !important;
        color: var(--text-1) !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
    }

    header, footer, #MainMenu { display: none !important; }
    [data-testid="stToolbar"] { display: none !important; }
    [data-testid="stDecoration"] { display: none !important; }

    .block-container {
        padding-top: 0 !important;
        padding-bottom: 7.5rem !important;
        max-width: 100% !important;
        padding-left: 0 !important;
        padding-right: 0 !important;
    }

    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: #8CC0EB; border-radius: 99px; }

    /* ══════════════════════════════════════
       SIDEBAR
    ══════════════════════════════════════ */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #8CC0EB 0%, #BFDDF0 100%) !important;
        border-right: 1.5px solid var(--border-md) !important;
        padding-top: 0 !important;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
    [data-testid="stSidebarContent"] { padding: 0 !important; }

    .sb-brand {
        display: flex;
        align-items: center;
        gap: 11px;
        padding: 20px 18px 16px 18px;
        border-bottom: 1.5px solid var(--border-md);
    }
    .sb-brand-icon {
        width: 36px; height: 36px;
        background: linear-gradient(135deg, #8CC0EB, #FFEBCC);
        border-radius: 11px;
        display: flex; align-items: center; justify-content: center;
        font-size: 17px; flex-shrink: 0;
        box-shadow: 0 4px 18px rgba(140,192,235,0.6);
        color: #0C2336;
    }
    .sb-brand-name {
        font-family: 'Sora', sans-serif;
        font-size: 0.95rem;
        font-weight: 700;
        color: var(--text-1);
        letter-spacing: -0.01em;
    }
    .sb-brand-sub { font-size: 0.68rem; color: var(--text-3); margin-top: 1px; }

    .sb-section { padding: 16px 18px 6px 18px; }
    .sb-section-label {
        font-size: 0.63rem;
        font-weight: 700;
        color: var(--text-3);
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 10px;
    }

    .pat-card {
        background: #FFFFFF;
        border: 1.5px solid var(--border-md);
        border-radius: 12px;
        padding: 13px;
        margin-bottom: 6px;
        box-shadow: 0 2px 10px rgba(140,192,235,0.25);
    }
    .pat-card-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.76rem;
        padding: 4px 0;
        color: var(--text-2);
        border-bottom: 1px solid rgba(140,192,235,0.3);
    }
    .pat-card-row:last-child { border-bottom: none; }
    .pat-card-row span { color: var(--text-3); }
    .pat-card-row strong { color: #1F7199; font-weight: 600; }

    .dag-pipeline { padding: 4px 0; }
    .dag-step {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 6px 0;
        font-size: 0.75rem;
        color: var(--text-2);
    }
    .dag-step-dot {
        width: 6px; height: 6px;
        border-radius: 50%;
        background: #5296CC;
        flex-shrink: 0;
        box-shadow: 0 0 7px rgba(82,150,204,0.5);
    }
    .dag-connector { width: 1px; height: 10px; background: var(--border-md); margin-left: 2px; }

    [data-testid="stSidebar"] .stSelectbox > div > div {
        background: #FFFFFF !important;
        border: 1.5px solid var(--border-md) !important;
        border-radius: 10px !important;
        color: var(--text-1) !important;
        font-size: 0.82rem !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: #FFFFFF !important;
        border: 1.5px solid var(--border-md) !important;
        color: var(--text-1) !important;
        border-radius: 10px !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        padding: 7px 12px !important;
        transition: all 0.15s ease !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #FFF9D2 !important;
        border-color: #8CC0EB !important;
        color: #0C2336 !important;
    }

    /* ══════════════════════════════════════
       MAIN AREA & STATIC HEADER
    ══════════════════════════════════════ */
    .main-wrapper {
        max-width: 860px;
        margin: 0 auto;
        padding: 0 24px;
    }

    .sticky-header-container {
        position: sticky;
        top: 0;
        z-index: 999;
        background: #BFDDF0;
        padding-top: 20px;
        padding-bottom: 12px;
        border-bottom: 1.5px solid var(--border-md);
        margin-bottom: 20px;
    }

    .chat-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
    }
    .chat-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #FFEBCC;
        border: 1px solid #F7D7A3;
        border-radius: 20px;
        padding: 4px 11px;
        font-size: 0.65rem;
        font-weight: 700;
        color: #7A4B00;
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .chat-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: #D97706; animation: pulse-dot 2s infinite; }
    @keyframes pulse-dot { 0%,100%{opacity:1;transform:scale(1);} 50%{opacity:.4;transform:scale(.8);} }

    .hero-greeting { font-size: 0.95rem; color: var(--text-2); margin-top: 16px; }
    .hero-title {
        font-family: 'Sora', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #0C2336;
        letter-spacing: -0.03em;
        line-height: 1.15;
        margin-top: 2px;
        margin-bottom: 6px;
        background: linear-gradient(90deg, #0C2336 40%, #234B6E 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .hero-subtitle { font-size: 0.85rem; color: var(--text-2); margin-bottom: 22px; }

    /* ── Robot mascot ── */
    .mascot-wrap {
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 8px 0 26px 0;
    }
    .mascot-orb {
        width: 128px; height: 128px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 62px;
        background: radial-gradient(circle at 35% 30%, #8CC0EB 0%, #BFDDF0 70%);
        border: 3px solid #FFFFFF;
        box-shadow: 0 12px 40px rgba(140,192,235,0.6), inset 0 0 30px rgba(255,249,210,0.5);
        animation: float-bot 4.5s ease-in-out infinite;
    }
    @keyframes float-bot { 0%,100%{transform:translateY(0px);} 50%{transform:translateY(-9px);} }

    /* ── Quick action cards ── */
    .qa-label { font-size: 0.68rem; font-weight: 700; color: var(--text-3); text-transform: uppercase; letter-spacing: 0.08em; margin: 4px 0 10px 2px; }
    .cap-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 8px; }

    .stButton.qa-button > button {
        background: #FFFFFF !important;
        border: 1.5px solid var(--border-md) !important;
        border-radius: 14px !important;
        padding: 16px 14px !important;
        text-align: left !important;
        height: auto !important;
        white-space: normal !important;
        color: var(--text-1) !important;
        transition: all 0.18s ease !important;
        width: 100% !important;
        box-shadow: 0 3px 12px rgba(140,192,235,0.25) !important;
    }
    .stButton.qa-button > button:hover {
        border-color: #5296CC !important;
        background: #FFF9D2 !important;
        transform: translateY(-2px);
        box-shadow: 0 10px 24px rgba(140,192,235,0.45) !important;
    }

    @media (max-width: 700px) { .cap-grid { grid-template-columns: repeat(2, 1fr); } }

    .pulse-divider { width: 100%; height: 20px; margin: 6px 0 20px 0; opacity: 0.7; }

    /* ══════════════════════════════════════
       STATUS CHIPS
    ══════════════════════════════════════ */
    .status-bar { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 0; }
    .status-chip {
        display: inline-flex; align-items: center; gap: 6px;
        background: #FFFFFF; border: 1.5px solid var(--border-md);
        border-radius: 8px; padding: 6px 11px; font-size: 0.72rem; color: var(--text-2);
        box-shadow: 0 2px 8px rgba(140,192,235,0.2);
    }
    .status-chip .chip-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 5px var(--green-dim); }
    .status-chip .chip-label { color: var(--text-3); text-transform: uppercase; font-size: 0.6rem; letter-spacing: 0.06em; font-weight: 700; }
    .status-chip .chip-value { color: var(--text-1); font-weight: 600; }

    /* ══════════════════════════════════════
       CHAT MESSAGES
    ══════════════════════════════════════ */
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        max-width: 100% !important;
        width: 100% !important;
        margin-bottom: 10px !important;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { width: 100% !important; }

    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-user"],
    [data-testid="stChatMessage"] [data-testid="chatAvatarIcon-assistant"] {
        background: #FFFFFF !important;
        border: 1.5px solid #8CC0EB !important;
        border-radius: 9px !important;
        width: 30px !important; height: 30px !important;
        font-size: 12px !important;
    }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) .stMarkdown {
        background: var(--user-bubble) !important;
        border: 1.5px solid #F7D7A3 !important;
        border-radius: 14px 14px 4px 14px !important;
        padding: 14px 18px !important;
        margin-left: 8px;
        box-shadow: 0 6px 18px rgba(255, 235, 204, 0.6);
    }
    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) p { color: #0C2336 !important; }

    [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) .stMarkdown {
        background: var(--ai-bubble) !important;
        border: 1.5px solid #8CC0EB !important;
        border-radius: 14px 14px 14px 4px !important;
        padding: 14px 18px !important;
        margin-right: 8px;
        box-shadow: 0 4px 14px rgba(140, 192, 235, 0.25);
    }

    [data-testid="stChatMessage"] p { font-size: 0.875rem !important; line-height: 1.65 !important; color: var(--text-1) !important; margin-bottom: 6px !important; }
    [data-testid="stChatMessage"] strong { color: #0C2336 !important; font-weight: 700 !important; }
    [data-testid="stChatMessage"] code {
        font-family: 'Geist Mono', 'Fira Code', monospace !important;
        background: #EBF4FB !important; border: 1px solid #8CC0EB !important;
        padding: 1px 5px !important; border-radius: 4px !important; font-size: 0.8rem !important; color: #1F7199 !important;
    }
    [data-testid="stChatMessage"] pre { background: #EBF4FB !important; border: 1px solid #8CC0EB !important; border-radius: 8px !important; padding: 12px !important; overflow-x: auto !important; }
    [data-testid="stChatMessage"] ul, [data-testid="stChatMessage"] ol { padding-left: 18px !important; }
    [data-testid="stChatMessage"] li { font-size: 0.875rem !important; line-height: 1.65 !important; color: var(--text-1) !important; margin-bottom: 2px !important; }
    [data-testid="stChatMessage"] h1, [data-testid="stChatMessage"] h2, [data-testid="stChatMessage"] h3, [data-testid="stChatMessage"] h4 { color: var(--text-1) !important; margin-top: 8px !important; margin-bottom: 6px !important; }

    .node-tag {
        display: inline-flex; align-items: center; gap: 5px;
        background: #FFEBCC; border: 1px solid #F7D7A3; color: #7A4B00;
        padding: 2px 9px; border-radius: 99px; font-size: 0.63rem; font-weight: 700;
        letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 8px;

    /* ══════════════════════════════════════
       FIXED UNIFIED BOTTOM INPUT BAR
    ══════════════════════════════════════ */

    /* Bottom gradient fade background */
    html body [data-testid="stBottom"],
    html body [data-testid="stBottom"] > div {
        background: linear-gradient(180deg, rgba(191,221,240,0) 0%, #BFDDF0 35%) !important;
        border-top: none !important;
    }

    /* Bottom container layout */
    html body [data-testid="stBottomBlockContainer"],
    html body .stChatFloatingInputContainer {
        background: transparent !important;
        max-width: 900px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 6px 18px 18px 18px !important;
    }

    /* ── Chat input pill ── */
    html body [data-testid="stChatInput"] {
        background: #FFFFFF !important;
        border: 2px solid #8CC0EB !important;
        border-radius: 999px !important;
        box-shadow: 0 6px 24px rgba(140,192,235,0.35) !important;
        transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
        margin-left: 95px !important; /* Make room for fixed 📎 and 🎤 buttons on left */
    }
    html body [data-testid="stChatInput"]:focus-within {
        border-color: #5296CC !important;
        box-shadow: 0 0 0 3px rgba(140,192,235,0.4), 0 6px 24px rgba(140,192,235,0.35) !important;
    }
    html body [data-testid="stChatInput"] [data-baseweb="textarea"],
    html body [data-testid="stChatInput"] [data-baseweb="base-input"] {
        background: transparent !important;
        border: none !important;
    }
    html body [data-testid="stChatInput"] textarea {
        color: #0C2336 !important;
        -webkit-text-fill-color: #0C2336 !important;
        caret-color: #5296CC !important;
        font-size: 0.9rem !important;
        font-family: 'Inter', sans-serif !important;
        background: transparent !important;
        padding: 12px 18px !important;
        line-height: 1.5 !important;
    }
    html body [data-testid="stChatInput"] textarea::placeholder {
        color: #457096 !important;
        opacity: 1 !important;
    }
    /* Send button inside the pill */
    html body [data-testid="stChatInput"] button {
        background: linear-gradient(135deg, #8CC0EB, #5296CC) !important;
        border-radius: 50% !important;
        width: 2rem !important;
        height: 2rem !important;
        transition: transform 0.1s ease !important;
    }
    html body [data-testid="stChatInput"] button:hover {
        transform: scale(1.08) !important;
    }
    html body [data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
    }

    /* ── FIXED Bottom action buttons row (📎 upload + 🎤 mic) ── */
    [data-testid="stElementContainer"]:has(#bottom-actions-container),
    div:has(> #bottom-actions-container),
    .stMarkdown:has(#bottom-actions-container) {
        position: fixed !important;
        bottom: 24px !important;
        left: calc(50% - 432px) !important;
        z-index: 999999 !important;
        width: auto !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    #bottom-actions-container {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    .bottom-actions-row .stPopover > button,
    .bottom-actions-row [data-testid="stPopover"] button {
        background: #FFFFFF !important;
        border: 2px solid #8CC0EB !important;
        border-radius: 50% !important;
        color: #0C2336 !important;
        font-size: 1.1rem !important;
        height: 2.5rem !important;
        width: 2.5rem !important;
        min-width: 2.5rem !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.15s ease !important;
        box-shadow: 0 4px 12px rgba(140,192,235,0.3) !important;
    }
    .bottom-actions-row .stPopover > button:hover,
    .bottom-actions-row [data-testid="stPopover"] button:hover {
        background: #FFF9D2 !important;
        border-color: #5296CC !important;
        transform: scale(1.05) !important;
    }

    /* Audio input mic button styling */
    .bottom-actions-row [data-testid="stAudioInput"] {
        display: block !important;
    }
    .bottom-actions-row [data-testid="stAudioInput"] > label {
        display: none !important;
    }
    .bottom-actions-row [data-testid="stAudioInput"] button {
        background: #FFFFFF !important;
        border: 2px solid #8CC0EB !important;
        border-radius: 50% !important;
        color: #0C2336 !important;
        height: 2.5rem !important;
        width: 2.5rem !important;
        min-width: 2.5rem !important;
        padding: 0 !important;
        box-shadow: 0 4px 12px rgba(140,192,235,0.3) !important;
        transition: all 0.15s ease !important;
    }
    .bottom-actions-row [data-testid="stAudioInput"] button:hover {
        background: #FFF9D2 !important;
        border-color: #5296CC !important;
        transform: scale(1.05) !important;
    }

    /* Hide default audio-input if outside bottom-actions-row */
    [data-testid="stAudioInput"]:not(.bottom-actions-row [data-testid="stAudioInput"]) {
        display: none !important;
    }

    /* ══════════════════════════════════════
       HITL FORM & MISC WIDGETS
    ══════════════════════════════════════ */
    .hitl-card {
        background: #FFFFFF;
        border: 2px solid #8CC0EB;
        border-radius: 16px;
        padding: 20px 22px;
        margin: 16px 0;
        box-shadow: 0 6px 24px rgba(140,192,235,0.35);
    }
    .hitl-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
    .hitl-title { font-family: 'Sora', sans-serif; font-size: 0.95rem; font-weight: 700; color: var(--text-1); }
    .hitl-badge {
        background: #FFEBCC; border: 1px solid #F7D7A3; color: #7A4B00;
        font-size: 0.62rem; font-weight: 700; padding: 3px 9px; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .hitl-detail-row { font-size: 0.8rem; color: var(--text-2); margin-bottom: 4px; line-height: 1.6; }
    .hitl-detail-row b { color: var(--text-1); font-weight: 500; }

    .stButton > button {
        background: #FFFFFF !important;
        border: 1.5px solid #8CC0EB !important;
        color: #0C2336 !important;
        border-radius: 10px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover { background: #FFF9D2 !important; border-color: #5296CC !important; color: #0C2336 !important; }
    [data-testid="baseButton-primary"] { background: linear-gradient(135deg, #8CC0EB, #5296CC) !important; border: none !important; color: #FFFFFF !important; }
    [data-testid="baseButton-primary"]:hover { filter: brightness(1.08); }

    .stSelectbox > div > div {
        background: #FFFFFF !important; border: 1.5px solid #8CC0EB !important;
        border-radius: 10px !important; color: #0C2336 !important; font-size: 0.82rem !important;
    }
    .stDateInput > div > div > input {
        background: #FFFFFF !important; border: 1.5px solid #8CC0EB !important;
        border-radius: 10px !important; color: #0C2336 !important; font-size: 0.82rem !important;
    }

    [data-testid="stAlert"] { background: #FFFFFF !important; border: 1.5px solid #8CC0EB !important; border-radius: 12px !important; color: #0C2336 !important; font-size: 0.82rem !important; }

    hr { border-color: var(--border-md) !important; margin: 12px 0 !important; }

    [data-testid="stFileUploader"] { background: #FFFFFF !important; border: 1.5px dashed #8CC0EB !important; border-radius: 10px !important; padding: 10px !important; }
    [data-testid="stFileUploader"] label { color: var(--text-2) !important; font-size: 0.8rem !important; }

    .stCaption, [data-testid="stCaption"] { color: var(--text-3) !important; font-size: 0.72rem !important; }
    [data-testid="column"] { padding: 0 6px !important; }

    .pdf-banner {
        display: flex; align-items: center; gap: 8px;
        background: #FFEBCC; border: 1.5px solid #F7D7A3;
        border-radius: 10px; padding: 9px 13px; margin-bottom: 12px; font-size: 0.78rem; color: #7A4B00; font-weight: 600;
    }
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


def get_current_session() -> dict:
    pid = st.session_state.current_patient_id
    if pid not in st.session_state.user_sessions:
        st.session_state.user_sessions[pid] = {
            "chat_history": [],
            "hitl_pending": None,
            "active_agent": "Awaiting query",
            "rag_pipeline": None,
            "uploaded_pdf_name": None,
        }
    return st.session_state.user_sessions[pid]


curr_session = get_current_session()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sb-brand">
        <div class="sb-brand-icon">⚕</div>
        <div>
            <div class="sb-brand-name">MediAssist AI</div>
            <div class="sb-brand-sub">Multi-agent healthcare intelligence</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section"><div class="sb-section-label">Active Patient</div>', unsafe_allow_html=True)
    patients = load_json_file("data/patients.json", default=[])
    patient_options = {f"{p['full_name']} ({p['patient_id']})": p["patient_id"] for p in patients}
    selected_label = st.selectbox(
        "Patient",
        options=list(patient_options.keys()),
        index=0,
        label_visibility="collapsed",
    )
    new_pid = patient_options.get(selected_label, "PAT0001")
    if st.session_state.current_patient_id != new_pid:
        st.session_state.current_patient_id = new_pid
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    curr_p = next((p for p in patients if p["patient_id"] == st.session_state.current_patient_id), {})
    if curr_p:
        allergies = ", ".join(curr_p.get("known_allergies", [])) or "None"
        conditions = ", ".join(curr_p.get("chronic_conditions", [])) or "None"
        st.markdown(f"""
        <div class="sb-section">
        <div class="pat-card">
            <div class="pat-card-row"><span>Age / Sex</span><strong>{curr_p.get('age')} / {curr_p.get('gender')}</strong></div>
            <div class="pat-card-row"><span>Blood Group</span><strong>{curr_p.get('blood_group')}</strong></div>
            <div class="pat-card-row"><span>Allergies</span><strong>{allergies}</strong></div>
            <div class="pat-card-row"><span>Conditions</span><strong>{conditions}</strong></div>
        </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="sb-section">
    <div class="sb-section-label">Agent Pipeline</div>
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
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:1px;background:var(--border);margin:8px 0'></div>", unsafe_allow_html=True)

    st.markdown('<div class="sb-section">', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        curr_session["chat_history"] = []
        curr_session["hitl_pending"] = None
        curr_session["active_agent"] = "Awaiting query"
        curr_session["rag_pipeline"] = None
        curr_session["uploaded_pdf_name"] = None
        st.toast("Chat cleared.", icon="🧹")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ─── Main Chat Area Wrapper ────────────────────────────────────────────────────
patient_name = curr_p.get("full_name", "there") if curr_p else "there"
first_name = patient_name.split(" ")[0] if patient_name else "there"
active_agent = curr_session.get("active_agent", "Awaiting query")
chat_is_empty = len(curr_session["chat_history"]) == 0

st.markdown('<div class="main-wrapper">', unsafe_allow_html=True)

# ─── FIXED STATIC HEADER (Pinned top banner) ───────────────────────────────────
st.markdown(f"""
<div class="sticky-header-container">
    <div class="chat-header">
        <div class="chat-badge"><div class="chat-badge-dot"></div>AI SPECIALIST CHAT</div>
    </div>
    <div class="status-bar">
        <div class="status-chip">
            <div class="chip-dot"></div>
            <span class="chip-label">PATIENT</span>
            <span class="chip-value">{patient_name}</span>
        </div>
        <div class="status-chip">
            <div class="chip-dot" style="background:var(--accent); box-shadow:0 0 5px var(--accent-glow);"></div>
            <span class="chip-label">ACTIVE AGENT</span>
            <span class="chip-value">{active_agent}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if chat_is_empty:
    st.markdown(f"""
    <div class="hero-greeting">Hi, {first_name} 👋</div>
    <div class="hero-title">How may I help you today?</div>
    <div class="hero-subtitle">Your intelligent assistant for appointments, symptoms, medications & lab report analysis.</div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="mascot-wrap"><div class="mascot-orb">🤖</div></div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="qa-label">Quick Actions</div>', unsafe_allow_html=True)
    qa_col1, qa_col2, qa_col3, qa_col4 = st.columns(4)
    quick_actions = [
        (qa_col1, "📅", "Book Appointment", "I'd like to book a doctor's appointment.", "cap-appt"),
        (qa_col2, "🩺", "Check Symptoms", "I've been feeling unwell, can you help me understand my symptoms?", "cap-symp"),
        (qa_col3, "💊", "Medication Info", "Can you tell me about my current medications and possible interactions?", "cap-med"),
        (qa_col4, "📋", "Analyze Lab Report", "I want to upload and analyze my lab report.", "cap-report"),
    ]
    for col, icon, label, prompt_text, key in quick_actions:
        with col:
            st.markdown('<div class="stButton qa-button">', unsafe_allow_html=True)
            if st.button(f"{icon}  {label}", key=key, use_container_width=True):
                st.session_state.queued_prompt = prompt_text
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("""
    <svg class="pulse-divider" viewBox="0 0 820 18" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
      <polyline points="0,9 260,9 285,1 308,17 330,3 352,9 820,9"
        fill="none" stroke="url(#grad)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      <defs>
        <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#8CC0EB"/>
            <stop offset="100%" stop-color="#FFEBCC"/>
        </linearGradient>
      </defs>
    </svg>
    """, unsafe_allow_html=True)


# ─── HITL Confirmation Function Definition ─────────────────────────────────────
def render_hitl_confirmation():
    pending = curr_session.get("hitl_pending")
    if not pending:
        return

    # Ensure we have a patient id available for widget keys and lookups
    patient_id = pending.get("patient_id") or st.session_state.get("current_patient_id")

    action     = pending.get("action", "book").capitalize()
    doctor     = pending.get("doctor_name", "Unknown Doctor")
    specialty  = pending.get("specialty", "")
    date_str   = pending.get("date", "2026-08-10")
    time_slot  = pending.get("time_slot", "")
    patient_nm = pending.get("patient_name", "")
    avail_slots = pending.get("available_slots", [])
    avail_days  = pending.get("available_days", [])
    fee        = pending.get("consultation_fee", 0)
    currency   = pending.get("currency", "USD")
    days_str   = ", ".join(avail_days) if avail_days else "All Week"

    try:
        default_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        default_date = datetime.now().date()

    st.markdown(f"""
    <div class="hitl-card">
        <div class="hitl-header">
            <div class="hitl-title">📋 Confirm Appointment — {action}</div>
            <div class="hitl-badge">Human Validation Required</div>
        </div>
        <div class="hitl-detail-row"><b>Patient:</b> {patient_nm} &nbsp;|&nbsp; <b>Doctor:</b> {doctor} ({specialty})</div>
        <div class="hitl-detail-row"><b>Available Days:</b> {days_str} &nbsp;|&nbsp; <b>Consultation Fee:</b> {currency} {fee}</div>
    </div>
    """, unsafe_allow_html=True)

    # Allow the user to pick from matching doctors (HITL)
    available_doctors = pending.get("available_doctors", [])
    chosen_doctor = None
    # Offer an option to expand to the full doctor directory
    show_all_key = f"hitl_show_all_{patient_id}"
    try:
        show_all = st.checkbox("Show all doctors", key=show_all_key)
    except Exception:
        show_all = False

    if show_all:
        # Load the full doctor directory
        all_docs = DoctorLookupTool().search_doctors()
        if all_docs:
            available_doctors = all_docs

    # Text filter to help patients find a doctor quickly
    filter_key = f"hitl_filter_{patient_id}"
    filter_text = st.text_input("Filter doctors by name or specialty", key=filter_key)
    filtered_docs = available_doctors
    if filter_text:
        ft = filter_text.strip().lower()
        filtered_docs = [d for d in available_doctors if ft in d.get("full_name", "").lower() or ft in d.get("specialty", "").lower() or ft in d.get("qualification", "").lower()]

    if filtered_docs:
        doc_labels = {d["doctor_id"]: f"{d.get('full_name')} — {d.get('qualification','')} ({d.get('currency','')}{d.get('consultation_fee',0)})" for d in filtered_docs}
        doc_options = [d["doctor_id"] for d in filtered_docs]
        # Use radio for clearer single-choice selection and better visibility
        chosen_doc_id = st.radio(
            "👨‍⚕️ Choose preferred doctor",
            options=doc_options,
            format_func=lambda did: doc_labels.get(did, did),
            key=f"hitl_doctor_{patient_id}",
        )
        chosen_doctor = next((d for d in filtered_docs if d.get("doctor_id") == chosen_doc_id), None)
        if chosen_doctor:
            doctor = chosen_doctor.get("full_name", doctor)
            # Update available slots/days to reflect chosen doctor
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
        if st.button("✅ Confirm Appointment", type="primary", use_container_width=True, disabled=not is_date_valid):
            with st.spinner("Processing..."):
                tool = AppointmentTool()
                if action.lower() == "cancel":
                    appts = tool.list_appointments(patient_id=pending["patient_id"])
                    scheduled = [a for a in appts if a.get("status") == "Scheduled"]
                    result = tool.cancel_appointment(scheduled[0]["appointment_id"]) if scheduled else \
                             {"status": "Error", "message": "No scheduled appointment found."}
                elif action.lower() == "reschedule":
                    appts = tool.list_appointments(patient_id=pending["patient_id"])
                    scheduled = [a for a in appts if a.get("status") in ("Scheduled", "Rescheduled")]
                    result = tool.reschedule_appointment(scheduled[0]["appointment_id"], chosen_date, chosen_slot) \
                             if scheduled else {"status": "Error", "message": "No appointment to reschedule."}
                else:
                    # If user selected a different doctor in HITL, use that doctor's id
                    doctor_id_to_book = (chosen_doctor.get("doctor_id") if chosen_doctor else pending.get("doctor_id", "DOC001"))
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
                    msg = (
                        f"✅ **Appointment {action}d Successfully!**\n\n"
                        f"**ID:** `{appt.get('appointment_id', 'N/A')}`  |  "
                        f"**Doctor:** {appt.get('doctor_name', doctor)}\n"
                        f"**Date:** {appt.get('appointment_date', chosen_date)}  |  "
                        f"**Time:** {appt.get('time_slot', chosen_slot)}\n"
                        f"**Status:** {appt.get('status', 'Confirmed')}"
                    )
                    st.toast("Appointment confirmed!", icon="🎉")
                else:
                    msg = f"❌ **{action} Failed:** {result.get('message', 'Unknown error.')}"
                    st.toast("Action failed.", icon="❌")

                curr_session["chat_history"].append(
                    {"role": "assistant", "content": msg, "agent_info": "Appointment Agent (Confirmed)"}
                )
                curr_session["hitl_pending"] = None
                st.rerun()

    with col_cancel:
        if st.button("✕ Decline", use_container_width=True):
            curr_session["chat_history"].append({
                "role": "assistant",
                "content": "Appointment action was **declined**. No changes were made to your records.",
                "agent_info": "Appointment Agent (Declined)",
            })
            curr_session["hitl_pending"] = None
            st.toast("Declined.", icon="ℹ️")
            st.rerun()


# ─── Chat History ──────────────────────────────────────────────────────────────
for message in curr_session["chat_history"]:
    role = message["role"]
    content = message["content"]
    agent_info = message.get("agent_info", None)

    with st.chat_message(role):
        if agent_info and role == "assistant":
            st.markdown(f"<div class='node-tag'>⬡ {agent_info}</div>", unsafe_allow_html=True)
        st.markdown(content)

# ─── HITL Confirmation (Rendered AT THE BOTTOM of the chat thread) ──────────────
render_hitl_confirmation()

# ─── PDF Banner ────────────────────────────────────────────────────────────────
if curr_session.get("uploaded_pdf_name"):
    st.markdown(
        f'<div class="pdf-banner">📄 <b>Attached:</b> {curr_session.get("uploaded_pdf_name")}'
        f' — Indexed with SentenceTransformers & FAISS</div>',
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)  # close main-wrapper


# ─── Core message-processing pipeline ─────────────────────────────────────────
def process_user_message(prompt: str):
    if not isinstance(prompt, str) or not prompt.strip():
        return

    session = get_current_session()
    session["chat_history"].append({"role": "user", "content": prompt.strip()})
    with st.chat_message("user"):
        st.markdown(prompt.strip())

    messages_history = [
        HumanMessage(content=str(m["content"])) if m["role"] == "user"
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
                    "I'm unable to process your request at the moment."
                )
                routed_node = (
                    final_state.get("current_intent", "Supervisor Routed").capitalize()
                    + " Agent"
                )
                session["active_agent"] = routed_node
                agent_outputs = final_state.get("agent_outputs", {})
                pending_action = agent_outputs.get("appointment_pending")

                st.markdown(f"<div class='node-tag'>⬡ {routed_node}</div>", unsafe_allow_html=True)
                st.markdown(response)

                session["chat_history"].append({
                    "role": "assistant",
                    "content": response,
                    "agent_info": routed_node,
                })

                if pending_action:
                    session["hitl_pending"] = pending_action

                st.rerun()

            except Exception as e:
                st.error(f"LangGraph error: {str(e)}")


# ─── Bottom Input Bar ───────────────────────────────────────────────────────────
if curr_session.get("hitl_pending"):
    st.info("⏳ Please **confirm or decline** the appointment above before sending a new message.")
else:
    # ── Action buttons row (FIXED to bottom left of chat_input) ─────────────────
    st.markdown('<div id="bottom-actions-container" class="bottom-actions-row">', unsafe_allow_html=True)

    act_col1, act_col2 = st.columns([1, 1])

    with act_col1:
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
                            curr_session["chat_history"].append({
                                "role": "assistant",
                                "content": (
                                    f"📄 **Lab Report Indexed:** `{uploaded_file.name}` "
                                    f"({res.get('num_chunks')} semantic chunks).\n\n"
                                    "Ask me to explain, summarize, or flag abnormal values!"
                                ),
                                "agent_info": "Report RAG Pipeline",
                            })
                            st.toast(f"'{uploaded_file.name}' indexed!", icon="📄")
                            st.rerun()
                        else:
                            st.error(f"Failed: {res.get('message')}")

    with act_col2:
        audio_value = st.audio_input(
            "🎤",
            key=f"voice_input_{st.session_state.current_patient_id}",
        )
        if audio_value is not None:
            audio_bytes = audio_value.read()
            if audio_bytes and st.session_state.get("_last_audio_bytes") != audio_bytes:
                st.session_state["_last_audio_bytes"] = audio_bytes
                from utils.voice_input import transcribe_audio
                with st.spinner("🎙️ Transcribing…"):
                    transcribed = transcribe_audio(audio_bytes, filename="audio.webm")
                if transcribed:
                    st.toast(f"🎙️ Heard: *{transcribed}*", icon="🎤")
                    st.session_state.queued_prompt = transcribed
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Chat input pill ──────────────────────────────────────────────────────────
    chat_prompt = st.chat_input("Ask MediAssist AI anything about your health…")

    # ── Process prompt ───────────────────────────────────────────────────────────
    final_prompt = None
    if st.session_state.get("queued_prompt"):
        final_prompt = st.session_state.queued_prompt
        st.session_state.queued_prompt = None
    elif isinstance(chat_prompt, str) and chat_prompt.strip():
        final_prompt = chat_prompt

    if isinstance(final_prompt, str) and final_prompt.strip():
        process_user_message(final_prompt)

