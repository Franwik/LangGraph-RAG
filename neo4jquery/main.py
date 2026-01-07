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
    ORDER BY score DESC
    RETURN item
    """

    result = remote_graph.query(retrieve_query, {"embedding": embedding})
    return [(record["item"]) for record in result]


def get_subgraphs(item_id):

    print("Retrieving subgraphs")

    query = """
    MATCH (root {id: $item_id})
    CALL apoc.path.subgraphAll(root, {maxLevel: 1}) YIELD nodes, relationships
    RETURN nodes, relationships
    """

    result = remote_graph.query(query, {"item_id": item_id})
    return result[0] if result else {"nodes": [], "relationships": []}


# def import_subgraphs(subgraph_record):
#     print("Importing subgraphs into local graph")
    
#     nodes = subgraph_record["nodes"]
#     relationships = subgraph_record["relationships"]

#     # query = """
#     # CALL apoc.refactor.cloneSubgraph($nodes, [rel in $relationships])
#     # YIELD input, output, error
#     # RETURN input, output, error
#     # """

#     query = """
    
#     """

#     local_graph.query(query, {
#         "nodes": nodes,
#         "relationships": relationships
#     })


def import_subgraphs(subgraph_record):
    print("Importing subgraphs into local graph")

    nodes = subgraph_record["nodes"]
    relationships = subgraph_record["relationships"]

    # Importa i nodi con MERGE su tutte le proprietà
    for node in nodes:
        labels = ":".join(node.labels)
        props = dict(node)

        # Costruisci MATCH condition per ogni proprietà
        merge_parts = ", ".join([f"{k}: ${k}" for k in props])
        set_props = ", ".join([f"n.{k} = ${k}" for k in props])

        query = f"""
        MERGE (n:{labels} {{ {merge_parts} }})
        SET {set_props}
        """
        local_graph.query(query, props)

    # Importa le relazioni
    for rel in relationships:
        start_node = dict(rel.start_node)
        end_node = dict(rel.end_node)
        rel_props = dict(rel)
        rel_type = rel.type

        # MATCH conditions per start e end nodes
        start_match = " AND ".join([f"a.{k} = $start_{k}" for k in start_node])
        end_match = " AND ".join([f"b.{k} = $end_{k}" for k in end_node])
        rel_set = ", ".join([f"r.{k} = $rel_{k}" for k in rel_props])

        query = f"""
        MATCH (a), (b)
        WHERE {start_match} AND {end_match}
        MERGE (a)-[r:{rel_type}]->(b)
        SET {rel_set}
        """

        # Prefissa le chiavi per evitare conflitti nei parametri
        params = {f"start_{k}": v for k, v in start_node.items()}
        params.update({f"end_{k}": v for k, v in end_node.items()})
        params.update({f"rel_{k}": v for k, v in rel_props.items()})

        local_graph.query(query, params)


def create_shard(embedding):
    similar_items = find_similar_items(embedding)

    for item in similar_items:
        item_id = item.get("id")
        if not item_id:
            continue
        subgraph = get_subgraphs(item_id)
        # print(subgraph)
        # break
        import_subgraphs(subgraph)


create_shard(embedding)