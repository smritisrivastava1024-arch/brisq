"""
app/main.py
-----------
FastAPI application factory.

Creates the app, registers middleware, wires up all routers,
and runs the DB initialisation on startup.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import CORS_ORIGINS
from app.routers import chat, approvals, abandoned_carts, auth
from app.deps import init_clients, close_clients

from database import initialize_database

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    initialize_database()
    init_clients()
    yield
    # Shutdown
    await close_clients()

app = FastAPI(title="Brisq E-commerce AI Operations API", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(chat.router)
app.include_router(approvals.router)
app.include_router(abandoned_carts.router)
app.include_router(auth.router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "Shiftora API running.",
        "customer_chat": "/chat/customer",
        "owner_chat": "/chat/owner",
        "approvals": "/approvals",
        "agents": [
            "customer_ai",
            "operations_ai",
            "finance_ai",
            "growth_ai",
            "executive_ai",
            "supplier_ai",
        ],
    }
