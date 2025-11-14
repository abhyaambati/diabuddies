"""ExtractorAgent - Extracts structured JSON data from conversation."""
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json


class ExtractedData(BaseModel):
    """Structured data extracted from conversation."""
    glucose: Optional[float] = Field(None, description="Blood glucose reading in mg/dL, or None if not mentioned")
    medications_taken: Optional[bool] = Field(None, description="Whether medications were taken today, or None if not mentioned")
    mood: Optional[str] = Field(None, description="User's mood or emotional state, or None if not mentioned")
    symptoms: list[str] = Field(default_factory=list, description="List of symptoms mentioned (e.g., dizziness, shakiness, thirst, fatigue)")
    concerns: Optional[str] = Field(None, description="Any concerns or worries mentioned, or None if not mentioned")


class ExtractorState(TypedDict):
    """State passed between agents."""
    user_message: str
    conversation_history: list
    reply: str
    extracted: dict
    risk: dict
    summary: str


def extractor_agent(state: ExtractorState) -> ExtractorState:
    """
    ExtractorAgent analyzes the conversation and extracts structured data:
    - Glucose readings
    - Medication status
    - Mood
    - Symptoms
    - Concerns
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    parser = PydanticOutputParser(pydantic_object=ExtractedData)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a data extraction agent. Extract structured information from diabetes-related conversations.

Extract the following information if mentioned:
- glucose: Blood glucose reading in mg/dL (numeric value only)
- medications_taken: Boolean indicating if medications were taken today
- mood: User's emotional state or mood
- symptoms: List of symptoms (dizziness, shakiness, thirst, fatigue, etc.)
- concerns: Any health concerns or worries mentioned

If information is not mentioned, set the field to null.
Return ONLY valid JSON matching the schema.

{format_instructions}"""),
        ("human", """Extract data from this conversation:

User message: {user_message}
Buddy reply: {reply}

Conversation history:
{history}

Extract the structured data.""")
    ])
    
    # Format conversation history
    history_text = ""
    if state.get("conversation_history"):
        for msg in state["conversation_history"][-5:]:  # Last 5 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"
    
    chain = prompt | llm | parser
    
    try:
        extracted_data = chain.invoke({
            "user_message": state["user_message"],
            "reply": state.get("reply", ""),
            "history": history_text,
            "format_instructions": parser.get_format_instructions()
        })
        
        # Convert Pydantic model to dict
        extracted_dict = extracted_data.model_dump()
    except Exception as e:
        print(f"Extraction error: {e}")
        # Return empty structure on error
        extracted_dict = {
            "glucose": None,
            "medications_taken": None,
            "mood": None,
            "symptoms": [],
            "concerns": None
        }
    
    return {
        **state,
        "extracted": extracted_dict
    }

