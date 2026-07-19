"""
app/agents/executive_ai.py
---------------------------
Executive briefing agent.
Pulls live data snapshots from multiple Shopify tools and synthesises
a CEO-style business briefing.
"""

from app.config import MODEL
from app.deps import groq_client

from shopify_tools import (
    get_revenue_summary,
    get_revenue_trends,
    get_order_insights,
    get_cash_flow_dashboard,
    get_profit_forecast,
    forecast_all_reorders,
)


def run_executive_ai(user_message: str, history=None) -> str:
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

    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return response.choices[0].message.content
