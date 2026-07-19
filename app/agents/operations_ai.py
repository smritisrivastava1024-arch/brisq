"""
app/agents/operations_ai.py
----------------------------
Operations agent.
Handles: inventory overview, reorder forecasting, fulfillment operations.
"""

import json

from app.agents.tools import operations_tools
from app.config import MODEL
from app.deps import groq_client

from shopify_tools import (
    forecast_reorder,
    get_all_products,
    forecast_all_reorders,
    get_order_insights,
)

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


async def run_operations_ai(user_message: str, history=None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Operations AI. "
                "Use Shopify tools for inventory, reorder forecasting, stock overview, and fulfillment operations. "
                "For 'what needs reordering', use forecast_all_reorders. "
                "For one specific product, use forecast_reorder. "
                "Never invent stock or order numbers."
            ),
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    response = await groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=operations_tools,
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
            days = args.get("days", 30)

            if tool_name == "forecast_reorder":
                result = await forecast_reorder(args["item_name"])
            elif tool_name == "get_all_products":
                result = await get_all_products()
            elif tool_name == "forecast_all_reorders":
                result = await forecast_all_reorders()
            elif tool_name == "get_order_insights":
                result = await get_order_insights(days)
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

        final = await groq_client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0,
        )
        return final.choices[0].message.content

    return message.content
