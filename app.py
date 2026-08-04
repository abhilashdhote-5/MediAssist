import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from graph import build_mediassist_graph
from utils.helpers import load_json_file

# Page Configuration
st.set_page_config(
    page_title="MediAssist AI - Healthcare Multi-Agent Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
    }
    .agent-badge {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 4px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
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

# Sidebar Controls
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/hospital-2.png", width=70)
    st.title("MediAssist AI")
    st.caption("Supervisor-Based Multi-Agent System")
    
    st.divider()
    st.subheader("👤 Patient Profile")
    
    patients = load_json_file("data/patients.json", default=[])
    patient_options = {f"{p['full_name']} ({p['patient_id']})": p['patient_id'] for p in patients}
    
    selected_patient_label = st.selectbox(
        "Select Patient Session",
        options=list(patient_options.keys()),
        index=0
    )
    st.session_state.current_patient_id = patient_options.get(selected_patient_label, "PAT8801")

    curr_p = next((p for p in patients if p['patient_id'] == st.session_state.current_patient_id), {})
    if curr_p:
        st.write(f"**Age / Gender:** {curr_p.get('age')} / {curr_p.get('gender')}")
        st.write(f"**Blood Group:** {curr_p.get('blood_group')}")
        st.write(f"**Known Allergies:** {', '.join(curr_p.get('known_allergies', [])) or 'None'}")
        st.write(f"**Conditions:** {', '.join(curr_p.get('chronic_conditions', [])) or 'None'}")

    st.divider()
    st.subheader("⚙️ System Architecture")
    st.info("""
    **LangGraph Nodes:**
    - 🧭 **Supervisor Agent**
    - 📅 **Appointment Agent**
    - 🩺 **Symptom Agent**
    - 💊 **Medication Agent**
    - 📋 **Report Agent**
    - 🛡️ **Reflection Safety Node**
    """)

    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        st.rerun()

# Header
st.markdown("<div class='main-header'>🏥 MediAssist AI</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Intelligent Multi-Agent Healthcare Assistant with LangGraph & Shared Memory</div>", unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.chat_history:
    role = message["role"]
    content = message["content"]
    agent_info = message.get("agent_info", None)
    
    with st.chat_message(role):
        if agent_info:
            st.markdown(f"<span class='agent-badge'>Routed Node: {agent_info}</span>", unsafe_allow_html=True)
        st.markdown(content)

# Chat Input
if prompt := st.chat_input("Ask about appointments, symptoms, medications, or lab reports..."):
    # Append user prompt
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare LangGraph Agent Input State
    messages_history = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in st.session_state.chat_history]

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
        with st.spinner("Supervisor Agent coordinating specialized healthcare agents..."):
            try:
                # Invoke LangGraph Workflow
                final_state = st.session_state.graph_app.invoke(initial_state)
                response = final_state.get("final_response", "I am unable to process your request at the moment.")
                routed_node = final_state.get("current_intent", "Supervisor Routed").capitalize() + " Agent"
                
                st.markdown(f"<span class='agent-badge'>Routed Node: {routed_node}</span>", unsafe_allow_html=True)
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
