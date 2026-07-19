from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4
import json
import os
import httpx
from dotenv import load_dotenv
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions
from marketing_ai import run_marketing_ai
from database import create_abandoned_cart, get_pending_abandoned_carts
from database import (
    initialize_database,
    create_abandoned_cart,
    get_pending_abandoned_carts,
    get_abandoned_cart_by_token,
    update_abandoned_cart_ai_messages,
    create_approval,
    get_pending_approvals,
    get_all_approvals,
    approve_request,
    reject_request,
)
from orchestrator import route_message

from shopify_tools import (
    get_order_status,
    check_refund,
    check_inventory,
    get_all_products,
    forecast_reorder,
    forecast_all_reorders,
    get_revenue_summary,
    get_top_products,
    get_refund_summary,
    get_revenue_trends,
    get_customer_insights,
    get_order_insights,
    categorize_shopify_transactions,
    analyze_refund_risk,
    get_weekly_pnl_report,
    get_cash_flow_dashboard,
    get_profit_forecast,
)


load_dotenv()

app = FastAPI(title="Brisq E-commerce AI Operations API")

initialize_database()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.Client(headers={"User-Agent": "Mozilla/5.0"})

client = Groq(
    api_key=os.getenv("GROQ_API_KEY"),
    http_client=http_client
)

MODEL = "llama-3.3-70b-versatile"
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "changeme123")



embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

policy_collection = chroma_client.get_or_create_collection(
    name="store_policies",
    embedding_function=embedding_fn
)

STRICT_INSTRUCTION = {
    "role": "system",
    "content": (
        "IMPORTANT: Only use the exact data returned by the tool above. "
        "Do not invent or assume any details not explicitly returned by the tool."
    )
}


class ChatRequest(BaseModel):
    message: str
    history: list = []



class AbandonedCartRequest(BaseModel):
    cart_token: str
    customer_name: str
    email: str
    phone: str
    items: str
    cart_value: float
    checkout_url: str

def safe_tool_args(tool_call):
    try:
        return json.loads(tool_call.function.arguments or "{}") or {}
    except Exception:
        return {}


def search_policies(query):
    results = policy_collection.query(query_texts=[query], n_results=2)

    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])

    return "No relevant policy found."


def create_refund_approval(order_id, reason="Customer requested refund"):
    risk_report = analyze_refund_risk(order_id)

    if "not found" in risk_report.lower():
        return risk_report

    create_approval(
        approval_type="refund",
        reference_id=order_id,
        title=f"Refund approval for order #{order_id}",
        description=reason,
        payload={
            "order_id": order_id,
            "reason": reason,
            "risk_report": risk_report,
            "action": "refund_requires_owner_approval"
        }
    )

    return (
        f"Refund approval request created for order #{order_id}.\n\n"
        f"{risk_report}\n\n"
        f"Important: No refund has been issued yet. "
        f"The owner must approve or reject this request from the approval queue."
    )


support_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up the status and delivery date of a customer order by order number",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order number, for example 1001"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_refund",
            "description": "Check if an order is eligible for refund",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order number"
                    }
                },
                "required": ["order_id"]
            }
        }
    }
]


inventory_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check stock levels for a specific product by name",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The product name"
                    }
                },
                "required": ["item_name"]
            }
        }
    }
]


policy_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": "Search store policies for return, refund, shipping, cancellation, warranty, or damaged item rules",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's policy question"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


operations_tools = [
    {
        "type": "function",
        "function": {
            "name": "forecast_reorder",
            "description": "Forecast when one specific product will run out of stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_name": {
                        "type": "string",
                        "description": "The exact product name"
                    }
                },
                "required": ["item_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_products",
            "description": "Get all product names in the store",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_all_reorders",
            "description": "Get stockout and reorder forecast for all products",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_insights",
            "description": "Get pending orders, fulfillment time, and unfulfilled order value",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days to look back"
                    }
                },
                "required": []
            }
        }
    }
]


finance_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_revenue_summary",
            "description": "Get total revenue, order count, and average order value",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_products",
            "description": "Get best-selling products by units and revenue",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_refund_summary",
            "description": "Get refund count, refund rate, and total refunded amount",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_revenue_trends",
            "description": "Compare revenue this week vs last week and this month vs last month",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_insights",
            "description": "Get new vs returning customers and top customers by spend",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_insights",
            "description": "Get pending orders, fulfillment time, and unfulfilled order value",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_shopify_transactions",
            "description": "Bookkeeping categories and accounting-style journal entries",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_refund_risk",
            "description": "Analyze refund or chargeback risk for a specific Shopify order",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The Shopify order number"
                    }
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_refund_approval",
            "description": "Create a pending refund approval request for owner review",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_pnl_report",
            "description": "Generate weekly profit and loss report",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cash_flow_dashboard",
            "description": "Generate cash flow dashboard",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_profit_forecast",
            "description": "Forecast revenue and profit based on recent sales",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer"}
                },
                "required": []
            }
        }
    }
]


def run_customer_ai(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Customer AI. "
                "Help customers with order status, product availability, refunds, returns, shipping, and store policies. "
                "Use tools for real order, inventory, and policy data. "
                "Never invent order details, refund status, delivery dates, or policy terms. "
                "Do not create owner refund approvals here. Customer AI can only check eligibility or explain policy."
            )
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    tools = support_tools + inventory_tools + policy_tools

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = safe_tool_args(tool_call)

            if tool_name == "get_order_status":
                result = get_order_status(args["order_id"])
            elif tool_name == "check_refund":
                result = check_refund(args["order_id"])
            elif tool_name == "check_inventory":
                result = check_inventory(args["item_name"])
            elif tool_name == "search_policies":
                result = search_policies(args["query"])
            else:
                result = "Tool not found."

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                }
            )

        messages.append(STRICT_INSTRUCTION)

        final = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0
        )

        return final.choices[0].message.content

    return message.content


def run_operations_ai(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Operations AI. "
                "Use Shopify tools for inventory, reorder forecasting, stock overview, and fulfillment operations. "
                "For 'what needs reordering', use forecast_all_reorders. "
                "For one specific product, use forecast_reorder. "
                "Never invent stock or order numbers."
            )
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=operations_tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = safe_tool_args(tool_call)
            days = args.get("days", 30)

            if tool_name == "forecast_reorder":
                result = forecast_reorder(args["item_name"])
            elif tool_name == "get_all_products":
                result = get_all_products()
            elif tool_name == "forecast_all_reorders":
                result = forecast_all_reorders()
            elif tool_name == "get_order_insights":
                result = get_order_insights(days)
            else:
                result = "Tool not found."

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                }
            )

        messages.append(STRICT_INSTRUCTION)

        final = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0
        )

        return final.choices[0].message.content

    return message.content


def run_finance_ai(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Finance AI for an e-commerce business. "
                "Use tools for real financial data. Never invent numbers.\n\n"
                "You can handle:\n"
                "- Revenue summaries\n"
                "- Revenue trends\n"
                "- Top products\n"
                "- Refund summaries\n"
                "- Customer insights\n"
                "- Order insights\n"
                "- Bookkeeping and journal entries\n"
                "- Weekly P&L\n"
                "- Cash flow dashboard\n"
                "- Profit forecasting\n"
                "- Refund and chargeback risk analysis\n"
                "- Creating pending refund approval requests\n\n"
                "Important refund rule:\n"
                "AI must NEVER approve or execute refunds by itself. "
                "AI can only create a pending approval for owner review. "
                "The owner must approve or reject from the dashboard.\n\n"
                "Never invent refund amounts, approval status, payment timelines, or order information."
            )
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=finance_tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = safe_tool_args(tool_call)
            days = args.get("days", 30)

            if tool_name == "get_revenue_summary":
                result = get_revenue_summary(days)
            elif tool_name == "get_top_products":
                result = get_top_products(days)
            elif tool_name == "get_refund_summary":
                result = get_refund_summary(days)
            elif tool_name == "get_revenue_trends":
                result = get_revenue_trends()
            elif tool_name == "get_customer_insights":
                result = get_customer_insights(days)
            elif tool_name == "get_order_insights":
                result = get_order_insights(days)
            elif tool_name == "categorize_shopify_transactions":
                result = categorize_shopify_transactions(days)
            elif tool_name == "analyze_refund_risk":
                result = analyze_refund_risk(args["order_id"])
            elif tool_name == "create_refund_approval":
                result = create_refund_approval(
                    args["order_id"],
                    args.get("reason", "Customer requested refund")
                )
            elif tool_name == "get_weekly_pnl_report":
                result = get_weekly_pnl_report()
            elif tool_name == "get_cash_flow_dashboard":
                result = get_cash_flow_dashboard(days)
            elif tool_name == "get_profit_forecast":
                result = get_profit_forecast(days)
            else:
                result = "Tool not found."

            if "not found" in result.lower():
                return result

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                }
            )

        messages.append(STRICT_INSTRUCTION)

        final = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0
        )

        return final.choices[0].message.content

    return message.content


def run_growth_ai(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Growth AI, an e-commerce growth strategist. "
                "Help the owner decide what products to add, how to price products, what bundles to create, "
                "what niches to explore, and how to increase sales.\n\n"
                "Important:\n"
                "- Do NOT call Shopify tools.\n"
                "- Use strategic business reasoning.\n"
                "- If the owner asks for tech product ideas, suggest practical high-margin e-commerce products.\n"
                "- Prefer accessories, consumables, bundles, and lightweight products over low-margin expensive products.\n"
                "- Give clear, actionable recommendations."
            )
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4
    )

    return response.choices[0].message.content


def run_supplier_ai(user_message, history=None):
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Supplier AI. "
                "Help create supplier emails, purchase order drafts, reorder messages, and supplier follow-ups. "
                "Do not actually send emails or place purchase orders. "
                "Always frame supplier actions as drafts for owner approval."
            )
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content


def run_executive_ai(user_message, history=None):
    finance_snapshot = get_revenue_summary(30)
    trends = get_revenue_trends()
    orders = get_order_insights(30)
    cash_flow = get_cash_flow_dashboard(30)
    profit = get_profit_forecast(30)
    inventory = forecast_all_reorders()

    prompt = f"""
You are Shiftora Executive AI.

Create a concise executive business briefing for the owner.

Use only the following real business data:

FINANCE SNAPSHOT:
{finance_snapshot}

REVENUE TRENDS:
{trends}

ORDER INSIGHTS:
{orders}

CASH FLOW:
{cash_flow}

PROFIT FORECAST:
{profit}

INVENTORY:
{inventory}

The owner asked:
{user_message}

Return:
1. Business health summary
2. Key numbers
3. Risks
4. Recommended actions
5. What to focus on today
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content


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
            "supplier_ai"
        ]
    }


@app.post("/chat/customer")
def chat_customer_endpoint(request: ChatRequest):
    agent_functions = {
        "customer_ai": lambda msg: run_customer_ai(msg, request.history),
    }

    return route_message(
        request.message,
        client,
        MODEL,
        agent_functions,
        request.history
    )


@app.post("/chat/owner")
def chat_owner_endpoint(
    request: ChatRequest,
    x_owner_password: str = Header(default="")
):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    agent_functions = {
        "customer_ai": lambda msg: run_customer_ai(msg, request.history),
        "operations_ai": lambda msg: run_operations_ai(msg, request.history),
        "finance_ai": lambda msg: run_finance_ai(msg, request.history),
        "growth_ai": lambda msg: run_growth_ai(msg, request.history),
        "executive_ai": lambda msg: run_executive_ai(msg, request.history),
        "supplier_ai": lambda msg: run_supplier_ai(msg, request.history),
        "marketing_ai": lambda msg: run_marketing_ai(msg, client, MODEL, request.history),
    }

    return route_message(
        request.message,
        client,
        MODEL,
        agent_functions,
        request.history
    )


@app.post("/customer-ai")
def customer_ai_endpoint(request: ChatRequest):
    return {
        "agent": "customer_ai",
        "response": run_customer_ai(request.message, request.history)
    }


@app.post("/operations-ai")
def operations_ai_endpoint(request: ChatRequest):
    return {
        "agent": "operations_ai",
        "response": run_operations_ai(request.message, request.history)
    }


@app.post("/finance-ai")
def finance_ai_endpoint(request: ChatRequest):
    return {
        "agent": "finance_ai",
        "response": run_finance_ai(request.message, request.history)
    }


@app.post("/growth-ai")
def growth_ai_endpoint(request: ChatRequest):
    return {
        "agent": "growth_ai",
        "response": run_growth_ai(request.message, request.history)
    }


@app.post("/executive-ai")
def executive_ai_endpoint(request: ChatRequest):
    return {
        "agent": "executive_ai",
        "response": run_executive_ai(request.message, request.history)
    }


@app.post("/supplier-ai")
def supplier_ai_endpoint(request: ChatRequest):
    return {
        "agent": "supplier_ai",
        "response": run_supplier_ai(request.message, request.history)
    }
@app.post("/marketing-ai")
def marketing_ai_endpoint(request: ChatRequest):
    return {
        "agent": "marketing_ai",
        "response": run_marketing_ai(
            request.message,
            client,
            MODEL,
            request.history
        )
    }



@app.post("/abandoned-carts/create")
def create_abandoned_cart_endpoint(
    request: AbandonedCartRequest,
    x_owner_password: str = Header(default="")
):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    create_abandoned_cart(
        request.cart_token,
        request.customer_name,
        request.email,
        request.phone,
        request.items,
        request.cart_value,
        request.checkout_url
    )

    return {
        "message": "Abandoned cart saved successfully.",
        "cart_token": request.cart_token
    }
@app.get("/approvals/all")
def list_all_approvals(x_owner_password: str = Header(default="")):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    approvals = get_all_approvals()

    return {
        "approvals": approvals
    }


@app.get("/abandoned-carts")
def list_abandoned_carts(x_owner_password: str = Header(default="")):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    carts = get_pending_abandoned_carts()

    return {
        "pending_abandoned_carts": carts
    }
@app.post("/abandoned-carts/{cart_token}/generate-drafts")
def generate_abandoned_cart_drafts(
    cart_token: str,
    x_owner_password: str = Header(default="")
):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    cart = get_abandoned_cart_by_token(cart_token)

    if not cart:
        raise HTTPException(status_code=404, detail="Abandoned cart not found")

    prompt = f"""
You are Brisq Marketing AI.

Create abandoned cart recovery drafts for this customer.

Customer:
{cart["customer_name"]}

Email:
{cart["email"]}

Phone:
{cart["phone"]}

Items:
{cart["items"]}

Cart value:
₹{cart["cart_value"]}

Checkout URL:
{cart["checkout_url"]}

Return exactly this format:

EMAIL:
<email subject + email body>

WHATSAPP:
<short WhatsApp message>

COUPON:
<suggested coupon or incentive>
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )

    ai_text = response.choices[0].message.content

    email_part = ai_text
    whatsapp_part = ai_text
    coupon_part = "No coupon suggested"

    if "EMAIL:" in ai_text and "WHATSAPP:" in ai_text:
        email_part = ai_text.split("WHATSAPP:")[0].replace("EMAIL:", "").strip()
        rest = ai_text.split("WHATSAPP:")[1]

        if "COUPON:" in rest:
            whatsapp_part = rest.split("COUPON:")[0].strip()
            coupon_part = rest.split("COUPON:")[1].strip()
        else:
            whatsapp_part = rest.strip()

    update_abandoned_cart_ai_messages(
        cart_token,
        email_part,
        whatsapp_part,
        coupon_part
    )

    create_approval(
        approval_type="abandoned_cart",
        reference_id=cart_token,
        title=f"Abandoned cart recovery for {cart['customer_name']}",
        description=f"Recovery message for cart worth ₹{cart['cart_value']}",
        payload={
            "cart_token": cart_token,
            "customer_name": cart["customer_name"],
            "email": cart["email"],
            "phone": cart["phone"],
            "items": cart["items"],
            "cart_value": cart["cart_value"],
            "checkout_url": cart["checkout_url"],
            "email_draft": email_part,
            "whatsapp_draft": whatsapp_part,
            "suggested_coupon": coupon_part,
            "action": "abandoned_cart_recovery_requires_owner_approval"
        }
    )

    return {
        "message": "AI recovery drafts generated, saved, and sent to Approval Center.",
        "cart_token": cart_token,
        "email_draft": email_part,
        "whatsapp_draft": whatsapp_part,
        "suggested_coupon": coupon_part
    }
# ---------------------------------------------------------------------------
# Approval Center — single source of truth for ALL approval types.
# approval_type values in use:
#   "refund"         — created by create_refund_approval() via finance_ai
#   "abandoned_cart" — created by /abandoned-carts/{token}/generate-drafts
# New approval types should use create_approval() from database.py and will
# automatically appear here without any additional endpoint changes.
# ---------------------------------------------------------------------------
@app.get("/approvals")
def list_approvals(x_owner_password: str = Header(default="")):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    approvals = get_pending_approvals()

    return {
        "pending_approvals": approvals
    }


@app.post("/approvals/{approval_id}/approve")
def approve_approval(
    approval_id: int,
    x_owner_password: str = Header(default="")
):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    approve_request(approval_id)

    return {
        "message": "Approval marked as approved.",
        "approval_id": approval_id
    }


@app.post("/approvals/{approval_id}/reject")
def reject_approval(
    approval_id: int,
    x_owner_password: str = Header(default="")
):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")

    reject_request(approval_id)

    return {
        "message": "Approval marked as rejected.",
        "approval_id": approval_id
    }