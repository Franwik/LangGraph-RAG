from langchain_community.graphs import Neo4jGraph

# Refresh schema is false to avoid unnecessary load
graph = Neo4jGraph(refresh_schema=False)
