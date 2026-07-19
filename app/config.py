"""
app/config.py
-------------
Centralised environment-variable loading.
All other modules import from here — nothing else calls load_dotenv() or os.getenv().
"""

import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
MODEL: str = "llama-3.3-70b-versatile"

# Owner dashboard
OWNER_PASSWORD: str = os.getenv("OWNER_PASSWORD", "changeme123")
JWT_SECRET: str = os.getenv("JWT_SECRET", "super-secret-default-key-please-change")

# CORS — explicit list; set ALLOWED_ORIGINS in .env as comma-separated list for production
# Wildcard + allow_credentials=True is rejected by browsers, so we always list origins explicitly.
_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
)
CORS_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]
