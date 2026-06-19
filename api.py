from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import httpx
import sqlite3
from groq import Groq
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
import os

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

# ── ChromaDB setup for RAG ──
embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
policy_collection = chroma_client.get_or_create_collection(
    name="store_policies",
    embedding_function=embedding_fn
)

def get_db_connection():
    return sqlite3.connect("store.db")

STRICT_INSTRUCTION = {
    "role": "system",
    "content": "IMPORTANT: Only use the exact data returned by the tool above. Do not invent, assume, or add any other warehouses, numbers, tracking numbers, or details that were not explicitly in the tool result."
}

# ── Tool functions ──
def get_order_status(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT item, status, delivery_date FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item, status, delivery = row
        return f"Order #{order_id}: {item} — Status: {status}, Expected delivery: {delivery}"
    return f"Order #{order_id} not found."

def check_refund(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT eligible, note FROM refunds WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        eligible, note = row
        status = "Eligible" if eligible == "Yes" else "Not eligible"
        return f"Refund status for Order #{order_id}: {status} — {note}"
    return f"No refund information for Order #{order_id}."

def check_inventory(item_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stock, warehouse FROM inventory WHERE item = ?", (item_name,))
    row = cursor.fetchone()
    conn.close()
    if row:
        stock, warehouse = row
        if stock > 0:
            return f"{item_name}: {stock} units in stock at {warehouse} warehouse."
        return f"{item_name}: OUT OF STOCK at {warehouse} warehouse."
    return f"No inventory data found for '{item_name}'."

def search_policies(query):
    results = policy_collection.query(
        query_texts=[query],
        n_results=2
    )
    if results["documents"] and results["documents"][0]:
        retrieved = "\n\n".join(results["documents"][0])
        return retrieved
    return "No relevant policy found."

# ── Tool definitions ──
support_tools = [
    {"type": "function", "function": {"name": "get_order_status", "description": "Look up the status and delivery date of a customer order", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "The order ID"}}, "required": ["order_id"]}}},
    {"type": "function", "function": {"name": "check_refund", "description": "Check if an order is eligible for a refund", "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "The order ID"}}, "required": ["order_id"]}}}
]

inventory_tools = [
    {"type": "function", "function": {"name": "check_inventory", "description": "Check stock levels and warehouse location for a product", "parameters": {"type": "object", "properties": {"item_name": {"type": "string", "description": "The exact product name"}}, "required": ["item_name"]}}}
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

# ── Agent functions ──
def run_support_agent(user_message):
    messages = [
        {"role": "system", "content": "You are a customer support agent. Use tools to look up real order data."},
        {"role": "user", "content": user_message}
    ]
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

def run_inventory_agent(user_message):
    messages = [
        {"role": "system", "content": "You are an inventory management agent. Use tools to check real stock data."},
        {"role": "user", "content": user_message}
    ]
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

def run_policy_agent(user_message):
    messages = [
        {"role": "system", "content": "You are a store policy assistant. Use the search_policies tool to find the relevant policy, then answer based only on what it returns."},
        {"role": "user", "content": user_message}
    ]
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

# ── Request schema ──
class ChatRequest(BaseModel):
    message: str

# ── API ENDPOINTS ──
@app.get("/")
def root():
    return {"message": "E-commerce Agent API is running. Use /support, /inventory, or /policy endpoints."}

@app.post("/support")
def support_endpoint(request: ChatRequest):
    answer = run_support_agent(request.message)
    return {"agent": "support", "response": answer}

@app.post("/inventory")
def inventory_endpoint(request: ChatRequest):
    answer = run_inventory_agent(request.message)
    return {"agent": "inventory", "response": answer}

@app.post("/policy")
def policy_endpoint(request: ChatRequest):
    answer = run_policy_agent(request.message)
    return {"agent": "policy", "response": answer}