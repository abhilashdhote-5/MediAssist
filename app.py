import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import build_mediassist_graph
from utils.helpers import load_json_file
from tools.appointment_tool import AppointmentTool

# ─── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediAssist AI — Healthcare Multi-Agent Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main-header {
    font-size: 2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #1E40AF 0%, #0EA5E9 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.1rem;
}
.sub-header {
    font-size: 0.95rem;
    color: #64748B;
    margin-bottom: 1.2rem;
}
.agent-badge {
    display: inline-block;
    background: linear-gradient(90deg, #1E40AF22 0%, #0EA5E922 100%);
    color: #1E40AF;
    border: 1px solid #1E40AF44;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 8px;
}
.hitl-card {
    background: linear-gradient(135deg, #EFF6FF 0%, #F0FDF4 100%);
    border: 1.5px solid #3B82F6;
    border-radius: 12px;
    padding: 18px 22px;
    margin: 10px 0;
}
.hitl-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1E40AF;
    margin-bottom: 10px;
}
.hitl-detail {
    color: #374151;
    font-size: 0.92rem;
    line-height: 1.7;
}
.disclaimer {
    font-size: 0.78rem;
    color: #94A3B8;
    border-top: 1px solid #E2E8F0;
    padding-top: 6px;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)

# ─── Session State Init ─────────────────────────────────────────────────────────
if "graph_app" not in st.session_state:
    st.session_state.graph_app = build_mediassist_graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "current_patient_id" not in st.session_state:
    st.session_state.current_patient_id = "PAT0001"

if "hitl_pending" not in st.session_state:
    st.session_state.hitl_pending = None

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏥 MediAssist AI")
    st.caption("Supervisor-Based Multi-Agent System")
    st.divider()

    st.subheader("👤 Patient Profile")
    patients = load_json_file("data/patients.json", default=[])
    patient_options = {
        f"{p['full_name']} ({p['patient_id']})": p["patient_id"]
        for p in patients
    }

    selected_label = st.selectbox(
        "Select Patient Session",
        options=list(patient_options.keys()),
        index=0,
    )
    selected_pid = patient_options.get(selected_label, "PAT0001")

    # Reset HITL if patient changes
    if st.session_state.current_patient_id != selected_pid:
        st.session_state.current_patient_id = selected_pid
        st.session_state.hitl_pending = None

    curr_p = next((p for p in patients if p["patient_id"] == selected_pid), {})
    if curr_p:
        st.markdown(f"**Age / Gender:** {curr_p.get('age')} / {curr_p.get('gender')}")
        st.markdown(f"**Blood Group:** {curr_p.get('blood_group')}")
        allergies = ", ".join(curr_p.get("known_allergies", [])) or "None"
        conditions = ", ".join(curr_p.get("chronic_conditions", [])) or "None"
        st.markdown(f"**Allergies:** {allergies}")
        st.markdown(f"**Conditions:** {conditions}")

    st.divider()
    st.subheader("⚙️ System Nodes")
    st.info(
        "**LangGraph Agents:**\n"
        "- 🧭 Supervisor\n"
        "- 📅 Appointment Agent\n"
        "- 🩺 Symptom Agent\n"
        "- 💊 Medication Agent\n"
        "- 📋 Report Agent\n"
        "- 🛡️ Reflection Node"
    )

    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.hitl_pending = None
        st.rerun()

# ─── Header ─────────────────────────────────────────────────────────────────────
st.markdown("<div class='main-header'>🏥 MediAssist AI</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='sub-header'>Intelligent Multi-Agent Healthcare Assistant · LangGraph · Supervised Routing</div>",
    unsafe_allow_html=True,
)

# ─── HITL Confirmation Block (rendered above chat if pending) ────────────────────
def render_hitl_confirmation():
    pending = st.session_state.hitl_pending
    if not pending:
        return

    action = pending.get("action", "book").capitalize()
    doctor = pending.get("doctor_name", "Unknown Doctor")
    specialty = pending.get("specialty", "")
    date = pending.get("date", "")
    time_slot = pending.get("time_slot", "")
    patient_name = pending.get("patient_name", "")
    available_slots = pending.get("available_slots", [])
    available_days = pending.get("available_days", [])
    fee = pending.get("consultation_fee", 0)
    currency = pending.get("currency", "USD")

    st.markdown(f"""
    <div class='hitl-card'>
        <div class='hitl-title'>📋 Confirm Appointment {action}</div>
        <div class='hitl-detail'>
            <b>Patient:</b> {patient_name}<br>
            <b>Doctor:</b> {doctor} — {specialty}<br>
            <b>Date:</b> {date}<br>
            <b>Time:</b> {time_slot}<br>
            <b>Available Days:</b> {', '.join(available_days)}<br>
            <b>Consultation Fee:</b> {currency} {fee}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Let user pick a different slot / date before confirming
    col_slot, col_date = st.columns(2)
    with col_slot:
        chosen_slot = st.selectbox(
            "⏰ Choose Time Slot",
            options=available_slots,
            index=0,
            key="hitl_slot_select",
        )
    with col_date:
        chosen_date = st.text_input(
            "📅 Appointment Date (YYYY-MM-DD)",
            value=date,
            key="hitl_date_input",
        )

    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button("✅ Confirm Appointment", type="primary", use_container_width=True):
            # Execute the real action
            tool = AppointmentTool()
            if action.lower() == "cancel":
                appts = tool.list_appointments(patient_id=pending["patient_id"])
                scheduled = [a for a in appts if a.get("status") == "Scheduled"]
                if scheduled:
                    result = tool.cancel_appointment(scheduled[0]["appointment_id"])
                else:
                    result = {"status": "Error", "message": "No scheduled appointment found to cancel."}
            elif action.lower() == "reschedule":
                appts = tool.list_appointments(patient_id=pending["patient_id"])
                scheduled = [a for a in appts if a.get("status") in ("Scheduled", "Rescheduled")]
                if scheduled:
                    result = tool.reschedule_appointment(
                        scheduled[0]["appointment_id"], chosen_date, chosen_slot
                    )
                else:
                    result = {"status": "Error", "message": "No appointment found to reschedule."}
            else:
                result = tool.book_appointment(
                    patient_id=pending["patient_id"],
                    doctor_id=pending.get("doctor_id", "DOC001"),
                    date=chosen_date,
                    time_slot=chosen_slot,
                    reason=pending.get("reason", "Patient requested appointment via MediAssist AI"),
                    patient_name=patient_name,
                    doctor_name=doctor,
                )

            if result.get("status") == "Success":
                appt = result.get("appointment", {})
                confirmation_msg = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"**{action} ID:** {appt.get('appointment_id', 'N/A')}\n"
                    f"**Doctor:** {appt.get('doctor_name', doctor)}\n"
                    f"**Date:** {appt.get('appointment_date', chosen_date)}\n"
                    f"**Time:** {appt.get('time_slot', chosen_slot)}\n"
                    f"**Status:** {appt.get('status', 'Confirmed')}\n\n"
                    f"Your appointment has been saved. You will receive a reminder closer to the date."
                )
            else:
                confirmation_msg = f"❌ **Action Failed:** {result.get('message', 'Unknown error.')}"

            st.session_state.chat_history.append({
                "role": "assistant",
                "content": confirmation_msg,
                "agent_info": "Appointment Agent (Confirmed)",
            })
            st.session_state.hitl_pending = None
            st.rerun()

    with col_cancel:
        if st.button("❌ Cancel / Decline", use_container_width=True):
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Appointment action was **declined**. No changes have been made. Let me know if you'd like to try again or need anything else.",
                "agent_info": "Appointment Agent (Declined)",
            })
            st.session_state.hitl_pending = None
            st.rerun()


render_hitl_confirmation()

# ─── Chat History ────────────────────────────────────────────────────────────────
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    agent_info = message.get("agent_info", None)

    with st.chat_message(role):
        if agent_info and role == "assistant":
            st.markdown(
                f"<span class='agent-badge'>🤖 {agent_info}</span>",
                unsafe_allow_html=True,
            )
        st.markdown(content)

# ─── Chat Input ──────────────────────────────────────────────────────────────────
if st.session_state.hitl_pending:
    st.info("⏳ Please confirm or decline the pending appointment action above before sending a new message.")
elif prompt := st.chat_input("Ask about appointments, symptoms, medications, or lab reports..."):
    # Append user message
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Build LangGraph input state
    messages_history = [
        HumanMessage(content=m["content"]) if m["role"] == "user" else AIMessage(content=m["content"])
        for m in st.session_state.chat_history
    ]

    initial_state = {
        "messages": messages_history,
        "patient_id": st.session_state.current_patient_id,
        "current_intent": "",
        "next_node": "",
        "agent_outputs": {},
        "final_response": "",
        "is_safe": True,
        "reflection_feedback": "",
    }

    with st.chat_message("assistant"):
        with st.spinner("Coordinating healthcare agents…"):
            try:
                final_state = st.session_state.graph_app.invoke(initial_state)
                response = final_state.get(
                    "final_response",
                    "I'm unable to process your request at the moment. Please try again.",
                )
                intent = final_state.get("current_intent", "").capitalize()
                routed_node = f"{intent} Agent" if intent else "Supervisor Routed"

                # Check if there is a pending HITL action
                agent_outputs = final_state.get("agent_outputs", {})
                pending_action = agent_outputs.get("appointment_pending")

                if pending_action:
                    # Show the pre-booking response and set HITL pending
                    st.markdown(
                        f"<span class='agent-badge'>🤖 {routed_node}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(response)
                    st.session_state.hitl_pending = pending_action
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "agent_info": routed_node,
                    })
                    st.rerun()
                else:
                    st.markdown(
                        f"<span class='agent-badge'>🤖 {routed_node}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(response)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response,
                        "agent_info": routed_node,
                    })

            except Exception as e:
                err_msg = f"⚠️ An error occurred while processing your request: `{str(e)}`"
                st.error(err_msg)
