import re

with open('shopify_tools.py', 'r') as f:
    content = f.read()

# 1. Imports and global setup
content = re.sub(
    r'import requests',
    'import httpx\nimport asyncio',
    content
)

content = re.sub(
    r'HEADERS = \{\n    "X-Shopify-Access-Token": ACCESS_TOKEN,\n    "Content-Type": "application/json",\n\}',
    'HEADERS = {\n    "X-Shopify-Access-Token": ACCESS_TOKEN,\n    "Content-Type": "application/json",\n}\n\nshopify_semaphore = asyncio.Semaphore(10)',
    content
)

# 2. Rewrite _get
old_get = '''def _get(endpoint, params=None):
    """
    Simple GET helper for Shopify Admin API.
    """
    try:
        url = f"{BASE_URL}/{endpoint}"
        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception:
        return None'''

new_get = '''async def _get(endpoint, params=None):
    """
    Simple GET helper for Shopify Admin API.
    """
    import app.deps
    async with shopify_semaphore:
        # Shopify REST rate limit is 2 req/sec per store on standard plans
        try:
            url = f"{BASE_URL}/{endpoint}"
            if not app.deps.shared_http_client:
                return None
            response = await app.deps.shared_http_client.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception:
            return None'''

content = content.replace(old_get, new_get)

# 3. Add `async def` and `await` for all functions calling other async functions
funcs_to_async = [
    '_orders_between', '_get_order_by_number_or_id', '_get_product_stock', '_get_sales_velocity',
    'get_order_status', 'check_refund', 'check_inventory', 'get_all_products',
    'forecast_reorder', 'forecast_all_reorders', 'get_low_stock_products',
    'get_fastest_selling_products', 'get_order_insights', 'get_revenue_summary',
    'get_top_products', 'get_refund_summary', 'get_revenue_trends',
    'get_customer_insights', 'categorize_shopify_transactions', 'get_weekly_pnl_report',
    'get_cash_flow_dashboard', 'get_profit_forecast', 'analyze_refund_risk',
    'suggest_refund_decision', 'get_finance_overview', 'get_executive_snapshot',
    'get_abandoned_checkouts'
]

for func in funcs_to_async:
    content = re.sub(fr'^def {func}\(', f'async def {func}(', content, flags=re.MULTILINE)

calls_to_await = [
    '_get', '_orders_between', '_get_order_by_number_or_id', '_get_product_stock',
    '_get_sales_velocity', 'analyze_refund_risk', 'get_revenue_summary', 'get_revenue_trends',
    'get_refund_summary', 'categorize_shopify_transactions', 'get_cash_flow_dashboard',
    'get_profit_forecast', 'get_order_insights', 'forecast_all_reorders'
]

for call in calls_to_await:
    # Look for calls, e.g. `data = _get(` -> `data = await _get(`
    # Need to be careful to not replace the `def _get` definitions.
    # We can match `[^def ]call(` and inject await.
    content = re.sub(fr'(?<!def )(?<!async def ){call}\(', f'await {call}(', content)

with open('shopify_tools.py', 'w') as f:
    f.write(content)

print("shopify_tools.py refactored.")
