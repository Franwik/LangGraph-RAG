import os
from dotenv import load_dotenv

load_dotenv()  # Optional, if you're using a .env file

NEO4J_URI = "neo4j+s://bbbb0499.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Vp7D00JQZiERq4s1DnO4HFFwSxSPxZb9S9tZ4ruoaC4"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")

os.environ["NEO4J_DATABASE"] = "alice"
os.environ["NEO4J_URI"] = NEO4J_URI
os.environ["NEO4J_USERNAME"] = NEO4J_USER
os.environ["NEO4J_PASSWORD"] = NEO4J_PASSWORD