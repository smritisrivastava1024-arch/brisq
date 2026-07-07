from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import httpx
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import os

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
)

app = FastAPI(title="E-commerce Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

http_client = httpx.Client(headers={"User-Agent": "Mozilla/5.0"})
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"), http_client=http_client)
MODEL = "llama-3.3-70b-versatile"
OWNER_PASSWORD = os.getenv("OWNER_PASSWORD", "changeme123")

# ── ChromaDB for policy RAG (stays local, not Shopify) ──
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
    "content": "IMPORTANT: Only use the exact data returned by the tool above. Do not invent or assume any details not explicitly returned by the tool."
}


def search_policies(query):
    results = policy_collection.query(query_texts=[query], n_results=2)
    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])
    return "No relevant policy found."


# ── Tool definitions ──

support_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": "Look up the status and delivery date of a customer order by order number",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order number e.g. 1001"}},
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_refund",
            "description": "Check if an order is eligible for a refund",
            "parameters": {
                "type": "object",
                "properties": {"order_id": {"type": "string", "description": "The order number"}},
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
                "properties": {"item_name": {"type": "string", "description": "The product name"}},
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
                "properties": {"query": {"type": "string", "description": "The customer's policy question"}},
                "required": ["query"]
            }
        }
    }
]

forecasting_tools = [
    {
        "type": "function",
        "function": {
            "name": "forecast_reorder",
            "description": "Forecast when ONE specific product will run out of stock. Use only when user names a specific product.",
            "parameters": {
                "type": "object",
                "properties": {"item_name": {"type": "string", "description": "The exact product name"}},
                "required": ["item_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_products",
            "description": "Get the list of all real product names in the store. Use this if unsure what products exist.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_all_reorders",
            "description": "Get stockout/reorder forecast for ALL products at once. Use for 'what needs reordering', 'stock overview', or 'fastest sellers'.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]


# ── Agent functions ──

def run_support_agent(user_message, history=None):
    messages = [
        {"role": "system", "content": (
            "You are a customer support agent. Use tools to look up real order data. "
            "IMPORTANT: Only call check_refund if the customer explicitly asks about "
            "a refund or return. If they just ask for order status or say an order number, "
            "only call get_order_status — do NOT call check_refund unless they ask for it. "
            "Use the conversation history to understand context — if the customer says "
            "'my order' or 'that order', look at previous messages to find the order number."
        )},
    ]
    if history:
        messages.extend(history[-6:])  # last 3 exchanges (6 messages)
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=support_tools, tool_choice="auto")
    message = response.choices[0].message

    if message.tool_calls:
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            if tool_name == "get_order_status":
                result = get_order_status(tool_args["order_id"])
            elif tool_name == "check_refund":
                result = check_refund(tool_args["order_id"])
            else:
                result = "Tool not found"
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        messages.append(STRICT_INSTRUCTION)
        final = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        return final.choices[0].message.content

    return message.content


def run_inventory_agent(user_message, history=None):
    messages = [
        {"role": "system", "content": (
            "You are an inventory agent. Use tools to check real stock data. "
            "Never invent stock numbers. Use conversation history for context."
        )},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=inventory_tools, tool_choice="auto")
    message = response.choices[0].message

    if message.tool_calls:
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        for tool_call in message.tool_calls:
            tool_args = json.loads(tool_call.function.arguments)
            result = check_inventory(tool_args["item_name"])
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        messages.append(STRICT_INSTRUCTION)
        final = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        return final.choices[0].message.content

    return message.content


def run_policy_agent(user_message, history=None):
    messages = [
        {"role": "system", "content": (
            "You are a store policy assistant. Use the search_policies tool to find "
            "relevant policy, then answer based only on what it returns. "
            "Use conversation history for context."
        )},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=policy_tools, tool_choice="auto")
    message = response.choices[0].message

    if message.tool_calls:
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        for tool_call in message.tool_calls:
            tool_args = json.loads(tool_call.function.arguments)
            result = search_policies(tool_args["query"])
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        messages.append(STRICT_INSTRUCTION)
        final = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        return final.choices[0].message.content

    return message.content


def run_forecasting_agent(user_message, history=None):
    messages = [
        {"role": "system", "content": (
            "You are an inventory forecasting agent. "
            "For ONE specific product, use forecast_reorder. "
            "For general questions like 'what needs reordering' or 'stock overview', use forecast_all_reorders. "
            "If unsure what products exist, call get_all_products first. "
            "Never invent numbers not returned by a tool. "
            "Use conversation history for context."
        )},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=forecasting_tools, tool_choice="auto")
    message = response.choices[0].message

    if message.tool_calls:
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            if tool_name == "forecast_reorder":
                result = forecast_reorder(tool_args["item_name"])
            elif tool_name == "get_all_products":
                result = get_all_products()
            elif tool_name == "forecast_all_reorders":
                result = forecast_all_reorders()
            else:
                result = "Tool not found"
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        messages.append(STRICT_INSTRUCTION)
        final = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        return final.choices[0].message.content

    return message.content


finance_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_revenue_summary",
            "description": "Get total revenue, order count and average order value for the last N days",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Number of days to look back (default 7)"}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_products",
            "description": "Get the best selling products by units sold and revenue for the last N days",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Number of days to look back (default 30)"}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_refund_summary",
            "description": "Get total refunds issued and refund rate for the last N days",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Number of days to look back (default 30)"}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_revenue_trends",
            "description": "Compare revenue this week vs last week and this month vs last month to show growth or decline trends",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_insights",
            "description": "Get new vs returning customer counts and top customers by spend for the last N days",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Number of days to look back (default 30)"}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_insights",
            "description": "Get pending orders count, average fulfillment time, and unfulfilled order value for the last N days",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer", "description": "Number of days to look back (default 30)"}},
                "required": []
            }
        }
    }
]


def run_finance_agent(user_message, history=None):
    messages = [
        {"role": "system", "content": (
            "You are a finance and reporting agent for an e-commerce store. "
            "Use tools to pull real sales data from Shopify and give clear, "
            "actionable financial summaries. Never invent numbers. "
            "Use these tools based on what the user asks:\n"
            "- get_revenue_summary: total revenue, order count, avg order value\n"
            "- get_top_products: best selling products by units and revenue\n"
            "- get_refund_summary: refund count, rate, total refunded\n"
            "- get_revenue_trends: this week vs last week, this month vs last month\n"
            "- get_customer_insights: new vs returning customers, top spenders\n"
            "- get_order_insights: pending orders, fulfillment time, at-risk revenue\n"
            "For a 'full summary' or 'overview', call ALL six tools."
        )},
    ]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model=MODEL, messages=messages, tools=finance_tools, tool_choice="auto")
    message = response.choices[0].message

    if message.tool_calls:
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            days = tool_args.get("days", 30)
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
            else:
                result = "Tool not found"
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})
        messages.append(STRICT_INSTRUCTION)
        final = client.chat.completions.create(model=MODEL, messages=messages, temperature=0)
        return final.choices[0].message.content

    return message.content


# ── Request schema ──

class ChatRequest(BaseModel):
    message: str
    history: list = []  # list of {"role": "user"/"assistant", "content": "..."}


# ── API Endpoints ──

@app.get("/")
def root():
    return {
        "message": "E-commerce Agent API running.",
        "customer_chat": "/chat/customer",
        "owner_chat": "/chat/owner (requires X-Owner-Password header)",
        "individual_agents": ["/support", "/inventory", "/policy", "/forecast"]
    }


@app.post("/support")
def support_endpoint(request: ChatRequest):
    return {"agent": "support", "response": run_support_agent(request.message)}


@app.post("/inventory")
def inventory_endpoint(request: ChatRequest):
    return {"agent": "inventory", "response": run_inventory_agent(request.message)}


@app.post("/policy")
def policy_endpoint(request: ChatRequest):
    return {"agent": "policy", "response": run_policy_agent(request.message)}


@app.post("/forecast")
def forecast_endpoint(request: ChatRequest):
    return {"agent": "forecasting", "response": run_forecasting_agent(request.message)}


@app.post("/finance")
def finance_endpoint(request: ChatRequest):
    return {"agent": "finance", "response": run_finance_agent(request.message)}


@app.post("/chat/customer")
def chat_customer_endpoint(request: ChatRequest):
    agent_functions = {
        "support": lambda msg: run_support_agent(msg, request.history),
        "inventory": lambda msg: run_inventory_agent(msg, request.history),
        "policy": lambda msg: run_policy_agent(msg, request.history),
    }
    result = route_message(request.message, client, MODEL, agent_functions)
    return result


@app.post("/chat/owner")
def chat_owner_endpoint(request: ChatRequest, x_owner_password: str = Header(default="")):
    if x_owner_password != OWNER_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid owner password")
    agent_functions = {
        "support": lambda msg: run_support_agent(msg, request.history),
        "inventory": lambda msg: run_inventory_agent(msg, request.history),
        "policy": lambda msg: run_policy_agent(msg, request.history),
        "forecasting": lambda msg: run_forecasting_agent(msg, request.history),
        "finance": lambda msg: run_finance_agent(msg, request.history),
    }
    result = route_message(request.message, client, MODEL, agent_functions)
    return result