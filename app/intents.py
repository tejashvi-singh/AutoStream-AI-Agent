from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

VALID_INTENTS = ["casual greeting", "product/pricing inquiry", "high-intent lead"]


class IntentClassification(BaseModel):
    intent: str = Field(
        description="The classified intent. Must be exactly one of: 'casual greeting', 'product/pricing inquiry', 'high-intent lead'"
    )


def classify_intent(message: str) -> str:
    """
    Given a user message, classifies the intent into one of the predetermined categories.
    Returns one of: 'casual greeting', 'product/pricing inquiry', 'high-intent lead', or 'unknown'.
    """
    # FIX: use 'model' not 'model_name' for ChatGroq
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

    prompt = PromptTemplate.from_template(
        """You are an intent classification assistant for AutoStream, an automated video editing SaaS.

Classify the user's message into EXACTLY ONE of these categories:
- "casual greeting" — when user says hello, hi, hey, or any greeting
- "product/pricing inquiry" — when user asks about features, pricing, plans, refunds, or support policies
- "high-intent lead" — when the user explicitly wants to buy, try, sign up, or use AutoStream for their channel/business

User message: "{message}"

Return only the exact intent label, nothing else.
"""
    )

    structured_llm = llm.with_structured_output(IntentClassification)
    chain = prompt | structured_llm

    try:
        result = chain.invoke({"message": message})
        intent = result.intent.strip().lower()
        if intent not in VALID_INTENTS:
            return "unknown"
        return intent
    except Exception as e:
        print(f"[IntentClassifier] Error: {e}")
        return "unknown"
