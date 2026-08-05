import operator
from typing import Annotated, Any, Dict, Sequence, TypedDict
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    Shared LangGraph state passed between the Supervisor, specialized AI agents,
    and the Reflection Node.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]
    patient_id: str
    current_intent: str
    next_node: str
    agent_outputs: Dict[str, Any]
    final_response: str
    is_safe: bool
    reflection_feedback: str
    pdf_context: str
