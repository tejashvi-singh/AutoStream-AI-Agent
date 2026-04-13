# AutoStream Social-to-Lead Agentic Workflow

AutoStream is a fictional SaaS platform providing automated video editing for content creators. This project implements a conversational LangGraph-powered AI that seamlessly routes user intent, retrieves pricing/policy information using RAG, and qualifies/captures leads in a structured workflow.

## Project Structure
```text
autostream-agent/
├── app/
│   ├── state.py       # Defines LangGraph state (Thread dictionary)
│   ├── tools.py       # Mock lead capture tool logic
│   ├── rag.py         # Local huggingface embeddings FAISS retriever
│   ├── intents.py     # LLM structured output classification logic
│   ├── graph.py       # Core LangGraph compile (Nodes, Edges, MemorySaver)
│   └── main.py        # FastAPI endpoints integrating the compiled Graph
├── frontend/
│   └── streamlit_app.py # Clean SaaS-style UI with conversation history
├── knowledge_base.md  # Documents used for RAG
├── requirements.txt   # Dependencies
└── README.md          # You are here!
```

## Architecture Explanation

This application implements an Agentic "Social-to-Lead" architecture using **LangGraph** to construct a highly reliable, stateful multi-turn workflow. 
User messages flow into a Fast API backend which passes them to the LangGraph `StateGraph`. A unified `GraphState` preserves the growing conversation history and extracted lead variables (`name`, `email`, `creator_platform`).

The entry node (`process_message_node`) intelligently branches logic:
1. It uses an LLM to **classify intent** into greetings, pricing inquiries, or high-intent leads.
2. It simultaneously runs a parallel structural extraction if "high intent" is active, plucking entities out of colloquial chat.

Edges route execution to contextual responses (like `retrieve_rag_answer` for pricing queries) or into the gated lead-capture flow. In the lead-capture sequence, nodes inspect the state to ask follow-up questions iteratively. A strict mock tool execution only engages once all three explicit tracking points (Name, Email, Platform) are populated in memory. 

By separating intent, RAG memory retrieval, and lead management into disparate nodes, the application stays highly modular making it less prone to LLM hallucination and easily scalable.

## Why LangGraph?
LangGraph was chosen over simple vanilla LangChain because we require strict boundaries for multi-turn lead extraction (statefulness). While a standard chain is rigid or completely uncontrolled (like an un-configured REACT agent), LangGraph lets us define precise, loop-friendly paths and persistence using `MemorySaver`. This ensures that a tool *cannot* be called prematurely due to the hardcoded routing constraints checked at the graph's edges.

## Memory & State Management
Memory is maintained locally via LangGraph's native `MemorySaver()` checkpointer. The Streamlit UI generates a unique `thread_id` per user session which is transmitted to the FastAPI layer. Graph nodes share information strictly by returning delta updates to the `GraphState` dictionary (e.g. extending messages, or updating a specific lead variable).

## WhatsApp Webhook Integration Strategy
If this workflow were to be integrated with WhatsApp Business API:
1. **Webhook Endpoint:** The FastAPI server would expose a specific `POST /webhook` route to consume Meta's payload, responding instantly to handshake challenges.
2. **Thread ID Mapping:** The user's WhatsApp phone number would act as the LangGraph `thread_id` to reliably load state across distributed messages.
3. **Response Delivery:** Instead of returning a synchronous HTTP JSON response, the `execute_mock_tool` or end-nodes would trigger async HTTP `POST` requests directly via Meta's Graph API to push standard text messages back to the user's handset. 

## Local Run Steps

1. **Install Requirements:**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables:**
Create a `.env` in the root folder (or `export` natively):
```bash
GROQ_API_KEY=groq_api_key
```

3. **Run the Backend (FastAPI)**
```bash
cd app
python -m uvicorn main:fastapi_app --reload --port 8000
```
*(Or from project root: `python -m uvicorn app.main:fastapi_app --reload --port 8000`)*

4. **Run the Frontend (Streamlit)**
In a new terminal:
```bash
streamlit run frontend/streamlit_app.py
```

## Demo Conversation Flow
Try this exact flow in the UI to see the multi-turn agent traverse all states:
1. **User**: "Hi, tell me about your pricing" 
   *(Triggers RAG node, returns info on Basic/Pro plans)*
2. **User**: "I want to try the Pro plan for my YouTube channel" 
   *(Detects high-intent, extracts platform "YouTube", triggers lead flow, asks name)*
3. **User**: "My name is John" 
   *(Extracts name, asks email)*
4. **User**: "john@example.com" 
   *(Extracts email, conditions met -> mock tool successfully executed!)*
