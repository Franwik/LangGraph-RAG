from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from typing import Annotated
from neo4j_graph import init_connection
from llm import llm

class State(TypedDict):
    messages: Annotated[list, add_messages]
    cypher_query: str
    neo4j_result: list

graph_builder = StateGraph(State)

def generate_query(state: State):
    messages = state["messages"]
    
    system_prompt = {
        "role": "system",
        "content": (
            "Sei un assistente che genera query Cypher per interrogare un database Neo4j. "
            "Rispondi solo con la query, senza spiegazioni. "
            "Il database contiene entità come: Movie, Person, Director, Actor, Genre, ecc."
        )
    }

    user_prompt = messages[-1]  # ultimo messaggio utente

    query = llm.invoke([system_prompt, user_prompt]).content.strip()

    return {"cypher_query": query}

def clean_cypher_query(query: str) -> str:
    return (
        query.replace("```cypher", "")
             .replace("```", "")
             .strip()
    )

def run_query(state: State):
    conn = init_connection()
    query = state["cypher_query"]

    query = clean_cypher_query(query)

    results = conn.query(query)

    return {"neo4j_result": results}

def chatbot(state: State):
    from langchain_core.messages import AIMessage, HumanMessage

    user_msg = state["messages"][-1].content
    results = state["neo4j_result"]

    # Format the Neo4j results for context
    if results:
        result_text = "\n".join([str(row) for row in results])
    else:
        result_text = "Nessun risultato trovato nel grafo."

    # Compose a prompt with both the question and the context
    prompt = f"""Rispondi alla domanda seguente usando solo le informazioni qui sotto.
        Se non riesci a trovare una risposta, di' che non lo sai.

        Domanda: {user_msg}

        Informazioni dal grafo:
        {result_text}
        """

    # Call the LLM
    answer = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": state["messages"] + [AIMessage(content=answer.content)],
    }

# Creation of the graph
graph_builder.add_node("generate_query", generate_query)
graph_builder.add_node("run_query", run_query)
graph_builder.add_node("chatbot", chatbot)

graph_builder.set_entry_point("generate_query")
graph_builder.add_edge("generate_query", "run_query")
graph_builder.add_edge("run_query", "chatbot")
graph_builder.set_finish_point("chatbot")