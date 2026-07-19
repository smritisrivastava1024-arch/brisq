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

# CORS — wildcard by default; tighten in production
CORS_ORIGINS: list[str] = ["*"]
