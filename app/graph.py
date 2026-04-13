import os
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from app.state import GraphState
from app.intents import classify_intent
from app.rag import get_rag_chain
from app.tools import mock_lead_capture

load_dotenv()


# ─── Lead Extraction Model ────────────────────────────────────────────────────

class LeadExtraction(BaseModel):
    name: str | None = Field(default=None, description="The user's name if provided")
    email: str | None = Field(default=None, description="The user's email if provided")
    creator_platform: str | None = Field(
        default=None,
        description="The user's creator platform like YouTube, TikTok, Instagram, etc. if provided"
    )


def extract_lead_info(message: str) -> LeadExtraction:
    """Use structured LLM output to extract name, email, and platform from a message."""
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    structured_llm = llm.with_structured_output(LeadExtraction)
    res = structured_llm.invoke(
        f"Extract lead contact info from the following message. "
        f"Only return fields that are EXPLICITLY mentioned. Don't invent anything.\n\nMessage: {message}"
    )
    return res


# ─── Graph Nodes ──────────────────────────────────────────────────────────────

def process_message_node(state: GraphState):
    """
    Entry node: determines intent or extracts lead info if already in lead flow.
    """
    messages = state.get("messages", [])
    if not messages:
        return {}

    latest_msg = messages[-1].content
    current_intent = state.get("intent")
    updates = {}

    # If already in lead capture mode — extract info from latest message
    if current_intent == "high-intent lead":
        extracted = extract_lead_info(latest_msg)
        if extracted.name and not state.get("name"):
            updates["name"] = extracted.name
        if extracted.email and not state.get("email"):
            updates["email"] = extracted.email
        if extracted.creator_platform and not state.get("creator_platform"):
            updates["creator_platform"] = extracted.creator_platform
        return updates

    # Otherwise classify fresh intent
    new_intent = classify_intent(latest_msg)
    updates["intent"] = new_intent

    if new_intent == "high-intent lead":
        # Try to extract info from the very first high-intent message
        extracted = extract_lead_info(latest_msg)
        if extracted.name:
            updates["name"] = extracted.name
        if extracted.email:
            updates["email"] = extracted.email
        if extracted.creator_platform:
            updates["creator_platform"] = extracted.creator_platform

    return updates


def handle_greeting(state: GraphState):
    return {"messages": [AIMessage(content=(
        "👋 Hello! Welcome to **AutoStream** — your AI-powered video editing platform for creators!\n\n"
        "I can help you with:\n"
        "• 📦 Plan pricing & features\n"
        "• 📋 Our refund & support policies\n"
        "• 🚀 Getting you started on the right plan\n\n"
        "What can I help you with today?"
    ))]}


def handle_unknown(state: GraphState):
    return {"messages": [AIMessage(content=(
        "I'm not quite sure I understand that. Could you clarify?\n\n"
        "You can ask me about our **pricing plans**, **features**, or just say "
        "**'I want to try AutoStream'** if you're ready to get started! 🎬"
    ))]}


def retrieve_rag_answer(state: GraphState):
    messages = state.get("messages", [])
    if not messages:
        return {}
    latest_msg = messages[-1].content
    rag_chain = get_rag_chain()
    answer = rag_chain.invoke(latest_msg)
    return {"messages": [AIMessage(content=answer)]}


def collect_name(state: GraphState):
    return {"messages": [AIMessage(content=(
        "🎉 Awesome choice! Let's get you set up on AutoStream Pro.\n\n"
        "First — **what's your name?**"
    ))]}


def collect_email(state: GraphState):
    name = state.get("name", "there")
    return {"messages": [AIMessage(content=(
        f"Great, {name}! 🙌\n\n"
        "Now, what's your **email address** so we can send you the onboarding details?"
    ))]}


def collect_platform(state: GraphState):
    return {"messages": [AIMessage(content=(
        "Almost done! 🎬\n\n"
        "Which **creator platform** do you mainly post on?\n"
        "*(e.g., YouTube, TikTok, Instagram, Twitch...)*"
    ))]}


def execute_mock_tool(state: GraphState):
    """STRICT: Only executes after ALL three fields are confirmed in state."""
    name = state.get("name")
    email = state.get("email")
    platform = state.get("creator_platform")

    # Safety guard (should never reach here without all three, but just in case)
    if not all([name, email, platform]):
        return {"messages": [AIMessage(content="Please provide all details so I can complete your registration.")]}

    # Execute the lead capture tool
    tool_response = mock_lead_capture(name, email, platform)

    return {
        "lead_captured": True,
        "messages": [AIMessage(content=(
            f"✅ **You're all set, {name}!**\n\n"
            f"{tool_response}\n\n"
            f"📧 We'll be in touch at **{email}** shortly with your Pro plan access.\n"
            f"🎬 We can't wait to supercharge your **{platform}** content with AutoStream AI!"
        ))]
    }


def already_captured(state: GraphState):
    name = state.get("name", "there")
    return {"messages": [AIMessage(content=(
        f"Hey {name}! We've already saved your details and our team will be in touch soon. 🚀\n\n"
        "Is there anything else you'd like to know about AutoStream?"
    ))]}


# ─── Routing Logic ────────────────────────────────────────────────────────────

def route_intent(state: GraphState):
    intent = state.get("intent", "unknown")
    if intent == "casual greeting":
        return "handle_greeting"
    elif intent == "product/pricing inquiry":
        return "retrieve_rag_answer"
    elif intent == "high-intent lead":
        return "lead_routing"
    else:
        return "handle_unknown"


def route_lead_capture(state: GraphState):
    if state.get("lead_captured"):
        return "already_captured"
    if not state.get("name"):
        return "collect_name"
    elif not state.get("email"):
        return "collect_email"
    elif not state.get("creator_platform"):
        return "collect_platform"
    else:
        return "execute_mock_tool"


# ─── Build the Graph ──────────────────────────────────────────────────────────

builder = StateGraph(GraphState)

# Add all nodes first (FIX: lead_routing must be added BEFORE conditional edges referencing it)
def pass_through(state: GraphState):
    return {}

builder.add_node("process_message", process_message_node)
builder.add_node("handle_greeting", handle_greeting)
builder.add_node("retrieve_rag_answer", retrieve_rag_answer)
builder.add_node("handle_unknown", handle_unknown)
builder.add_node("lead_routing", pass_through)       # pass-through router node
builder.add_node("collect_name", collect_name)
builder.add_node("collect_email", collect_email)
builder.add_node("collect_platform", collect_platform)
builder.add_node("execute_mock_tool", execute_mock_tool)
builder.add_node("already_captured", already_captured)

# Entry edge
builder.add_edge(START, "process_message")

# Route from process_message based on detected intent
builder.add_conditional_edges("process_message", route_intent, {
    "handle_greeting": "handle_greeting",
    "retrieve_rag_answer": "retrieve_rag_answer",
    "lead_routing": "lead_routing",
    "handle_unknown": "handle_unknown",
})

# Route lead capture stages
builder.add_conditional_edges("lead_routing", route_lead_capture, {
    "collect_name": "collect_name",
    "collect_email": "collect_email",
    "collect_platform": "collect_platform",
    "execute_mock_tool": "execute_mock_tool",
    "already_captured": "already_captured",
})

# Terminal edges
builder.add_edge("handle_greeting", END)
builder.add_edge("retrieve_rag_answer", END)
builder.add_edge("handle_unknown", END)
builder.add_edge("collect_name", END)
builder.add_edge("collect_email", END)
builder.add_edge("collect_platform", END)
builder.add_edge("execute_mock_tool", END)
builder.add_edge("already_captured", END)

# Compile with in-memory checkpointer for multi-turn thread persistence
memory = MemorySaver()
app = builder.compile(checkpointer=memory)
