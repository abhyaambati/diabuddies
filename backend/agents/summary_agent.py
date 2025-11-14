"""SummaryAgent - Generates friendly daily summary."""
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json


class SummaryState(TypedDict):
    """State passed between agents."""
    user_message: str
    conversation_history: list
    reply: str
    extracted: dict
    risk: dict
    summary: str


def summary_agent(state: SummaryState) -> SummaryState:
    """
    SummaryAgent generates a friendly, supportive daily summary based on:
    - The conversation
    - Extracted data
    - Risk assessment
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a friendly summary agent for Diabuddies. Generate a warm, supportive daily summary.

TONE:
- Friendly, encouraging, like a caring neighbor
- Plain language, no medical jargon
- 2-4 sentences maximum
- Focus on positive reinforcement and gentle encouragement

CONTENT:
- Summarize the key points from today's check-in
- Acknowledge what the user shared
- Provide gentle encouragement
- If risk is moderate/high, include a gentle reminder to stay in touch with their healthcare team
- DO NOT provide medical advice or dosing instructions"""),
        ("human", """Generate a friendly daily summary based on:

Conversation:
User: {user_message}
Buddy: {reply}

Extracted Data:
{extracted_data}

Risk Assessment:
{risk_data}

Create a warm, supportive summary.""")
    ])
    
    extracted_data = state.get("extracted", {})
    risk_data = state.get("risk", {})
    
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "user_message": state["user_message"],
            "reply": state.get("reply", ""),
            "extracted_data": json.dumps(extracted_data, indent=2),
            "risk_data": json.dumps(risk_data, indent=2)
        })
        
        summary = response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        print(f"Summary generation error: {e}")
        summary = "Thank you for checking in today. Take care!"
    
    return {
        **state,
        "summary": summary
    }

