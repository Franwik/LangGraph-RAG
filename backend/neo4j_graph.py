from langchain_neo4j import Neo4jGraph
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

graph = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD,
    refresh_schema=True,
)

def init_connection():
    return graph