from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL

llm = ChatOllama(
    model="llama3.2",
    base_url=OLLAMA_BASE_URL
)