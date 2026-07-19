"""
app/agents/finance_ai.py
-------------------------
Finance agent.
Handles: revenue, P&L, bookkeeping, cash flow, refund risk, refund approvals.
"""

import json

from app.agents.tools import finance_tools
from app.config import MODEL
from app.deps import groq_client

from database import create_approval
from shopify_tools import (
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


def create_refund_approval(order_id: str, reason: str = "Customer requested refund") -> str:
    """
    Business logic for creating a pending refund approval.
    Called directly by the finance agent's tool dispatch.
    Writes to the DB-backed approval system (database.create_approval).
    """
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
            "action": "refund_requires_owner_approval",
        },
    )

    return (
        f"Refund approval request created for order #{order_id}.\n\n"
        f"{risk_report}\n\n"
        f"Important: No refund has been issued yet. "
        f"The owner must approve or reject this request from the approval queue."
    )


def run_finance_ai(user_message: str, history=None) -> str:
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
            ),
        }
    ]

    if history:
        messages.extend(history[-6:])

    messages.append({"role": "user", "content": user_message})

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=finance_tools,
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
                    args.get("reason", "Customer requested refund"),
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
