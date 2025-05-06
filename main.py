from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from neo4j import GraphDatabase

# Connessione al database Neo4j
NEO4J_URI = "neo4j+s://3299886a.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "4VGjh_3hF4BzjvuUlYTN9A3v8Lw15fSuL4avnzBPF7E"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_neo4j_query():
    query = """
    MATCH (p:Person {name:'Tom Hanks'})-[r]-(m:Movie) RETURN p,r,m
    """
    # print("Executing Neo4j query...")
    with driver.session() as session:
        result = session.run(query)
        context = ""
        for record in result:
            
            p = record["p"]
            r = record["r"]
            m = record["m"]

            # Estrai label
            p_label = list(p.labels)[0] if p.labels else "Node"
            m_label = list(m.labels)[0] if m.labels else "Node"
            r_type = r.type

            # Estrai proprietà
            p_props = dict(p)
            m_props = dict(m)
            r_props = dict(r)

            context += f"(:{p_label} {p_props})-[:{r_type} {r_props}]->(:{m_label} {m_props})\n"
    # print(context)
    # print("Neo4j query executed successfully.")
    return context

template = """
Answer the question below based on the database.
If the user doesn't mention anything about the database, please answer based on your own knowledge.
If the user asks about the database, please answer based on the database context.
Keep the answer simple, short and concise and use the same language the question is in.

Here is the conversation history: {history}

Here is the database context: {context}

Question: {question}

Answer:
"""

model = OllamaLLM(model="llama3")
promt = ChatPromptTemplate.from_template(template)
chain = promt | model

def handle_conversation():
  history = ""
  print("--- Welcome to the AI ChatBot, type '\\q' to quit ---\n")
  while True:
    user_input = input("You: ")

    if user_input.lower() == '\\q':
        break
    elif user_input.startswith('\\'):
        print("No such command...")
    else:
        context = run_neo4j_query()
        
        # print("\n--- AI is thinking... ---\n")
        result = chain.invoke({"history": history, "context":context, "question": user_input})
        print("\nAI: ", result, "\n")
        history += f"You: {user_input}\nAI: {result}\n"
        # print("--- Conversation history updated ---\n")

if __name__ == "__main__":
    handle_conversation()