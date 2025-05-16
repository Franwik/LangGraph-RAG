from langchain_neo4j import Neo4jGraph
from sentence_transformers import SentenceTransformer

# Configura le credenziali e l'URL del tuo database
# NEO4J_URI = "neo4j+s://bbbb0499.databases.neo4j.io"
# NEO4J_USER = "neo4j"
# NEO4J_PASSWORD = "Vp7D00JQZiERq4s1DnO4HFFwSxSPxZb9S9tZ4ruoaC4"

NEO4J_URI = "neo4j://143.225.233.156:7687"
NEO4J_DATABASE = "alice"
NEO4J_USER = "fdonnarumma"
NEO4J_PASSWORD = "fDonnarumma"

# Modello per creare embedding da testo
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Frase da cercare
text = "This program is designed to answer questions about epilepsy, including symptoms, treatment options, seizure types, first aid, and lifestyle tips. It provides clear, reliable, and easy-to-understand information based on trusted medical sources, helping users learn more about managing and understanding epilepsy."
embedding = model.encode(text, normalize_embeddings=True).tolist()

# print(f"\n\nEmbedding: {embedding}\n\n")

# Crea la connessione
graph = Neo4jGraph(
    url=NEO4J_URI,
    database=NEO4J_DATABASE,
    username=NEO4J_USER,
    password=NEO4J_PASSWORD,
    refresh_schema=True,
)

# Query ANN + risalita al nodo collegato
cypher_query = """
CALL db.index.vector.queryNodes("abstractEmbedding", 100, $embedding) YIELD node, score
MATCH (item)-[:HAS_EMBEDDING]->(node)
RETURN item, score
ORDER BY score DESC
"""

def find_similar_items(embedding):
    result = graph.query(cypher_query, {"embedding": embedding})
    return [(record["item"], record["score"]) for record in result]

# Risultati
results = find_similar_items(embedding)
for item, score in results:
    print(f"{item['name']} (score: {score:.4f})")