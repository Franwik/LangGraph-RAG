from langchain_neo4j import Neo4jGraph
from sentence_transformers import SentenceTransformer

# Configura le credenziali e l'URL del tuo database
# REMOTE_NEO4J_URI = "neo4j://143.225.233.156:7687"
# REMOTE_NEO4J_DATABASE = "alice"
# REMOTE_NEO4J_USER = "fdonnarumma"
# REMOTE_NEO4J_PASSWORD = "fDonnarumma"

REMOTE_NEO4J_URI = "neo4j+s://bbbb0499.databases.neo4j.io"
REMOTE_NEO4J_DATABASE = "neo4j"
REMOTE_NEO4J_USER = "neo4j"
REMOTE_NEO4J_PASSWORD = "Vp7D00JQZiERq4s1DnO4HFFwSxSPxZb9S9tZ4ruoaC4"

LOCAL_NEO4J_URI = "bolt://localhost:7689"
LOCAL_NEO4J_DATABASE = "neo4j"
LOCAL_NEO4J_USER = "neo4j"
LOCAL_NEO4J_PASSWORD = "Vp7D00JQZiERq4s1DnO4HFFwSxSPxZb9S9tZ4ruoaC4"

# Modello per creare embedding da testo
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Frase da cercare
description = "I want to see an action movie"
embedding = model.encode(description, normalize_embeddings=True).tolist()

# Crea la connessione
remote_graph = Neo4jGraph(
    url=REMOTE_NEO4J_URI,
    database=REMOTE_NEO4J_DATABASE,
    username=REMOTE_NEO4J_USER,
    password=REMOTE_NEO4J_PASSWORD,
    refresh_schema=False,
)

local_graph = Neo4jGraph(
    url=LOCAL_NEO4J_URI,
    database=LOCAL_NEO4J_DATABASE,
    username=LOCAL_NEO4J_USER,
    password=LOCAL_NEO4J_PASSWORD,
    refresh_schema=False,
)


def find_similar_items(embedding):

    # Query ANN + risalita al nodo collegato
    retrieve_query = """
    CALL db.index.vector.queryNodes("abstractEmbedding", 10, $embedding) YIELD node, score
    MATCH (item)-[:HAS_EMBEDDING]->(node)
    RETURN item, labels(item) AS item_labels
    ORDER BY score DESC
    """

    result = remote_graph.query(retrieve_query, {"embedding": embedding})
    return [(record["item"], record["item_labels"]) for record in result]

def create_shard(embedding):
    # Recupera nodi simili dal remoto
    results = find_similar_items(embedding)

    for item, item_labels in results:

        item_props = item
        item_id = item_props.pop("id", None)

        # Costruisci dinamicamente la query di creazione
        create_node_query = f"""
        MERGE (n:{':'.join(item_labels)} {{id: $id}})
        SET n += $props
        """

        # Crea il nodo nel grafo locale
        local_graph.query(create_node_query, {"props": item_props, "id": item_id})

        # Copia i nodi connessi e relazioni
        related_query_outgoing = """
        MATCH (i {id: $item_id})-[r]->(related)
        RETURN type(r) AS rel_type, properties(r) AS rel_props, labels(related) AS related_labels, properties(related) AS related_props
        """

        outgoing_relations = remote_graph.query(related_query_outgoing, {"item_id": item_id})

        for rel in outgoing_relations:

            rel_type = rel["rel_type"]
            rel_props = rel["rel_props"]
            related_labels = rel["related_labels"]
            related_props = dict(rel["related_props"])
            related_id = related_props.pop("id", None)

            # Crea nodo collegato
            create_related_node = f"""
            MERGE (n:{':'.join(related_labels)} {{id: $id}})
            SET n += $props
            """

            create_embedding_node = f"""
            MATCH (n {{id: $id}})
            MERGE (m:{':'.join(related_labels)} {{value: $embedding}})
            MERGE (n)-[:HAS_EMBEDDING]->(m)
            """

            if related_id is None:
                internal_embedding = related_props.pop("value", None)
                local_graph.query(create_embedding_node, {"props": related_props, "id": item_id, "embedding": internal_embedding})
            else:
                local_graph.query(create_related_node, {"props": related_props, "id": related_id})

                # Crea la relazione tra `n` e `m`
                create_rel_query = f"""
                MATCH (n {{id: $n_id}}), (m {{id: $m_id}})
                MERGE (n)-[r:{rel_type}]->(m)
                SET r += $props
                """
                local_graph.query(create_rel_query, {
                    "n_id": item_id,
                    "m_id": related_id,
                    "props": rel_props
                })


        related_query_ingoing = """
        MATCH (i {id: $item_id})<-[r]-(related)
        RETURN type(r) AS rel_type, properties(r) AS rel_props, labels(related) AS related_labels, properties(related) AS related_props
        """

        ingoing_relations = remote_graph.query(related_query_ingoing, {"item_id": item_id})

        for rel in ingoing_relations:

            rel_type = rel["rel_type"]
            rel_props = rel["rel_props"]
            related_labels = rel["related_labels"]
            related_props = dict(rel["related_props"])
            related_id = related_props.pop("id", None)

            # Crea nodo collegato
            create_related_node = f"""
            MERGE (n:{':'.join(related_labels)} {{id: $id}})
            SET n += $props
            """

            local_graph.query(create_related_node, {"props": related_props, "id": related_id})

            # Crea la relazione tra `n` e `m`
            create_rel_query = f"""
            MATCH (n {{id: $n_id}}), (m {{id: $m_id}})
            MERGE (n)<-[r:{rel_type}]-(m)
            SET r += $props
            """
            local_graph.query(create_rel_query, {
                "n_id": item_id,
                "m_id": related_id,
                "props": rel_props
            })

create_shard(embedding)