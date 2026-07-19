"""
app/deps.py
-----------
Shared FastAPI dependencies.

- require_owner  : validates X-Owner-Password header on protected routes.
- get_groq_client: returns the singleton Groq client.
- get_policy_collection: returns the ChromaDB policy collection.
"""

import httpx
import chromadb
from chromadb.utils import embedding_functions
from fastapi import Header, HTTPException
from groq import AsyncGroq

from app.config import GROQ_API_KEY, OWNER_PASSWORD

# ---------------------------------------------------------------------------
# Clients (initialized via lifespan)
# ---------------------------------------------------------------------------
shared_http_client: httpx.AsyncClient = None
groq_client: AsyncGroq = None

def init_clients():
    global shared_http_client, groq_client
    shared_http_client = httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"})
    groq_client = AsyncGroq(api_key=GROQ_API_KEY, http_client=shared_http_client)

async def close_clients():
    global shared_http_client
    if shared_http_client:
        await shared_http_client.aclose()

# ---------------------------------------------------------------------------
# ChromaDB policy collection (singleton at module level)
# ---------------------------------------------------------------------------
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_chroma_client = chromadb.PersistentClient(path="./chroma_db")
policy_collection = _chroma_client.get_or_create_collection(
    name="store_policies",
    embedding_function=_embedding_fn,
)


# ---------------------------------------------------------------------------
# Owner-auth dependency
# ---------------------------------------------------------------------------
def require_owner(x_owner_password: str = Header(default="")) -> None:
    """FastAPI dependency — raises 401 if the owner password header is wrong."""
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")
