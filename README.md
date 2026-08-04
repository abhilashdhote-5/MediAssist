# MediAssist AI - Intelligent Multi-Agent Healthcare Assistant

MediAssist AI is an enterprise-grade multi-agent healthcare assistant designed to help hospitals and clinics automate routine patient interactions using **LangGraph**, **LangChain**, and **Streamlit**.

## Architecture Overview
- **Supervisor Agent**: Intent detection & routing to specialized AI agents.
- **Appointment Agent**: Manage appointments (book, cancel, reschedule).
- **Symptom Agent**: Non-diagnostic healthcare guidance and specialty recommendation.
- **Medication Agent**: Information on drugs, dosages, precautions, and allergy checks.
- **Report Agent**: Simplifies complex laboratory reports and highlights abnormalities.
- **Reflection Node**: Validates response safety, non-diagnostic compliance, and appends disclaimers.
- **Memory Layer**: Shared state and persistent session checkpointer.

## Directory Structure
```
mediassist-ai/
├── app.py
├── supervisor.py
├── graph.py
├── requirements.txt
├── README.md
├── agents/
│   ├── appointment_agent.py
│   ├── symptom_agent.py
│   ├── medication_agent.py
│   ├── report_agent.py
│   └── reflection_node.py
├── memory/
│   ├── conversation_memory.py
│   └── state.py
├── tools/
│   ├── appointment_tool.py
│   ├── doctor_lookup.py
│   ├── medicine_lookup.py
│   └── report_reader.py
├── prompts/
│   ├── supervisor_prompt.py
│   ├── appointment_prompt.py
│   ├── symptom_prompt.py
│   ├── medication_prompt.py
│   ├── report_prompt.py
│   └── reflection_prompt.py
├── data/
│   ├── doctors.json
│   ├── patients.json
│   ├── appointments.json
│   ├── medicines.json
│   ├── medical_reports.json
│   ├── symptom_knowledge.json
│   └── sample_reports/
├── tests/
└── utils/
```

## Setup & Run
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `.env` file with your API keys.
3. Launch Streamlit UI:
   ```bash
   streamlit run app.py
   ```
