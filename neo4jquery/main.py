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
description = "This program is designed to answer questions about epilepsy, including symptoms, treatment options, seizure types, first aid, and lifestyle tips. It provides clear, reliable, and easy-to-understand information based on trusted medical sources, helping users learn more about managing and understanding epilepsy."
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
    # retrieve_query = """
    # CALL db.index.vector.queryNodes("abstractEmbedding", 100, $embedding) YIELD node, score
    # MATCH (item)-[:HAS_EMBEDDING]->(node)
    # RETURN item, score
    # ORDER BY score DESC
    # """

    retrieve_query = """
    MATCH (item:Person {name:'Tom Hanks'})
    RETURN item, labels(item) AS item_labels
    """

    result = remote_graph.query(retrieve_query, {"embedding": embedding})
    return [(record["item"], record["item_labels"]) for record in result]
    # return [(record["item"], record["score"]) for record in result]

def create_shard(embedding):
    # Recupera nodi simili dal remoto
    results = find_similar_items(embedding)

    for item, item_labels in results:

        # Costruisci dinamicamente la query di creazione
        create_node_query = f"""
        CREATE (n:{':'.join(item_labels)})
        SET n += $props
        RETURN id(n) as local_id
        """

        # Crea il nodo nel grafo locale
        local_result = local_graph.query(create_node_query, {"props": item})
        local_id = local_result[0]["local_id"]
        print(local_id)

        # Copia i nodi connessi e relazioni
        related_query = """
        MATCH (i)-[r]->(related)
        WHERE id(i) = $remote_id
        RETURN type(r) AS rel_type, properties(r) AS rel_props, labels(related) AS related_labels, properties(related) AS related_props
        """

        remote_id = item.metadata["id"] # da usare pmcid
        relations = remote_graph.query(related_query, {"remote_id": remote_id})

        for rel in relations:
            # Crea nodo collegato
            create_related_node = f"""
            CREATE (m:{':'.join(rel["related_labels"])})
            SET m += $props
            RETURN id(m) as related_id
            """
            related_result = local_graph.query(create_related_node, {"props": rel["related_props"]})
            related_id = related_result[0]["related_id"]

            # Crea la relazione tra `n` e `m`
            create_rel_query = f"""
            MATCH (n), (m)
            WHERE id(n) = $n_id AND id(m) = $m_id
            CREATE (n)-[r:{rel['rel_type']}]->(m)
            SET r += $props
            """
            local_graph.query(create_rel_query, {
                "n_id": local_id,
                "m_id": related_id,
                "props": rel["rel_props"]
            })
        

    # for item, score in results:
    #     # Estrai proprietà del nodo principale
    #     item_props = dict(item)
    #     item_labels = list(item.labels)

    #     # Costruisci dinamicamente la query di creazione
    #     create_node_query = f"""
    #     CREATE (n:{':'.join(item_labels)})
    #     SET n += $props
    #     RETURN id(n) as local_id
    #     """

    #     # Crea il nodo nel grafo locale
    #     local_result = local_graph.query(create_node_query, {"props": item_props})
    #     local_id = local_result[0]["local_id"]

    #     # Copia i nodi connessi e relazioni
    #     related_query = """
    #     MATCH (i)-[r]->(related)
    #     WHERE id(i) = $remote_id
    #     RETURN type(r) AS rel_type, properties(r) AS rel_props, labels(related) AS related_labels, properties(related) AS related_props
    #     """

    #     remote_id = item.metadata["id"]
    #     relations = remote_graph.query(related_query, {"remote_id": remote_id})

    #     for rel in relations:
    #         # Crea nodo collegato
    #         create_related_node = f"""
    #         CREATE (m:{':'.join(rel["related_labels"])})
    #         SET m += $props
    #         RETURN id(m) as related_id
    #         """
    #         related_result = local_graph.query(create_related_node, {"props": rel["related_props"]})
    #         related_id = related_result[0]["related_id"]

    #         # Crea la relazione tra `n` e `m`
    #         create_rel_query = f"""
    #         MATCH (n), (m)
    #         WHERE id(n) = $n_id AND id(m) = $m_id
    #         CREATE (n)-[r:{rel['rel_type']}]->(m)
    #         SET r += $props
    #         """
    #         local_graph.query(create_rel_query, {
    #             "n_id": local_id,
    #             "m_id": related_id,
    #             "props": rel["rel_props"]
    #         })


create_shard(embedding)