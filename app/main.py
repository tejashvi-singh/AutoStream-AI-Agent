from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

from app.graph import app as workflow

fastapi_app = FastAPI(title="AutoStream Social-to-Lead API")

class ChatRequest(BaseModel):
    thread_id: str
    message: str

class ChatResponse(BaseModel):
    response: str
    intent: str | None
    lead_captured: bool | None

@fastapi_app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    # Configure thread configuration for MemorySaver
    config = {"configurable": {"thread_id": request.thread_id}}
    
    # User message
    user_message = HumanMessage(content=request.message)
    
    # Output from workflow
    output = workflow.invoke({"messages": [user_message]}, config)
    
    # Retrieve last AIMessage
    latest_message = output["messages"][-1].content
    intent = output.get("intent")
    lead_captured = output.get("lead_captured", False)
    
    return ChatResponse(
        response=latest_message,
        intent=intent,
        lead_captured=lead_captured
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8000)
