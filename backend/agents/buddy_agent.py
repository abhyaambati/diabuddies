"""BuddyAgent - Friendly diabetes conversation agent."""
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class BuddyState(TypedDict):
    """State passed between agents."""
    user_message: str
    conversation_history: list
    reply: str
    extracted: dict
    risk: dict
    summary: str
    is_emergency: bool
    patient_id: Optional[str]
    care_plan_context: Optional[str]


def buddy_agent(state: BuddyState) -> BuddyState:
    """
    BuddyAgent generates a friendly, supportive response to the user's message.
    Maintains the warm, neighborly tone and asks follow-up questions.
    Uses care plan information to provide personalized reminders and guidance.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    system_prompt = """You are Diabuddies, a warm, friendly diabetes check-in buddy for people in rural Georgia.

GOALS:
- Have short, supportive daily conversations with people living with diabetes.
- Ask about their blood sugar, medications, how they feel, and anything worrying them.
- Provide gentle reminders about medications, glucose checks, exercise, and meals based on their care plan.
- Encourage them, educate them gently, and help them feel less alone.
- NEVER give medical dosing instructions or override their clinician.

TONE:
- Friendly, plain language, no jargon.
- Speak like a kind neighbor, not a robot or doctor.
- Short sentences. One question at a time.
- Respectful, non-judgmental, no shaming.

SAFETY:
- DO NOT:
  - Adjust insulin doses.
  - Tell people to change meds.
  - Diagnose conditions.
  - Recommend specific drugs or treatments.
- If user asks for dosing or urgent medical advice, say:
  - "I'm not a doctor and I can't safely answer that. Please call your doctor or nurse."
- If user mentions chest pain, trouble breathing, confusion, passing out, or feeling like they might harm themselves:
  - Say: "This could be serious. Please call emergency services or go to the nearest emergency room right away."
  - Encourage them to contact a trusted person if possible.

STYLE:
- Keep replies 1–3 sentences.
- Ask only one question at a time.
- End the conversation kindly.
- Use care plan information to provide personalized, relevant reminders."""

    # Add care plan context if available
    if state.get("care_plan_context"):
        system_prompt += f"\n\nPATIENT CARE PLAN CONTEXT:\n{state['care_plan_context']}\n\nUse this information to provide personalized reminders and ask relevant questions about their medications, glucose targets, and health goals."

    # Build messages list with conversation history
    messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history if available
    if state.get("conversation_history"):
        for msg in state["conversation_history"]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))
    
    # Add current user message
    messages.append(HumanMessage(content=state["user_message"]))
    
    # Invoke LLM
    response = llm.invoke(messages)
    reply = response.content if hasattr(response, 'content') else str(response)
    
    # Check for emergency keywords in user message
    emergency_keywords = [
        'chest pain', 'trouble breathing', 'can\'t breathe', 'difficulty breathing',
        'confusion', 'passing out', 'fainted', 'unconscious', 'emergency',
        'very high', 'very low', 'extremely high', 'extremely low',
        'severe', 'critical', 'urgent', 'help', '911'
    ]
    user_msg_lower = state["user_message"].lower()
    is_emergency = any(keyword in user_msg_lower for keyword in emergency_keywords)
    
    return {
        **state,
        "reply": reply,
        "is_emergency": is_emergency
    }

