from fastapi import APIRouter
from pydantic import BaseModel
from graph_logic import graph_builder

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat(req: ChatRequest):
    user_input = req.message
    print(f"User input: {user_input} \n\n")
    graph = graph_builder.compile()

    state_input = {
        "messages": [{"role": "user", "content": user_input}],
        "cypher_query": "",
        "neo4j_result": []
    }

    result = graph.invoke(state_input)

    return {
        "response": result["messages"][-1].content
    }