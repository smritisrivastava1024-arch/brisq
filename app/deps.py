"""
app/deps.py
-----------
Shared FastAPI dependencies.

- require_owner  : validates X-Owner-Password header on protected routes.
- get_groq_client: returns the singleton Groq client.
- get_policy_collection: returns the ChromaDB policy collection.
"""

import httpx
import os
import chromadb
from chromadb.utils import embedding_functions
from fastapi import Header, HTTPException
from groq import AsyncGroq

import jwt
from app.config import GROQ_API_KEY, OWNER_PASSWORD, JWT_SECRET

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
_chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
_chroma_client = chromadb.PersistentClient(path=_chroma_db_path)
policy_collection = _chroma_client.get_or_create_collection(
    name="store_policies",
    embedding_function=_embedding_fn,
)

def check_chroma_health() -> bool:
    """Returns True if the Chroma collection is responsive."""
    try:
        policy_collection.count()
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Owner-auth dependency
# ---------------------------------------------------------------------------
def require_owner(authorization: str = Header(default="")) -> None:
    """FastAPI dependency — raises 401 if the JWT token is missing or invalid."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token format")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("sub") != "owner":
            raise HTTPException(status_code=401, detail="Invalid token scope")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
