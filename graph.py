from langgraph.graph import StateGraph, END
from memory.state import AgentState
from supervisor import classify_intent, route_next_node
from agents.appointment_agent import process_appointment
from agents.symptom_agent import assess_symptoms
from agents.medication_agent import get_medication_info
from agents.report_agent import explain_lab_report
from agents.reflection_node import validate_response
from agents.general_agent import handle_general_conversation
from agents.view_appointment_agent import view_appointments

def build_mediassist_graph():
    """
    Constructs and compiles the Supervisor-based Multi-Agent Healthcare LangGraph DAG workflow.
    """
    workflow = StateGraph(AgentState)

    # 1. Add Graph Nodes
    workflow.add_node("supervisor", classify_intent)
    workflow.add_node("appointment_agent", process_appointment)
    workflow.add_node("symptom_agent", assess_symptoms)
    workflow.add_node("medication_agent", get_medication_info)
    workflow.add_node("report_agent", explain_lab_report)
    workflow.add_node("general_agent", handle_general_conversation)
    workflow.add_node("view_appointment_agent", view_appointments)
    workflow.add_node("reflection_node", validate_response)

    # 2. Set Workflow Entry Point
    workflow.set_entry_point("supervisor")

    # 3. Add Conditional Routing Edges from Supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_next_node,
        {
            "appointment_agent": "appointment_agent",
            "symptom_agent": "symptom_agent",
            "medication_agent": "medication_agent",
            "report_agent": "report_agent",
            "general_agent": "general_agent",
            "view_appointment_agent": "view_appointment_agent",
        }
    )

    # 4. Connect Specialized Agents to Reflection Validation Node
    workflow.add_edge("appointment_agent", "reflection_node")
    workflow.add_edge("symptom_agent", "reflection_node")
    workflow.add_edge("medication_agent", "reflection_node")
    workflow.add_edge("report_agent", "reflection_node")
    workflow.add_edge("general_agent", "reflection_node")
    workflow.add_edge("view_appointment_agent", "reflection_node")

    # 5. Exit Point after Reflection
    workflow.add_edge("reflection_node", END)

    # 6. Compile and return executable StateGraph app
    app = workflow.compile()
    return app