import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import build_mediassist_graph
from utils.helpers import load_json_file

# Page Configuration
st.set_page_config(
    page_title="MediAssist AI",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Bright, White-First Clinical Chat Aesthetic
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

    :root {
        --bg: #FFFFFF;
        --surface: #F6FBF8;
        --border: #DCEEE4;
        --border-strong: #B7E4CE;
        --ink: #0B1F17;
        --ink-muted: #5B7268;
        --green-900: #063D2C;
        --green-700: #0C7A52;
        --green-600: #0E9F6E;
        --green-100: #E7F7EF;

        /* Streamlit's own theme variables — native widgets like chat_input read
           these directly, so we override the source instead of chasing every
           internal class Streamlit generates. */
        --background-color: #FFFFFF;
        --secondary-background-color: #F6FBF8;
        --text-color: #0B1F17;
        --primary-color: #0E9F6E;
    }

    /* Global Reset */
    html, body, [class*="css"], .stApp {
        background-color: var(--bg) !important;
        color: var(--ink) !important;
        font-family: 'Inter', sans-serif !important;
    }

    header {visibility: hidden;}
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 6.5rem !important;
        max-width: 720px !important;
    }

    /* Header Typography */
    .chat-title {
        font-family: 'Manrope', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: var(--green-900);
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
    }

    .chat-subtitle {
        font-size: 0.95rem;
        color: var(--ink-muted);
        font-weight: 400;
        margin-bottom: 1rem;
    }

    /* Signature pulse-line divider */
    .pulse-divider {
        width: 100%;
        height: 22px;
        margin: 0.4rem 0 1.6rem 0;
    }

    /* Capability cards */
    .capability-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 10px;
        margin-bottom: 1.8rem;
    }
    .capability-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 12px 14px;
    }
    .capability-card .cap-label {
        font-family: 'Manrope', sans-serif;
        font-size: 0.78rem;
        font-weight: 700;
        color: var(--green-700);
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
    }
    .capability-card .cap-desc {
        font-size: 0.78rem;
        color: var(--ink-muted);
        line-height: 1.35;
    }
    @media (max-width: 700px) {
        .capability-row { grid-template-columns: repeat(2, 1fr); }
    }

    /* Status bar: active patient + active agent, always visible above chat */
    .status-bar {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-bottom: 1.2rem;
    }
    .status-chip {
        display: flex;
        align-items: center;
        gap: 8px;
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 8px 14px;
        font-size: 0.8rem;
        color: var(--ink);
    }
    .status-chip .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--green-600);
        flex-shrink: 0;
    }
    .status-chip .status-label {
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
        color: var(--ink-muted);
        text-transform: uppercase;
        font-size: 0.68rem;
        letter-spacing: 0.04em;
        margin-right: 2px;
    }
    .status-chip .status-value {
        font-weight: 600;
        color: var(--green-900);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] h3 {
        font-family: 'Manrope', sans-serif !important;
        color: var(--green-900) !important;
        font-weight: 800 !important;
    }

    /* Patient Card Container */
    .patient-glass-card {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin-top: 10px;
    }

    .card-row {
        display: flex;
        justify-content: space-between;
        font-size: 0.82rem;
        color: var(--ink-muted);
        margin-bottom: 8px;
    }

    .card-row strong {
        color: var(--green-700);
        font-weight: 600;
    }

    /* Agent DAG list, styled as a quiet vertical timeline */
    .dag-list {
        font-size: 0.82rem;
        color: var(--ink-muted);
        margin-top: 6px;
        line-height: 1.9;
        border-left: 2px solid var(--border-strong);
        padding-left: 12px;
    }

    /* Source Node Tag */
    .node-tag {
        display: inline-flex;
        align-items: center;
        background: var(--green-100);
        color: var(--green-700);
        border: 1px solid var(--border-strong);
        padding: 3px 10px;
        border-radius: 20px;
        font-family: 'Manrope', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.03em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Custom Chat Message Containers */
    [data-testid="stChatMessage"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0.4rem 0 !important;
    }

    /* User Message Bubble */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #FFFFFF !important;
        border-radius: 14px 14px 4px 14px !important;
        padding: 10px 14px !important;
        margin-left: 2.2rem;
        border: 1px solid var(--border) !important;
        box-shadow: 0 2px 6px rgba(11, 31, 23, 0.03);
    }

    /* Assistant Message Bubble */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background: var(--surface) !important;
        border-radius: 14px 14px 14px 4px !important;
        padding: 10px 14px !important;
        margin-right: 2.2rem;
        border: 1px solid var(--border) !important;
    }

    [data-testid="stChatMessage"] p {
        font-size: 0.9rem !important;
        margin-bottom: 0.3rem !important;
    }

    /* Fixed bottom bar that wraps the chat input — constrain to the content
       column and match the capability-card surface color. Chained ancestor
       selectors here deliberately outrank Streamlit's own theme CSS. */
    html body [data-testid="stBottom"],
    html body [data-testid="stBottom"] > div {
        background-color: #FFFFFF !important;
        border-top: 1px solid var(--border) !important;
    }
    html body [data-testid="stBottomBlockContainer"],
    html body .stChatFloatingInputContainer {
        background-color: #FFFFFF !important;
        max-width: 720px !important;
        margin-left: auto !important;
        margin-right: auto !important;
        padding: 0.5rem 1rem 1rem 1rem !important;
    }

    /* Chat Input Bar Override — same soft surface as the capability cards,
       compact height, dark readable text */
    html body [data-testid="stChatInput"] {
        background-color: var(--surface) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        min-height: unset !important;
    }
    html body [data-testid="stChatInput"]:focus-within {
        border-color: var(--green-600) !important;
        box-shadow: 0 0 0 2px rgba(14, 159, 110, 0.15) !important;
    }

    /* BaseWeb wraps the textarea in its own themed layers — flatten them so
       the surface color shows through instead of Streamlit's default dark */
    html body [data-testid="stChatInput"] [data-baseweb="textarea"],
    html body [data-testid="stChatInput"] [data-baseweb="base-input"] {
        background-color: transparent !important;
        border: none !important;
    }

    html body [data-testid="stChatInput"] textarea {
        color: var(--ink) !important;
        -webkit-text-fill-color: var(--ink) !important;
        caret-color: var(--ink) !important;
        font-size: 0.85rem !important;
        font-family: 'Inter', sans-serif !important;
        background-color: transparent !important;
        padding: 6px 8px !important;
        min-height: 1.9rem !important;
    }
    html body [data-testid="stChatInput"] textarea::placeholder {
        color: var(--ink-muted) !important;
        opacity: 0.9 !important;
    }

    /* Send button */
    html body [data-testid="stChatInput"] button {
        background-color: var(--green-600) !important;
        border-radius: 7px !important;
        width: 1.8rem !important;
        height: 1.8rem !important;
    }
    html body [data-testid="stChatInput"] button svg {
        fill: #FFFFFF !important;
    }

    /* Dropdown Overrides */
    .stSelectbox > div > div {
        background-color: var(--surface) !important;
        color: var(--ink) !important;
        border-color: var(--border-strong) !important;
        border-radius: 8px !important;
    }

    /* Action Buttons */
    .stButton > button {
        width: 100%;
        background-color: #FFFFFF !important;
        color: var(--green-900) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-family: 'Manrope', sans-serif !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stButton > button:hover {
        background-color: var(--green-600) !important;
        color: #FFFFFF !important;
        border-color: var(--green-600) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "graph_app" not in st.session_state:
    st.session_state.graph_app = build_mediassist_graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_patient_id" not in st.session_state:
    st.session_state.current_patient_id = "PAT8801"

if "active_agent" not in st.session_state:
    st.session_state.active_agent = "Awaiting query"

# Sidebar Controls
with st.sidebar:
    st.markdown("<h3>MediAssist AI</h3>", unsafe_allow_html=True)
    st.caption("Supervisor multi-agent intelligence")

    st.divider()
    st.markdown("<span style='font-family: Manrope; font-size: 0.8rem; font-weight: 700; color: #5B7268; text-transform: uppercase; letter-spacing: 0.04em;'>Patient context</span>", unsafe_allow_html=True)

    patients = load_json_file("data/patients.json", default=[])
    patient_options = {f"{p['full_name']} ({p['patient_id']})": p['patient_id'] for p in patients}

    selected_patient_label = st.selectbox(
        "Select Patient Session",
        options=list(patient_options.keys()),
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.current_patient_id = patient_options.get(selected_patient_label, "PAT8801")

    curr_p = next((p for p in patients if p['patient_id'] == st.session_state.current_patient_id), {})
    if curr_p:
        st.markdown(f"""
        <div class="patient-glass-card">
            <div class="card-row"><span>Age / Sex</span><strong>{curr_p.get('age')} / {curr_p.get('gender')}</strong></div>
            <div class="card-row"><span>Blood Group</span><strong>{curr_p.get('blood_group')}</strong></div>
            <div class="card-row"><span>Allergies</span><strong>{', '.join(curr_p.get('known_allergies', [])) or 'None'}</strong></div>
            <div class="card-row"><span>Conditions</span><strong>{', '.join(curr_p.get('chronic_conditions', [])) or 'None'}</strong></div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    st.markdown("<span style='font-family: Manrope; font-size: 0.8rem; font-weight: 700; color: #5B7268; text-transform: uppercase; letter-spacing: 0.04em;'>Agent execution path</span>", unsafe_allow_html=True)
    st.markdown("""
    <div class="dag-list">
    Supervisor intent router<br>
    Appointment specialist<br>
    Symptom intelligence<br>
    Medication guide<br>
    Report interpreter<br>
    Safety validation node
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    if st.button("Reset Session"):
        st.session_state.chat_history = []
        st.rerun()

# Main Header Area
st.markdown("<div class='chat-title'>MediAssist AI</div>", unsafe_allow_html=True)
st.markdown("<div class='chat-subtitle'>Your assistant for scheduling, symptoms, medications, and lab reports.</div>", unsafe_allow_html=True)

# Signature pulse-line divider (medical monitor motif)
st.markdown("""
<svg class="pulse-divider" viewBox="0 0 860 22" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none">
  <polyline points="0,11 300,11 330,2 355,20 380,4 405,11 860,11"
    fill="none" stroke="#0E9F6E" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"/>
</svg>
""", unsafe_allow_html=True)

# Capability Overview
st.markdown("""
<div class="capability-row">
    <div class="capability-card">
        <div class="cap-label">Appointments</div>
        <div class="cap-desc">Check availability, book, reschedule, or cancel visits.</div>
    </div>
    <div class="capability-card">
        <div class="cap-label">Symptoms</div>
        <div class="cap-desc">Describe how you're feeling for general guidance and next steps.</div>
    </div>
    <div class="capability-card">
        <div class="cap-label">Medications</div>
        <div class="cap-desc">Ask about dosage, timing, or interactions for your prescriptions.</div>
    </div>
    <div class="capability-card">
        <div class="cap-label">Lab Reports</div>
        <div class="cap-desc">Get plain-language explanations of your test results.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Status Bar — active patient and active agent, visible without opening the sidebar
patient_name = curr_p.get('full_name', 'No patient selected') if curr_p else 'No patient selected'
st.markdown(f"""
<div class="status-bar">
    <div class="status-chip">
        <span class="status-dot"></span>
        <span class="status-label">Patient</span>
        <span class="status-value">{patient_name}</span>
    </div>
    <div class="status-chip">
        <span class="status-dot"></span>
        <span class="status-label">Active Agent</span>
        <span class="status-value">{st.session_state.active_agent}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Render Chat History
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    agent_info = message.get("agent_info", None)

    with st.chat_message(role):
        if agent_info and role == "assistant":
            st.markdown(f"<div class='node-tag'>{agent_info}</div>", unsafe_allow_html=True)
        st.markdown(content)

# Chat Input Field
if prompt := st.chat_input("Message MediAssist AI..."):
    # Append user prompt
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare LangGraph Agent Input State
    messages_history = [
        HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"])
        for msg in st.session_state.chat_history
    ]

    initial_state = {
        "messages": messages_history,
        "patient_id": st.session_state.current_patient_id,
        "current_intent": "",
        "next_node": "",
        "agent_outputs": {},
        "final_response": "",
        "is_safe": True,
        "reflection_feedback": ""
    }

    with st.chat_message("assistant"):
        with st.spinner("Routing query..."):
            try:
                # Invoke LangGraph Workflow
                final_state = st.session_state.graph_app.invoke(initial_state)
                response = final_state.get("final_response", "I am unable to process your request at the moment.")
                routed_node = final_state.get("current_intent", "Supervisor Routed").capitalize() + " Agent"
                st.session_state.active_agent = routed_node

                st.markdown(f"<div class='node-tag'>{routed_node}</div>", unsafe_allow_html=True)
                st.markdown(response)

                # Save assistant response
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "agent_info": routed_node
                })
            except Exception as e:
                err_msg = f"An error occurred while processing through LangGraph: {str(e)}"
                st.error(err_msg)