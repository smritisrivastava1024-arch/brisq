"""
shopify_tools.py
----------------
Shopify tool functions for Shiftora.

Includes:
- Shopify API helpers
- Order status
- Refund eligibility
- Inventory lookup
- Product listing
"""

import os
import httpx
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv


load_dotenv()

STORE_URL = os.getenv("SHOPIFY_STORE_URL")
ACCESS_TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
API_VERSION = "2024-01"

BASE_URL = f"https://{STORE_URL}/admin/api/{API_VERSION}"

HEADERS = {
    "X-Shopify-Access-Token": ACCESS_TOKEN,
    "Content-Type": "application/json",
}

shopify_semaphore = asyncio.Semaphore(10)


# -------------------------------------------------------------------
# Helper Functions
# -------------------------------------------------------------------

async def _get(endpoint, params=None):
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
            return None


def _safe_float(value):
    """
    Safely convert values to float.
    """
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _money(value):
    """
    Format INR currency.
    """
    return f"₹{value:,.2f}"


async def _orders_between(start, end=None):
    """
    Fetch Shopify orders between start and optional end datetime.
    """
    params = {
        "status": "any",
        "created_at_min": start.strftime("%Y-%m-%dT00:00:00Z"),
        "limit": 250,
        "fields": (
            "id,name,total_price,total_tax,total_discounts,"
            "total_shipping_price_set,financial_status,fulfillment_status,"
            "created_at,updated_at,refunds,customer,line_items"
        )
    }

    if end:
        params["created_at_max"] = end.strftime("%Y-%m-%dT23:59:59Z")

    data = await _get("orders.json", params=params)

    if not data or not data.get("orders"):
        return []

    return data["orders"]


def _paid_orders(orders):
    """
    Orders that count as paid revenue.
    """
    return [
        order for order in orders
        if order.get("financial_status") in [
            "paid",
            "partially_paid",
            "partially_refunded"
        ]
    ]


def _refunded_orders(orders):
    """
    Orders with refund activity.
    """
    return [
        order for order in orders
        if order.get("financial_status") in [
            "refunded",
            "partially_refunded"
        ]
    ]


def _shipping_amount(order):
    """
    Extract shipping amount from Shopify nested money object.
    """
    shipping_set = order.get("total_shipping_price_set") or {}
    shop_money = shipping_set.get("shop_money") or {}
    return _safe_float(shop_money.get("amount"))


async def _get_order_by_number_or_id(order_id):
    """
    Find order by Shopify order number like 1001 or by raw Shopify order ID.
    """
    data = await _get("orders.json", params={
        "name": f"#{order_id}",
        "status": "any",
        "fields": (
            "id,name,total_price,total_tax,total_discounts,"
            "total_shipping_price_set,financial_status,fulfillment_status,"
            "created_at,updated_at,refunds,customer,line_items,"
            "estimated_delivery_at"
        )
    })

    if data and data.get("orders"):
        return data["orders"][0]

    data = await _get(f"orders/{order_id}.json")

    if data and "order" in data:
        return data["order"]

    return None


# -------------------------------------------------------------------
# Customer Support Tools
# -------------------------------------------------------------------

async def get_order_status(order_id):
    """
    Look up real Shopify order status.
    """
    order = await _get_order_by_number_or_id(order_id)

    if not order:
        return f"Order #{order_id} not found."

    name = order.get("name", f"#{order_id}")

    financial = (
        order.get("financial_status", "unknown")
        .replace("_", " ")
        .title()
    )

    fulfillment = order.get("fulfillment_status") or "unfulfilled"
    fulfillment = fulfillment.replace("_", " ").title()

    items = order.get("line_items", [])
    item_names = (
        ", ".join(item.get("title", "Unknown") for item in items)
        if items else "Unknown item"
    )

    delivery = order.get("estimated_delivery_at")

    if delivery:
        delivery_str = delivery[:10]
    else:
        created = order.get("created_at", "")

        if created:
            created_date = datetime.fromisoformat(created[:10])
            delivery_str = (
                created_date + timedelta(days=7)
            ).strftime("%Y-%m-%d")
        else:
            delivery_str = "not available"

    return (
        f"Order {name}: {item_names}.\n"
        f"Payment: {financial}.\n"
        f"Fulfillment: {fulfillment}.\n"
        f"Estimated delivery: {delivery_str}."
    )


async def check_refund(order_id):
    """
    Check basic refund eligibility.
    This does not create or approve a refund.
    """
    order = await _get_order_by_number_or_id(order_id)

    if not order:
        return f"Order #{order_id} not found."

    name = order.get("name", f"#{order_id}")
    financial = order.get("financial_status", "")
    refunds = order.get("refunds", [])

    if refunds:
        return f"Order {name}: A refund has already been processed for this order."

    if financial in ["paid", "partially_paid"]:
        created = order.get("created_at", "")

        if created:
            created_date = datetime.fromisoformat(created[:10])
            days_since = (datetime.now() - created_date).days

            if days_since <= 30:
                return (
                    f"Order {name}: Eligible for refund review. "
                    f"The order is within the 30-day return window."
                )

            return (
                f"Order {name}: Not eligible under the standard policy. "
                f"The order is outside the 30-day return window."
            )

        return f"Order {name}: Likely eligible for refund review."

    if financial == "refunded":
        return f"Order {name}: This order has already been fully refunded."

    return (
        f"Order {name}: Not eligible for refund based on payment status: "
        f"{financial}."
    )


# -------------------------------------------------------------------
# Inventory Tools
# -------------------------------------------------------------------

async def check_inventory(item_name):
    """
    Search Shopify products by name and return stock levels.
    """
    data = await _get("products.json", params={
        "title": item_name,
        "fields": "id,title,variants,status"
    })

    if not data or not data.get("products"):
        return f"No product found matching '{item_name}'."

    product = data["products"][0]
    title = product["title"]
    variants = product.get("variants", [])

    if not variants:
        return f"{title}: No stock data available."

    total_stock = 0
    details = []

    for variant in variants:
        qty = variant.get("inventory_quantity", 0)
        total_stock += qty

        if qty > 0:
            details.append(
                f"{variant.get('title', 'Default')} ({qty} units)"
            )

    if total_stock <= 0:
        return f"{title}: OUT OF STOCK across all variants."

    stock_detail = ", ".join(details) if details else f"{total_stock} units"

    return f"{title}: In stock — {stock_detail}."


async def get_all_products():
    """
    Return all active product names from Shopify.
    """
    data = await _get("products.json", params={
        "fields": "title,status",
        "status": "active",
        "limit": 250
    })

    if not data or not data.get("products"):
        return "No products found in your Shopify store."

    names = [product["title"] for product in data["products"]]

    return "Products in your store: " + ", ".join(names)
# -------------------------------------------------------------------
# Forecasting / Operations Tools
# -------------------------------------------------------------------

async def _get_product_stock(product_title):
    """
    Get current total stock for a product.
    """
    data = await _get("products.json", params={
        "title": product_title,
        "fields": "title,variants"
    })

    if not data or not data.get("products"):
        return None, None

    product = data["products"][0]
    title = product["title"]

    total_stock = sum(
        variant.get("inventory_quantity", 0)
        for variant in product.get("variants", [])
    )

    return title, total_stock


async def _get_sales_velocity(product_title, days=30):
    """
    Estimate average daily sales for a product from recent orders.
    """
    start = datetime.now() - timedelta(days=days)
    orders = await _orders_between(start)

    total_sold = 0

    for order in orders:
        for item in order.get("line_items", []):
            item_title = item.get("title", "")

            if product_title.lower() in item_title.lower():
                total_sold += item.get("quantity", 0)

    if days <= 0:
        return 0

    return total_sold / days


async def forecast_reorder(item_name):
    """
    Forecast stockout for one product.
    """
    title, stock = await _get_product_stock(item_name)

    if title is None:
        return f"No product found matching '{item_name}'."

    avg_daily_sales = await _get_sales_velocity(title, days=30)

    if avg_daily_sales <= 0:
        return (
            f"{title}: {stock} units in stock.\n"
            f"No recent sales data found, so demand cannot be forecast reliably."
        )

    days_until_stockout = stock / avg_daily_sales
    suggested_reorder = round(avg_daily_sales * 30)

    if days_until_stockout <= 14:
        return (
            f"{title}: {stock} units in stock.\n"
            f"Average sales velocity: ~{avg_daily_sales:.1f} units/day.\n"
            f"Estimated stockout: ~{days_until_stockout:.0f} days.\n"
            f"Recommendation: Reorder ~{suggested_reorder} units soon."
        )

    return (
        f"{title}: {stock} units in stock.\n"
        f"Average sales velocity: ~{avg_daily_sales:.1f} units/day.\n"
        f"Estimated stock duration: ~{days_until_stockout:.0f} days.\n"
        f"Recommendation: No reorder needed yet."
    )


async def forecast_all_reorders():
    """
    Forecast reorder needs for all active products.
    """
    data = await _get("products.json", params={
        "fields": "title,variants",
        "status": "active",
        "limit": 250
    })

    if not data or not data.get("products"):
        return "No products found in your Shopify store."

    lines = []
    reorder_needed = []

    for product in data["products"]:
        title = product["title"]

        stock = sum(
            variant.get("inventory_quantity", 0)
            for variant in product.get("variants", [])
        )

        avg_daily_sales = await _get_sales_velocity(title, days=30)

        if avg_daily_sales <= 0:
            lines.append(
                f"{title}: {stock} units in stock, no recent sales velocity."
            )
            continue

        days_until_stockout = stock / avg_daily_sales
        suggested_reorder = round(avg_daily_sales * 30)

        if days_until_stockout <= 14:
            reorder_needed.append(title)
            lines.append(
                f"{title}: {stock} units, ~{avg_daily_sales:.1f}/day, "
                f"stockout in ~{days_until_stockout:.0f} days — "
                f"REORDER ~{suggested_reorder} units."
            )
        else:
            lines.append(
                f"{title}: {stock} units, ~{avg_daily_sales:.1f}/day, "
                f"lasts ~{days_until_stockout:.0f} days — OK."
            )

    if not lines:
        return "No inventory data available."

    summary = "\n".join(lines)

    if reorder_needed:
        return (
            f"Reorder Forecast\n\n"
            f"Products needing reorder: {', '.join(reorder_needed)}\n\n"
            f"{summary}"
        )

    return (
        f"Reorder Forecast\n\n"
        f"No products need immediate reordering based on current stock and recent sales velocity.\n\n"
        f"{summary}"
    )


async def get_low_stock_products(threshold=10):
    """
    Return products with total stock below threshold.
    """
    data = await _get("products.json", params={
        "fields": "title,variants",
        "status": "active",
        "limit": 250
    })

    if not data or not data.get("products"):
        return "No products found in your Shopify store."

    low_stock = []

    for product in data["products"]:
        title = product["title"]

        stock = sum(
            variant.get("inventory_quantity", 0)
            for variant in product.get("variants", [])
        )

        if stock <= threshold:
            low_stock.append((title, stock))

    if not low_stock:
        return f"No products are below the low-stock threshold of {threshold} units."

    lines = [f"Low Stock Products — Threshold: {threshold} units"]

    for title, stock in low_stock:
        lines.append(f"- {title}: {stock} units")

    return "\n".join(lines)


async def get_fastest_selling_products(days=30):
    """
    Return fastest-selling products based on units sold in recent orders.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    if not orders:
        return f"No order data found in the last {days} days."

    product_sales = {}

    for order in orders:
        for item in order.get("line_items", []):
            title = item.get("title", "Unknown")
            qty = item.get("quantity", 0)

            if title not in product_sales:
                product_sales[title] = 0

            product_sales[title] += qty

    if not product_sales:
        return f"No product sales found in the last {days} days."

    sorted_products = sorted(
        product_sales.items(),
        key=lambda item: item[1],
        reverse=True
    )

    lines = [f"Fastest Selling Products — Last {days} days"]

    for index, (title, units) in enumerate(sorted_products[:5], 1):
        avg_daily = units / days if days else 0
        lines.append(
            f"{index}. {title}: {units} units sold "
            f"(~{avg_daily:.1f}/day)"
        )

    return "\n".join(lines)


async def get_order_insights(days=30):
    """
    Returns fulfillment and pending order insights.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    if not orders:
        return f"No order data found in the last {days} days."

    fulfilled = [
        order for order in orders
        if order.get("fulfillment_status") == "fulfilled"
    ]

    unfulfilled = [
        order for order in orders
        if not order.get("fulfillment_status")
    ]

    pending_value = sum(
        _safe_float(order.get("total_price"))
        for order in unfulfilled
    )

    fulfillment_times = []

    for order in fulfilled:
        created = order.get("created_at")
        updated = order.get("updated_at")

        if created and updated:
            try:
                created_dt = datetime.fromisoformat(created[:19])
                updated_dt = datetime.fromisoformat(updated[:19])
                days_to_fulfill = (updated_dt - created_dt).days

                if days_to_fulfill >= 0:
                    fulfillment_times.append(days_to_fulfill)

            except Exception:
                pass

    if fulfillment_times:
        avg_fulfillment = (
            f"{sum(fulfillment_times) / len(fulfillment_times):.1f} days"
        )
    else:
        avg_fulfillment = "not enough data"

    return (
        f"Order Insights — Last {days} days\n\n"
        f"Total orders: {len(orders)}\n"
        f"Fulfilled: {len(fulfilled)}\n"
        f"Unfulfilled / pending: {len(unfulfilled)}\n"
        f"Pending revenue at risk: {_money(pending_value)}\n"
        f"Average fulfillment time: {avg_fulfillment}"
    )
# -------------------------------------------------------------------
# Finance Tools
# -------------------------------------------------------------------

async def get_revenue_summary(days=7):
    """
    Revenue, paid order count, and average order value.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))
    paid_orders = _paid_orders(orders)

    if not paid_orders:
        return f"No paid orders found in the last {days} days."

    total_revenue = sum(
        _safe_float(order.get("total_price"))
        for order in paid_orders
    )

    order_count = len(paid_orders)

    average_order_value = (
        total_revenue / order_count
        if order_count > 0 else 0
    )

    return (
        f"Revenue Summary — Last {days} days\n\n"
        f"Paid orders: {order_count}\n"
        f"Total revenue: {_money(total_revenue)}\n"
        f"Average order value: {_money(average_order_value)}"
    )


async def get_top_products(days=30):
    """
    Best-selling products by units and revenue.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))
    paid_orders = _paid_orders(orders)

    if not paid_orders:
        return f"No sales data found in the last {days} days."

    product_sales = {}

    for order in paid_orders:
        for item in order.get("line_items", []):
            title = item.get("title", "Unknown")
            quantity = item.get("quantity", 0)
            price = _safe_float(item.get("price"))

            revenue = price * quantity

            if title not in product_sales:
                product_sales[title] = {
                    "units": 0,
                    "revenue": 0
                }

            product_sales[title]["units"] += quantity
            product_sales[title]["revenue"] += revenue

    if not product_sales:
        return "No product sales data found."

    sorted_products = sorted(
        product_sales.items(),
        key=lambda item: item[1]["units"],
        reverse=True
    )

    lines = [f"Top Products — Last {days} days"]

    for index, (title, data) in enumerate(sorted_products[:5], 1):
        lines.append(
            f"{index}. {title} — "
            f"{data['units']} units sold, "
            f"{_money(data['revenue'])} revenue"
        )

    return "\n".join(lines)


async def get_refund_summary(days=30):
    """
    Refund count, refund rate, and refunded amount.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    if not orders:
        return f"No orders found in the last {days} days."

    refunded_orders = _refunded_orders(orders)

    total_orders = len(orders)
    refund_count = len(refunded_orders)

    refund_rate = (
        refund_count / total_orders * 100
        if total_orders > 0 else 0
    )

    total_refunded = sum(
        _safe_float(order.get("total_price"))
        for order in refunded_orders
    )

    return (
        f"Refund Summary — Last {days} days\n\n"
        f"Total orders: {total_orders}\n"
        f"Refunded orders: {refund_count}\n"
        f"Refund rate: {refund_rate:.1f}%\n"
        f"Total refunded: {_money(total_refunded)}"
    )


async def get_revenue_trends():
    """
    Compare this week vs last week and this month vs last month.
    """
    now = datetime.now()

    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    last_week_end = now - timedelta(days=7)

    this_week_orders = _paid_orders(
        await _orders_between(this_week_start, now)
    )

    last_week_orders = _paid_orders(
        await _orders_between(last_week_start, last_week_end)
    )

    this_month_start = now.replace(day=1)

    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month_orders = _paid_orders(
        await _orders_between(this_month_start, now)
    )

    last_month_orders = _paid_orders(
        await _orders_between(last_month_start, last_month_end)
    )

    def calculate_revenue(orders):
        return sum(
            _safe_float(order.get("total_price"))
            for order in orders
        )

    def trend_text(current, previous):
        if previous == 0:
            return "No previous period revenue data to compare."

        change = ((current - previous) / previous) * 100
        direction = "up" if change >= 0 else "down"

        return (
            f"Revenue is {direction} {abs(change):.1f}% "
            f"compared to the previous period."
        )

    this_week_revenue = calculate_revenue(this_week_orders)
    last_week_revenue = calculate_revenue(last_week_orders)

    this_month_revenue = calculate_revenue(this_month_orders)
    last_month_revenue = calculate_revenue(last_month_orders)

    return (
        f"Revenue Trends\n\n"
        f"This week: {_money(this_week_revenue)} "
        f"from {len(this_week_orders)} paid orders\n"
        f"Last week: {_money(last_week_revenue)} "
        f"from {len(last_week_orders)} paid orders\n"
        f"{trend_text(this_week_revenue, last_week_revenue)}\n\n"
        f"This month: {_money(this_month_revenue)} "
        f"from {len(this_month_orders)} paid orders\n"
        f"Last month: {_money(last_month_revenue)} "
        f"from {len(last_month_orders)} paid orders\n"
        f"{trend_text(this_month_revenue, last_month_revenue)}"
    )


async def get_customer_insights(days=30):
    """
    New vs returning customers and top customers by spend.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))
    paid_orders = _paid_orders(orders)

    if not paid_orders:
        return f"No customer data found in the last {days} days."

    customer_spend = {}
    new_customers = 0
    returning_customers = 0

    for order in paid_orders:
        customer = order.get("customer") or {}

        if not customer:
            continue

        customer_id = customer.get("id")
        first = customer.get("first_name", "")
        last = customer.get("last_name", "")

        name = f"{first} {last}".strip() or "Unknown Customer"
        order_count = customer.get("orders_count", 1)
        spend = _safe_float(order.get("total_price"))

        if order_count <= 1:
            new_customers += 1
        else:
            returning_customers += 1

        if customer_id not in customer_spend:
            customer_spend[customer_id] = {
                "name": name,
                "spend": 0
            }

        customer_spend[customer_id]["spend"] += spend

    top_customers = sorted(
        customer_spend.values(),
        key=lambda item: item["spend"],
        reverse=True
    )[:3]

    lines = [
        f"Customer Insights — Last {days} days",
        "",
        f"New customers: {new_customers}",
        f"Returning customers: {returning_customers}",
        "",
        "Top customers by spend:"
    ]

    if top_customers:
        for index, customer in enumerate(top_customers, 1):
            lines.append(
                f"{index}. {customer['name']} — "
                f"{_money(customer['spend'])}"
            )
    else:
        lines.append("No customer spend data available.")

    return "\n".join(lines)


async def categorize_shopify_transactions(days=30):
    """
    Bookkeeping report with categories and journal entries.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    if not orders:
        return f"No transactions found in the last {days} days."

    paid_orders = _paid_orders(orders)
    refunded_orders = _refunded_orders(orders)

    revenue = sum(
        _safe_float(order.get("total_price"))
        for order in paid_orders
    )

    taxes = sum(
        _safe_float(order.get("total_tax"))
        for order in paid_orders
    )

    discounts = sum(
        _safe_float(order.get("total_discounts"))
        for order in paid_orders
    )

    shipping = sum(
        _shipping_amount(order)
        for order in paid_orders
    )

    refunds = sum(
        _safe_float(order.get("total_price"))
        for order in refunded_orders
    )

    net_revenue = revenue - refunds

    return (
        f"Bookkeeping Report — Last {days} days\n\n"
        f"Summary:\n"
        f"- Paid orders: {len(paid_orders)}\n"
        f"- Refunded orders: {len(refunded_orders)}\n\n"
        f"Categories:\n"
        f"- Sales Revenue: {_money(revenue)}\n"
        f"- Refunds: {_money(refunds)}\n"
        f"- Taxes Collected: {_money(taxes)}\n"
        f"- Shipping Collected: {_money(shipping)}\n"
        f"- Discounts Given: {_money(discounts)}\n\n"
        f"Net Revenue After Refunds: {_money(net_revenue)}\n\n"
        f"Suggested Journal Entries:\n\n"
        f"1. Sales Entry\n"
        f"   Dr Cash / Shopify Payments: {_money(revenue)}\n"
        f"   Cr Sales Revenue: {_money(revenue)}\n\n"
        f"2. Tax Liability Entry\n"
        f"   Dr Cash / Shopify Payments: {_money(taxes)}\n"
        f"   Cr Tax Payable: {_money(taxes)}\n\n"
        f"3. Shipping Income Entry\n"
        f"   Dr Cash / Shopify Payments: {_money(shipping)}\n"
        f"   Cr Shipping Income: {_money(shipping)}\n\n"
        f"4. Discount Entry\n"
        f"   Dr Sales Discount Expense: {_money(discounts)}\n"
        f"   Cr Sales Revenue Adjustment: {_money(discounts)}\n\n"
        f"5. Refund Entry\n"
        f"   Dr Refund Expense: {_money(refunds)}\n"
        f"   Cr Cash / Shopify Payments: {_money(refunds)}"
    )


async def get_weekly_pnl_report():
    """
    Weekly profit and loss report.
    COGS and fees are estimates until actual cost data is connected.
    """
    days = 7
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    paid_orders = _paid_orders(orders)
    refunded_orders = _refunded_orders(orders)

    revenue = sum(
        _safe_float(order.get("total_price"))
        for order in paid_orders
    )

    refunds = sum(
        _safe_float(order.get("total_price"))
        for order in refunded_orders
    )

    taxes = sum(
        _safe_float(order.get("total_tax"))
        for order in paid_orders
    )

    shipping = sum(
        _shipping_amount(order)
        for order in paid_orders
    )

    discounts = sum(
        _safe_float(order.get("total_discounts"))
        for order in paid_orders
    )

    estimated_cogs = revenue * 0.45
    estimated_platform_fees = revenue * 0.029

    gross_profit = revenue - estimated_cogs - refunds
    net_profit = gross_profit - estimated_platform_fees

    net_margin = (
        net_profit / revenue * 100
        if revenue > 0 else 0
    )

    return (
        f"Weekly Profit & Loss Report\n\n"
        f"Revenue: {_money(revenue)}\n"
        f"Refunds: {_money(refunds)}\n"
        f"Taxes Collected: {_money(taxes)}\n"
        f"Shipping Income: {_money(shipping)}\n"
        f"Discounts: {_money(discounts)}\n\n"
        f"Estimated Cost of Goods Sold: {_money(estimated_cogs)}\n"
        f"Estimated Shopify / Payment Fees: {_money(estimated_platform_fees)}\n\n"
        f"Gross Profit: {_money(gross_profit)}\n"
        f"Net Profit: {_money(net_profit)}\n"
        f"Estimated Net Margin: {net_margin:.1f}%\n\n"
        f"Note: COGS and platform fees are estimated. "
        f"Connect product cost data for exact profit."
    )


async def get_cash_flow_dashboard(days=30):
    """
    Cash flow dashboard.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))

    if not orders:
        return f"No cash flow data found in the last {days} days."

    paid_orders = _paid_orders(orders)
    refunded_orders = _refunded_orders(orders)

    pending_orders = [
        order for order in orders
        if not order.get("fulfillment_status")
    ]

    cash_received = sum(
        _safe_float(order.get("total_price"))
        for order in paid_orders
    )

    refund_liability = sum(
        _safe_float(order.get("total_price"))
        for order in refunded_orders
    )

    pending_order_value = sum(
        _safe_float(order.get("total_price"))
        for order in pending_orders
    )

    estimated_platform_fees = cash_received * 0.029

    estimated_available_cash = (
        cash_received
        - refund_liability
        - estimated_platform_fees
    )

    return (
        f"Cash Flow Dashboard — Last {days} days\n\n"
        f"Cash received from paid orders: {_money(cash_received)}\n"
        f"Estimated platform/payment fees: {_money(estimated_platform_fees)}\n"
        f"Refunded / refund-risk amount: {_money(refund_liability)}\n"
        f"Unfulfilled order value at risk: {_money(pending_order_value)}\n\n"
        f"Estimated Available Cash: {_money(estimated_available_cash)}\n\n"
        f"Notes:\n"
        f"- Pending or unfulfilled orders may create refund risk.\n"
        f"- Shopify payout timing is not included.\n"
        f"- Connect Shopify payouts or bank APIs for exact cash flow."
    )


async def get_profit_forecast(days=30):
    """
    Forecast revenue and profit based on recent average revenue.
    """
    orders = await _orders_between(datetime.now() - timedelta(days=days))
    paid_orders = _paid_orders(orders)

    if not paid_orders:
        return f"No paid order data found in the last {days} days to forecast profit."

    revenue = sum(
        _safe_float(order.get("total_price"))
        for order in paid_orders
    )

    average_daily_revenue = (
        revenue / days
        if days > 0 else 0
    )

    next_7_day_revenue = average_daily_revenue * 7
    next_30_day_revenue = average_daily_revenue * 30

    estimated_cogs_rate = 0.45
    estimated_fee_rate = 0.029

    next_7_day_profit = (
        next_7_day_revenue
        - (next_7_day_revenue * estimated_cogs_rate)
        - (next_7_day_revenue * estimated_fee_rate)
    )

    next_30_day_profit = (
        next_30_day_revenue
        - (next_30_day_revenue * estimated_cogs_rate)
        - (next_30_day_revenue * estimated_fee_rate)
    )

    return (
        f"Profit Forecast Based on Last {days} Days\n\n"
        f"Historical revenue: {_money(revenue)}\n"
        f"Average daily revenue: {_money(average_daily_revenue)}\n\n"
        f"Next 7 days forecast:\n"
        f"- Revenue: {_money(next_7_day_revenue)}\n"
        f"- Estimated profit: {_money(next_7_day_profit)}\n\n"
        f"Next 30 days forecast:\n"
        f"- Revenue: {_money(next_30_day_revenue)}\n"
        f"- Estimated profit: {_money(next_30_day_profit)}\n\n"
        f"Assumptions:\n"
        f"- Estimated COGS: 45% of revenue\n"
        f"- Estimated payment/platform fees: 2.9% of revenue\n"
        f"- Forecast uses recent sales velocity only."
    )
# -------------------------------------------------------------------
# Refund / Chargeback Risk Tools
# -------------------------------------------------------------------

async def analyze_refund_risk(order_id):
    """
    Analyze refund / chargeback risk for a Shopify order.

    Important:
    This does NOT approve a refund.
    This only gives the owner a recommendation.
    """
    order = await _get_order_by_number_or_id(order_id)

    if not order:
        return f"Order #{order_id} not found."

    name = order.get("name", f"#{order_id}")
    total_price = _safe_float(order.get("total_price"))
    financial_status = order.get("financial_status", "unknown")
    fulfillment_status = order.get("fulfillment_status") or "unfulfilled"
    refunds = order.get("refunds", [])

    customer = order.get("customer") or {}
    customer_orders_count = customer.get("orders_count", 0)

    created = order.get("created_at", "")
    days_since_order = None

    if created:
        try:
            created_date = datetime.fromisoformat(created[:10])
            days_since_order = (datetime.now() - created_date).days
        except Exception:
            days_since_order = None

    risk_score = 0
    risk_reasons = []

    if refunds:
        risk_score += 40
        risk_reasons.append("Order already has refund activity.")

    if total_price >= 50000:
        risk_score += 25
        risk_reasons.append("High-value order.")

    if customer_orders_count <= 1:
        risk_score += 20
        risk_reasons.append("New or low-history customer.")

    if fulfillment_status == "fulfilled":
        risk_score += 15
        risk_reasons.append("Order has already been fulfilled.")

    if days_since_order is not None and days_since_order > 30:
        risk_score += 25
        risk_reasons.append("Refund request is outside the 30-day return window.")

    if financial_status in ["refunded", "partially_refunded"]:
        risk_score += 40
        risk_reasons.append("Order is already refunded or partially refunded.")

    if risk_score >= 70:
        risk_level = "High"
        recommendation = "Do NOT auto-approve. Send to owner/manual review."
    elif risk_score >= 40:
        risk_level = "Medium"
        recommendation = "Review before approving."
    else:
        risk_level = "Low"
        recommendation = "Likely safe to approve if store policy allows."

    reasons_text = (
        "\n".join(f"- {reason}" for reason in risk_reasons)
        if risk_reasons
        else "- No major risk signals detected."
    )

    return (
        f"Refund / Chargeback Risk Analysis for {name}\n\n"
        f"Order value: {_money(total_price)}\n"
        f"Financial status: {financial_status}\n"
        f"Fulfillment status: {fulfillment_status}\n"
        f"Customer order history: {customer_orders_count} orders\n"
        f"Days since order: "
        f"{days_since_order if days_since_order is not None else 'unknown'}\n\n"
        f"Risk score: {risk_score}/100\n"
        f"Risk level: {risk_level}\n\n"
        f"Risk reasons:\n"
        f"{reasons_text}\n\n"
        f"Recommendation: {recommendation}\n\n"
        f"Important: This is only a risk recommendation. "
        f"No refund has been approved or processed."
    )


async def suggest_refund_decision(order_id):
    """
    Lightweight wrapper that gives a decision-style recommendation.
    """
    risk_report = await analyze_refund_risk(order_id)

    if "not found" in risk_report.lower():
        return risk_report

    if "Risk level: High" in risk_report:
        decision = "Decision recommendation: Reject or require manual review."
    elif "Risk level: Medium" in risk_report:
        decision = "Decision recommendation: Manual review required before approval."
    else:
        decision = "Decision recommendation: Safe to approve only if policy allows."

    return f"{risk_report}\n\n{decision}"


# -------------------------------------------------------------------
# Optional Finance Utility Helpers
# -------------------------------------------------------------------

async def get_finance_overview(days=30):
    """
    One combined finance overview using existing finance tools.
    """
    return (
        f"Finance Overview — Last {days} days\n\n"
        f"{await get_revenue_summary(days)}\n\n"
        f"{await get_revenue_trends()}\n\n"
        f"{await get_refund_summary(days)}\n\n"
        f"{await categorize_shopify_transactions(days)}\n\n"
        f"{await get_cash_flow_dashboard(days)}\n\n"
        f"{await get_profit_forecast(days)}"
    )


async def get_executive_snapshot():
    """
    Combined business snapshot for Executive AI.
    """
    return (
        f"Executive Snapshot\n\n"
        f"{await get_revenue_summary(30)}\n\n"
        f"{await get_revenue_trends()}\n\n"
        f"{await get_order_insights(30)}\n\n"
        f"{await get_cash_flow_dashboard(30)}\n\n"
        f"{await get_profit_forecast(30)}\n\n"
        f"{await forecast_all_reorders()}"
    )
# -------------------------------------------------------------------
# Abandoned Cart / Checkout Tools
# -------------------------------------------------------------------

async def get_abandoned_checkouts(days=7):
    """
    Fetch abandoned checkouts from Shopify.
    These are customers who started checkout but did not complete purchase.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")

    data = await _get("checkouts.json", params={
        "created_at_min": since,
        "status": "open",
        "limit": 50
    })

    if not data or not data.get("checkouts"):
        return f"No abandoned checkouts found in the last {days} days."

    checkouts = data["checkouts"]

    lines = [f"Abandoned Checkouts — Last {days} days\n"]

    for checkout in checkouts[:10]:
        checkout_id = checkout.get("id")
        email = checkout.get("email", "No email")
        phone = checkout.get("phone", "No phone")
        total_price = checkout.get("total_price", "0.00")
        abandoned_url = checkout.get("abandoned_checkout_url", "No checkout URL")

        items = checkout.get("line_items", [])
        item_names = ", ".join(
            item.get("title", "Unknown item") for item in items
        ) or "No items"

        lines.append(
            f"Checkout ID: {checkout_id}\n"
            f"Customer email: {email}\n"
            f"Customer phone: {phone}\n"
            f"Cart value: ₹{total_price}\n"
            f"Items: {item_names}\n"
            f"Recovery URL: {abandoned_url}\n"
        )

    return "\n".join(lines)

# -------------------------------------------------------------------
# End of shopify_tools.py
# -------------------------------------------------------------------