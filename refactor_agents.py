import os
import re

agent_files = [
    'app/agents/customer_ai.py',
    'app/agents/operations_ai.py',
    'app/agents/finance_ai.py',
    'app/agents/growth_ai.py',
    'app/agents/executive_ai.py',
    'app/agents/supplier_ai.py',
    'app/agents/marketing_ai.py',
]

shopify_tools_list = [
    'get_order_status', 'check_refund', 'check_inventory', 'get_all_products',
    'forecast_reorder', 'forecast_all_reorders', 'get_low_stock_products',
    'get_fastest_selling_products', 'get_order_insights', 'get_revenue_summary',
    'get_top_products', 'get_refund_summary', 'get_revenue_trends',
    'get_customer_insights', 'categorize_shopify_transactions', 'get_weekly_pnl_report',
    'get_cash_flow_dashboard', 'get_profit_forecast', 'analyze_refund_risk',
    'suggest_refund_decision', 'get_finance_overview', 'get_executive_snapshot',
    'get_abandoned_checkouts'
]

for file_path in agent_files:
    with open(file_path, 'r') as f:
        content = f.read()

    # 1. async defs
    funcs = ['run_customer_ai', 'run_operations_ai', 'run_finance_ai', 
             'run_growth_ai', 'run_executive_ai', 'run_supplier_ai', 'run_marketing_ai',
             'create_refund_approval']
    for func in funcs:
        content = re.sub(fr'^def {func}\(', f'async def {func}(', content, flags=re.MULTILINE)

    # 2. groq client calls
    content = content.replace('groq_client.chat.completions.create', 'await groq_client.chat.completions.create')
    content = content.replace('_client.chat.completions.create', 'await _client.chat.completions.create')

    # 3. await shopify tools
    for tool in shopify_tools_list + ['create_refund_approval']:
        content = re.sub(fr'(?<!def )(?<!async def ){tool}\(', f'await {tool}(', content)

    with open(file_path, 'w') as f:
        f.write(content)

print("Agents refactored.")
