"""LangGraph Orchestrator - Controls message flow between agents."""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from .buddy_agent import buddy_agent
from .extractor_agent import extractor_agent
from .risk_agent import risk_agent
from .summary_agent import summary_agent


class DiabuddiesState(TypedDict, total=False):
    """Complete state for the Diabuddies multi-agent system."""
    user_message: str
    conversation_history: list
    reply: str
    extracted: dict
    risk: dict
    summary: str
    is_emergency: bool
    patient_id: Optional[str]
    care_plan_context: Optional[str]


def create_conversation_graph():
    """
    Creates a fast conversation-only graph (just BuddyAgent).
    Used during normal conversation to reduce latency.
    """
    workflow = StateGraph(DiabuddiesState)
    workflow.add_node("buddy", buddy_agent)
    workflow.set_entry_point("buddy")
    workflow.add_edge("buddy", END)
    return workflow.compile()


def create_full_insights_graph():
    """
    Creates the full LangGraph workflow with all agents:
    UserMessage → BuddyAgent → ExtractorAgent → RiskAgent → SummaryAgent → Return
    Used for generating insights after conversation or during emergencies.
    """
    workflow = StateGraph(DiabuddiesState)
    
    # Add nodes
    workflow.add_node("buddy", buddy_agent)
    workflow.add_node("extractor", extractor_agent)
    workflow.add_node("risk", risk_agent)
    workflow.add_node("summary", summary_agent)
    
    # Define the flow
    workflow.set_entry_point("buddy")
    workflow.add_edge("buddy", "extractor")
    workflow.add_edge("extractor", "risk")
    workflow.add_edge("risk", "summary")
    workflow.add_edge("summary", END)
    
    # Compile the graph
    return workflow.compile()


# Create graph instances
conversation_graph = create_conversation_graph()
diabuddies_graph = create_full_insights_graph()
