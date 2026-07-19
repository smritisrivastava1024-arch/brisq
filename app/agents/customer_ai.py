"""
app/agents/customer_ai.py
--------------------------
Customer-facing support agent.
Handles: order status, refund eligibility, inventory lookups, store policy queries.
"""

import json

from app.agents.tools import support_tools, inventory_tools, policy_tools
from app.config import MODEL
from app.deps import groq_client, policy_collection

from shopify_tools import get_order_status, check_refund, check_inventory

STRICT_INSTRUCTION = {
    "role": "system",
    "content": (
        "IMPORTANT: Only use the exact data returned by the tool above. "
        "Do not invent or assume any details not explicitly returned by the tool."
    ),
}


def _safe_tool_args(tool_call) -> dict:
    try:
        return json.loads(tool_call.function.arguments or "{}") or {}
    except Exception:
        return {}


def _search_policies(query: str) -> str:
    results = policy_collection.query(query_texts=[query], n_results=2)
    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])
    return "No relevant policy found."


def run_customer_ai(user_message: str, history=None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Customer AI. "
                "Help customers with order status, product availability, refunds, returns, shipping, and store policies. "
                "Use tools for real order, inventory, and policy data. "
                "Never invent order details, refund status, delivery dates, or policy terms. "
                "Do not create owner refund approvals here. Customer AI can only check eligibility or explain policy."
            ),
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    tools = support_tools + inventory_tools + policy_tools

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": message.tool_calls,
            }
        )

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            args = _safe_tool_args(tool_call)

            if tool_name == "get_order_status":
                result = get_order_status(args["order_id"])
            elif tool_name == "check_refund":
                result = check_refund(args["order_id"])
            elif tool_name == "check_inventory":
                result = check_inventory(args["item_name"])
            elif tool_name == "search_policies":
                result = _search_policies(args["query"])
            else:
                result = "Tool not found."

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                }
            )

        messages.append(STRICT_INSTRUCTION)

        final = groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
        )
        return final.choices[0].message.content

    return message.content
