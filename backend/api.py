from fastapi import APIRouter
from pydantic import BaseModel
from graph_logic import graph

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    user_input = req.message
    output = ""
    try:
        for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
            for value in event.values():
                output = value["messages"][-1].content
    except Exception as e:
        output = f"Error: {str(e)}"
    return {"response": output}