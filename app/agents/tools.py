"""
app/agents/tools.py
-------------------
All LLM tool-schema lists used by agent functions.
Imported by the individual agent modules — keeps schema definitions
in one place and out of the agent logic files.
"""

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
                        "description": "The order number, for example 1001",
                    }
                },
                "required": ["order_id"],
            },
        },
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
                        "description": "The order number",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
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
                        "description": "The product name",
                    }
                },
                "required": ["item_name"],
            },
        },
    }
]

policy_tools = [
    {
        "type": "function",
        "function": {
            "name": "search_policies",
            "description": (
                "Search store policies for return, refund, shipping, "
                "cancellation, warranty, or damaged item rules"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The customer's policy question",
                    }
                },
                "required": ["query"],
            },
        },
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
                        "description": "The exact product name",
                    }
                },
                "required": ["item_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_all_products",
            "description": "Get all product names in the store",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "forecast_all_reorders",
            "description": "Get stockout and reorder forecast for all products",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
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
                        "description": "Number of days to look back",
                    }
                },
                "required": [],
            },
        },
    },
]

finance_tools = [
    {
        "type": "function",
        "function": {
            "name": "get_revenue_summary",
            "description": "Get total revenue, order count, and average order value",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_products",
            "description": "Get best-selling products by units and revenue",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_refund_summary",
            "description": "Get refund count, refund rate, and total refunded amount",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_revenue_trends",
            "description": "Compare revenue this week vs last week and this month vs last month",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_insights",
            "description": "Get new vs returning customers and top customers by spend",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_order_insights",
            "description": "Get pending orders, fulfillment time, and unfulfilled order value",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "categorize_shopify_transactions",
            "description": "Bookkeeping categories and accounting-style journal entries",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
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
                        "description": "The Shopify order number",
                    }
                },
                "required": ["order_id"],
            },
        },
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
                    "reason": {"type": "string"},
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weekly_pnl_report",
            "description": "Generate weekly profit and loss report",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cash_flow_dashboard",
            "description": "Generate cash flow dashboard",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_profit_forecast",
            "description": "Forecast revenue and profit based on recent sales",
            "parameters": {
                "type": "object",
                "properties": {"days": {"type": "integer"}},
                "required": [],
            },
        },
    },
]
