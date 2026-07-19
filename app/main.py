"""
app/main.py
-----------
FastAPI application factory.

Creates the app, registers middleware, wires up all routers,
and runs the DB initialisation on startup.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time

from app.logger import logger

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time_ms = (time.time() - start_time) * 1000
    
    logger.info("Request processed", extra={
        "request_path": request.url.path,
        "http_method": request.method,
        "status_code": response.status_code,
        "response_time_ms": round(process_time_ms, 2)
    })
    
    return response

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
