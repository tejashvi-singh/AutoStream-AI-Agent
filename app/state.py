import operator
from typing import Annotated, TypedDict, List
from langchain_core.messages import AnyMessage

class GraphState(TypedDict):
    """
    Represents the state of our agent.
    """
    # Messages list is accumulated over turns
    messages: Annotated[list[AnyMessage], operator.add]
    
    # Track user intent and lead info
    intent: str | None
    name: str | None
    email: str | None
    creator_platform: str | None
    lead_captured: bool
