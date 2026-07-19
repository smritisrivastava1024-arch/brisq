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

from app.config import CORS_ORIGINS
from app.routers import chat, approvals, abandoned_carts

from database import initialize_database

app = FastAPI(title="Brisq E-commerce AI Operations API")

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    initialize_database()


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
