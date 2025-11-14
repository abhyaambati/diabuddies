"""RiskAgent - Assesses risk from extracted data."""
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import json


class RiskAssessment(BaseModel):
    """Risk assessment structure."""
    level: str = Field(description="Risk level: 'low', 'moderate', 'high', or 'critical'")
    glucose_risk: str = Field(description="Risk assessment for glucose levels")
    symptom_risk: str = Field(description="Risk assessment for symptoms")
    overall_risk: str = Field(description="Overall risk assessment")
    recommendations: list[str] = Field(default_factory=list, description="Non-medical recommendations (e.g., 'monitor glucose', 'contact healthcare provider')")


class RiskState(TypedDict):
    """State passed between agents."""
    user_message: str
    conversation_history: list
    reply: str
    extracted: dict
    risk: dict
    summary: str


def risk_agent(state: RiskState) -> RiskState:
    """
    RiskAgent assesses risk based on extracted data.
    Evaluates glucose levels, symptoms, and overall health status.
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    
    parser = PydanticOutputParser(pydantic_object=RiskAssessment)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a risk assessment agent for diabetes care. Assess risk based on extracted data.

Risk Levels:
- low: Normal glucose (70-180 mg/dL), no concerning symptoms, medications taken
- moderate: Glucose slightly out of range (50-70 or 180-250), mild symptoms, missed medications
- high: Glucose significantly out of range (<50 or >250), multiple symptoms, significant concerns
- critical: Severe symptoms (chest pain, trouble breathing, confusion), very high/low glucose, emergency situation

IMPORTANT SAFETY RULES:
- DO NOT provide medical advice or dosing instructions
- For critical situations, recommend immediate medical attention
- For high risk, recommend contacting healthcare provider
- Keep recommendations general and non-medical

{format_instructions}"""),
        ("human", """Assess risk from this extracted data:

{extracted_data}

Provide a risk assessment.""")
    ])
    
    extracted_data = state.get("extracted", {})
    
    chain = prompt | llm | parser
    
    try:
        risk_assessment = chain.invoke({
            "extracted_data": json.dumps(extracted_data, indent=2),
            "format_instructions": parser.get_format_instructions()
        })
        
        # Convert Pydantic model to dict
        risk_dict = risk_assessment.model_dump()
    except Exception as e:
        print(f"Risk assessment error: {e}")
        # Default to low risk on error
        risk_dict = {
            "level": "low",
            "glucose_risk": "Unable to assess",
            "symptom_risk": "Unable to assess",
            "overall_risk": "Unable to assess",
            "recommendations": []
        }
    
    return {
        **state,
        "risk": risk_dict
    }

