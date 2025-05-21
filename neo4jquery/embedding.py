from langchain_neo4j import Neo4jGraph
from sentence_transformers import SentenceTransformer

# 1. Parametri di connessione Neo4j
REMOTE_NEO4J_URI = "neo4j+s://bbbb0499.databases.neo4j.io"
REMOTE_NEO4J_DATABASE = "neo4j"
REMOTE_NEO4J_USER = "neo4j"
REMOTE_NEO4J_PASSWORD = "Vp7D00JQZiERq4s1DnO4HFFwSxSPxZb9S9tZ4ruoaC4"

# 2. Inizializza modello embedding
model = SentenceTransformer("all-MiniLM-L6-v2")

# 3. Connessione al database Neo4j
remote_graph = Neo4jGraph(
    url=REMOTE_NEO4J_URI,
    database=REMOTE_NEO4J_DATABASE,
    username=REMOTE_NEO4J_USER,
    password=REMOTE_NEO4J_PASSWORD,
    refresh_schema=False,
)


# 4. Estrai ID e descrizione dei film
def get_movies_with_description(tx):
    query = """
    MATCH (m:Movie)
    WHERE m.tagline IS NOT NULL AND m.tagline <> ''
    RETURN id(m) AS id, m.tagline AS description
    """
    result = remote_graph.query(query)
    return [{"id": record["id"], "text": record["description"]} for record in result]


# 5. Salva embedding nei nodi
def save_embedding(node_id, embedding):
    query = """
    MATCH (m) WHERE id(m) = $id
    MERGE (e:Embedding {value:$embedding})
    MERGE (m)-[:HAS_EMBEDDING]->(e)
    """
    remote_graph.query(query, {"id": node_id, "embedding": embedding})
    

movies = get_movies_with_description(remote_graph)
for movie in movies:
    # Calcola embedding
    embedding = model.encode(movie["text"], normalize_embeddings=True).tolist()
    
    # Salva embedding nel nodo
    save_embedding(movie["id"], embedding)