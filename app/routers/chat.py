"""
app/routers/chat.py
--------------------
Chat endpoints (both customer-facing and owner-facing) and
direct single-agent endpoints.

Paths (unchanged from original api.py):
  POST /chat/customer
  POST /chat/owner
  POST /customer-ai
  POST /operations-ai
  POST /finance-ai
  POST /growth-ai
  POST /executive-ai
  POST /supplier-ai
  POST /marketing-ai
"""

from fastapi import APIRouter, Depends

from app.config import MODEL
from app.deps import groq_client, require_owner
from app.schemas import ChatRequest

from app.agents.customer_ai import run_customer_ai
from app.agents.operations_ai import run_operations_ai
from app.agents.finance_ai import run_finance_ai
from app.agents.growth_ai import run_growth_ai
from app.agents.executive_ai import run_executive_ai
from app.agents.supplier_ai import run_supplier_ai
from app.agents.marketing_ai import run_marketing_ai

from orchestrator import route_message

router = APIRouter()


# ---------------------------------------------------------------------------
# Orchestrated chat
# ---------------------------------------------------------------------------

@router.post("/chat/customer")
async def chat_customer_endpoint(request: ChatRequest):
    agent_functions = {
        "customer_ai": lambda msg: run_customer_ai(msg, request.history),
    }
    return await route_message(
        request.message,
        groq_client,
        MODEL,
        agent_functions,
        request.history,
    )


@router.post("/chat/owner")
async def chat_owner_endpoint(
    request: ChatRequest,
    _: None = Depends(require_owner),
):
    agent_functions = {
        "customer_ai": lambda msg: run_customer_ai(msg, request.history),
        "operations_ai": lambda msg: run_operations_ai(msg, request.history),
        "finance_ai": lambda msg: run_finance_ai(msg, request.history),
        "growth_ai": lambda msg: run_growth_ai(msg, request.history),
        "executive_ai": lambda msg: run_executive_ai(msg, request.history),
        "supplier_ai": lambda msg: run_supplier_ai(msg, request.history),
        "marketing_ai": lambda msg: run_marketing_ai(msg, groq_client, MODEL, request.history),
    }
    return await route_message(
        request.message,
        groq_client,
        MODEL,
        agent_functions,
        request.history,
    )


# ---------------------------------------------------------------------------
# Direct single-agent endpoints
# ---------------------------------------------------------------------------

@router.post("/customer-ai")
async def customer_ai_endpoint(request: ChatRequest):
    return {"agent": "customer_ai", "response": await run_customer_ai(request.message, request.history)}


@router.post("/operations-ai")
async def operations_ai_endpoint(request: ChatRequest):
    return {"agent": "operations_ai", "response": await run_operations_ai(request.message, request.history)}


@router.post("/finance-ai")
async def finance_ai_endpoint(request: ChatRequest):
    return {"agent": "finance_ai", "response": await run_finance_ai(request.message, request.history)}


@router.post("/growth-ai")
async def growth_ai_endpoint(request: ChatRequest):
    return {"agent": "growth_ai", "response": await run_growth_ai(request.message, request.history)}


@router.post("/executive-ai")
async def executive_ai_endpoint(request: ChatRequest):
    return {"agent": "executive_ai", "response": await run_executive_ai(request.message, request.history)}


@router.post("/supplier-ai")
async def supplier_ai_endpoint(request: ChatRequest):
    return {"agent": "supplier_ai", "response": await run_supplier_ai(request.message, request.history)}


@router.post("/marketing-ai")
async def marketing_ai_endpoint(request: ChatRequest):
    return {
        "agent": "marketing_ai",
        "response": await run_marketing_ai(request.message, groq_client, MODEL, request.history),
    }
