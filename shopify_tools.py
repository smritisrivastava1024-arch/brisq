"""
shopify_tools.py
-----------------
Replaces the SQLite tool functions in api.py with real Shopify API calls.
All functions have the SAME names and return the SAME string format as
the SQLite versions -- so the agents and orchestrator don't change at all.

Requires in .env:
    SHOPIFY_STORE_URL=brisq-ai.myshopify.com
    SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxx
"""

import os
import requests
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


def _get(endpoint, params=None):
    """Simple GET helper for Shopify Admin API."""
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    return None


# ── Support Agent Tools ──

def get_order_status(order_id):
    """
    Look up a real Shopify order by ID or order number.
    Shopify order numbers are like #1001, #1002 etc.
    """
    # Try by order number first (e.g. customer says "order 1001")
    data = _get("orders.json", params={
        "name": f"#{order_id}",
        "status": "any",
        "fields": "id,name,financial_status,fulfillment_status,line_items,estimated_delivery_at,created_at"
    })

    if not data or not data.get("orders"):
        # Try by exact Shopify order ID
        data = _get(f"orders/{order_id}.json")
        if not data or "order" not in data:
            return f"Order #{order_id} not found. Please check the order number and try again."
        order = data["order"]
    else:
        order = data["orders"][0]

    name = order.get("name", f"#{order_id}")
    financial = order.get("financial_status", "unknown").replace("_", " ").title()
    fulfillment = order.get("fulfillment_status") or "unfulfilled"
    fulfillment = fulfillment.replace("_", " ").title()

    items = order.get("line_items", [])
    item_names = ", ".join(i["title"] for i in items) if items else "Unknown item"

    # Try to get estimated delivery
    delivery = order.get("estimated_delivery_at")
    if delivery:
        delivery_str = delivery[:10]  # just the date part
    else:
        # Fall back to created_at + 7 days as rough estimate
        created = order.get("created_at", "")
        if created:
            created_date = datetime.fromisoformat(created[:10])
            delivery_str = (created_date + timedelta(days=7)).strftime("%Y-%m-%d")
        else:
            delivery_str = "not available"

    return (
        f"Order {name}: {item_names}. "
        f"Payment: {financial}. "
        f"Fulfillment: {fulfillment}. "
        f"Estimated delivery: {delivery_str}."
    )


def check_refund(order_id):
    """
    Check if a Shopify order is eligible for a refund based on its
    financial status and whether it was fulfilled.
    """
    data = _get("orders.json", params={
        "name": f"#{order_id}",
        "status": "any",
        "fields": "id,name,financial_status,fulfillment_status,created_at,refunds"
    })

    if not data or not data.get("orders"):
        data = _get(f"orders/{order_id}.json")
        if not data or "order" not in data:
            return f"Order #{order_id} not found."
        order = data["order"]
    else:
        order = data["orders"][0]

    name = order.get("name", f"#{order_id}")
    financial = order.get("financial_status", "")
    existing_refunds = order.get("refunds", [])

    if existing_refunds:
        return f"Order {name}: A refund has already been processed for this order."

    if financial in ["paid", "partially_paid"]:
        created = order.get("created_at", "")
        if created:
            created_date = datetime.fromisoformat(created[:10])
            days_since = (datetime.now() - created_date).days
            if days_since <= 30:
                return (
                    f"Order {name}: Eligible for a refund. "
                    f"Order was placed {days_since} days ago (within the 30-day return window)."
                )
            else:
                return (
                    f"Order {name}: Not eligible for a refund. "
                    f"Order was placed {days_since} days ago, which is outside the 30-day return window."
                )
        return f"Order {name}: Likely eligible for refund — payment status is {financial}."

    if financial == "refunded":
        return f"Order {name}: This order has already been fully refunded."

    return f"Order {name}: Not eligible for a refund (payment status: {financial})."


# ── Inventory Agent Tools ──

def check_inventory(item_name):
    """
    Search Shopify products by name and return stock levels.
    """
    data = _get("products.json", params={
        "title": item_name,
        "fields": "id,title,variants,status"
    })

    if not data or not data.get("products"):
        return f"No product found matching '{item_name}'."

    product = data["products"][0]
    title = product["title"]
    variants = product.get("variants", [])

    if not variants:
        return f"{title}: No variants/stock data available."

    # Get inventory levels for all variants
    total_stock = 0
    out_of_stock_variants = []
    in_stock_variants = []

    for variant in variants:
        qty = variant.get("inventory_quantity", 0)
        variant_title = variant.get("title", "Default")
        total_stock += qty
        if qty <= 0:
            out_of_stock_variants.append(variant_title)
        else:
            in_stock_variants.append(f"{variant_title} ({qty} units)")

    if total_stock <= 0:
        return f"{title}: OUT OF STOCK across all variants."

    stock_detail = ", ".join(in_stock_variants) if len(variants) > 1 else f"{total_stock} units"
    return f"{title}: In stock — {stock_detail}."


# ── Forecasting Agent Tools ──

def get_all_products():
    """Returns real product names from Shopify."""
    data = _get("products.json", params={"fields": "title", "status": "active"})
    if not data or not data.get("products"):
        return "No products found in your Shopify store."
    names = [p["title"] for p in data["products"]]
    return "Products in your store: " + ", ".join(names)


def _get_sales_velocity(product_title, days=30):
    """
    Estimate daily sales velocity by looking at fulfilled orders
    containing this product in the last N days.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")

    data = _get("orders.json", params={
        "status": "any",
        "fulfillment_status": "shipped",
        "created_at_min": since,
        "fields": "line_items",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return 0

    total_sold = 0
    for order in data["orders"]:
        for item in order.get("line_items", []):
            if product_title.lower() in item.get("title", "").lower():
                total_sold += item.get("quantity", 0)

    return total_sold / days


def _get_product_stock(product_title):
    """Get current total stock for a product."""
    data = _get("products.json", params={
        "title": product_title,
        "fields": "title,variants"
    })
    if not data or not data.get("products"):
        return None, None

    product = data["products"][0]
    title = product["title"]
    total_stock = sum(
        v.get("inventory_quantity", 0) for v in product.get("variants", [])
    )
    return title, total_stock


def forecast_reorder(item_name):
    """Single product stockout forecast using real Shopify data."""
    title, stock = _get_product_stock(item_name)
    if title is None:
        return f"No product found matching '{item_name}'."

    avg_daily = _get_sales_velocity(title)

    if avg_daily <= 0:
        return (
            f"{title}: {stock} units in stock. "
            f"No recent sales data found to forecast demand."
        )

    days_until_stockout = stock / avg_daily if avg_daily > 0 else None
    suggested_reorder = round(avg_daily * 30)
    REORDER_THRESHOLD_DAYS = 14
    needs_reorder = days_until_stockout is not None and days_until_stockout <= REORDER_THRESHOLD_DAYS

    if needs_reorder:
        return (
            f"{title}: {stock} units in stock, selling ~{avg_daily:.1f}/day. "
            f"Stockout in ~{days_until_stockout:.0f} days. "
            f"RECOMMENDATION: Reorder ~{suggested_reorder} units soon."
        )
    return (
        f"{title}: {stock} units in stock, selling ~{avg_daily:.1f}/day. "
        f"Will last ~{days_until_stockout:.0f} days. No reorder needed yet."
    )


def forecast_all_reorders():
    """Bulk stockout forecast for all products using real Shopify data."""
    data = _get("products.json", params={"fields": "title,variants", "status": "active"})
    if not data or not data.get("products"):
        return "No products found in your Shopify store."

    lines = []
    REORDER_THRESHOLD_DAYS = 14

    for product in data["products"]:
        title = product["title"]
        stock = sum(v.get("inventory_quantity", 0) for v in product.get("variants", []))
        avg_daily = _get_sales_velocity(title)

        if avg_daily <= 0:
            lines.append(f"{title}: {stock} units, no recent sales data.")
            continue

        days_until_stockout = stock / avg_daily
        suggested_reorder = round(avg_daily * 30)
        needs_reorder = days_until_stockout <= REORDER_THRESHOLD_DAYS

        if needs_reorder:
            lines.append(
                f"{title}: {stock} units, ~{avg_daily:.1f}/day, "
                f"stockout in {days_until_stockout:.0f} days -- REORDER ~{suggested_reorder} units."
            )
        else:
            lines.append(
                f"{title}: {stock} units, ~{avg_daily:.1f}/day, "
                f"lasts {days_until_stockout:.0f} days -- OK."
            )

    return "\n".join(lines) if lines else "No inventory data available."


# ── Finance/Reporting Agent Tools ──

def get_revenue_summary(days=7):
    """
    Total revenue, order count, average order value
    for the last N days from real Shopify orders.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get("orders.json", params={
        "status": "any",
        "created_at_min": since,
        "fields": "total_price,financial_status,created_at",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return f"No orders found in the last {days} days."

    orders = data["orders"]
    paid_orders = [o for o in orders if o.get("financial_status") in ["paid", "partially_paid"]]
    total_revenue = sum(float(o.get("total_price", 0)) for o in paid_orders)
    order_count = len(paid_orders)
    avg_order_value = total_revenue / order_count if order_count > 0 else 0

    return (
        f"Last {days} days: {order_count} paid orders, "
        f"total revenue ₹{total_revenue:,.2f}, "
        f"average order value ₹{avg_order_value:,.2f}."
    )


def get_top_products(days=30):
    """
    Returns the best selling products by units sold
    in the last N days.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get("orders.json", params={
        "status": "any",
        "created_at_min": since,
        "fields": "line_items,financial_status",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return f"No sales data found in the last {days} days."

    product_sales = {}
    for order in data["orders"]:
        if order.get("financial_status") not in ["paid", "partially_paid"]:
            continue
        for item in order.get("line_items", []):
            title = item.get("title", "Unknown")
            qty = item.get("quantity", 0)
            revenue = float(item.get("price", 0)) * qty
            if title not in product_sales:
                product_sales[title] = {"units": 0, "revenue": 0}
            product_sales[title]["units"] += qty
            product_sales[title]["revenue"] += revenue

    if not product_sales:
        return "No product sales data found."

    sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["units"], reverse=True)
    lines = [f"Top products (last {days} days):"]
    for i, (title, data) in enumerate(sorted_products[:5], 1):
        lines.append(
            f"{i}. {title} — {data['units']} units sold, ₹{data['revenue']:,.2f} revenue"
        )
    return "\n".join(lines)


def get_refund_summary(days=30):
    """
    Returns total refunds issued and refund rate in the last N days.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get("orders.json", params={
        "status": "any",
        "created_at_min": since,
        "fields": "financial_status,total_price,refunds",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return f"No orders found in the last {days} days."

    orders = data["orders"]
    total_orders = len(orders)
    refunded_orders = [o for o in orders if o.get("financial_status") in ["refunded", "partially_refunded"]]
    refund_count = len(refunded_orders)
    refund_rate = (refund_count / total_orders * 100) if total_orders > 0 else 0
    total_refunded = sum(float(o.get("total_price", 0)) for o in refunded_orders)

    return (
        f"Last {days} days: {refund_count} refunded orders out of {total_orders} total "
        f"({refund_rate:.1f}% refund rate). "
        f"Total amount refunded: ₹{total_refunded:,.2f}."
    )


def get_revenue_trends():
    """
    Compares revenue this week vs last week and this month vs last month.
    """
    now = datetime.now()

    def fetch_revenue(start, end):
        data = _get("orders.json", params={
            "status": "any",
            "created_at_min": start.strftime("%Y-%m-%dT00:00:00Z"),
            "created_at_max": end.strftime("%Y-%m-%dT23:59:59Z"),
            "fields": "total_price,financial_status",
            "limit": 250
        })
        if not data or not data.get("orders"):
            return 0, 0
        paid = [o for o in data["orders"] if o.get("financial_status") in ["paid", "partially_paid"]]
        revenue = sum(float(o.get("total_price", 0)) for o in paid)
        return revenue, len(paid)

    # This week vs last week
    this_week_start = now - timedelta(days=7)
    last_week_start = now - timedelta(days=14)
    last_week_end = now - timedelta(days=7)

    this_week_rev, this_week_orders = fetch_revenue(this_week_start, now)
    last_week_rev, last_week_orders = fetch_revenue(last_week_start, last_week_end)

    # This month vs last month
    this_month_start = now.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    this_month_rev, this_month_orders = fetch_revenue(this_month_start, now)
    last_month_rev, last_month_orders = fetch_revenue(last_month_start, last_month_end)

    def trend(current, previous):
        if previous == 0:
            return "no previous data to compare"
        change = ((current - previous) / previous) * 100
        direction = "up" if change > 0 else "down"
        return f"{direction} {abs(change):.1f}% vs previous period"

    return (
        f"Revenue trends:\n"
        f"This week: ₹{this_week_rev:,.2f} ({this_week_orders} orders) — {trend(this_week_rev, last_week_rev)}\n"
        f"Last week: ₹{last_week_rev:,.2f} ({last_week_orders} orders)\n\n"
        f"This month: ₹{this_month_rev:,.2f} ({this_month_orders} orders) — {trend(this_month_rev, last_month_rev)}\n"
        f"Last month: ₹{last_month_rev:,.2f} ({last_month_orders} orders)"
    )


def get_customer_insights(days=30):
    """
    Returns new vs returning customers and top customers by spend.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get("orders.json", params={
        "status": "any",
        "created_at_min": since,
        "fields": "customer,total_price,financial_status",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return f"No customer data found in the last {days} days."

    orders = [o for o in data["orders"] if o.get("financial_status") in ["paid", "partially_paid"]]

    customer_spend = {}
    new_customers = 0
    returning_customers = 0

    for order in orders:
        customer = order.get("customer")
        if not customer:
            continue
        cid = customer.get("id")
        name = f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Unknown"
        orders_count = customer.get("orders_count", 1)
        spend = float(order.get("total_price", 0))

        if orders_count <= 1:
            new_customers += 1
        else:
            returning_customers += 1

        if cid not in customer_spend:
            customer_spend[cid] = {"name": name, "spend": 0}
        customer_spend[cid]["spend"] += spend

    top_customers = sorted(customer_spend.values(), key=lambda x: x["spend"], reverse=True)[:3]
    top_lines = "\n".join(
        f"  {i+1}. {c['name']} — ₹{c['spend']:,.2f}"
        for i, c in enumerate(top_customers)
    )

    return (
        f"Customer insights (last {days} days):\n"
        f"New customers: {new_customers}\n"
        f"Returning customers: {returning_customers}\n\n"
        f"Top customers by spend:\n{top_lines if top_lines else '  No data available'}"
    )


def get_order_insights(days=30):
    """
    Returns pending orders, average fulfillment time, and unfulfilled order count.
    """
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")
    data = _get("orders.json", params={
        "status": "any",
        "created_at_min": since,
        "fields": "fulfillment_status,created_at,updated_at,total_price,financial_status",
        "limit": 250
    })

    if not data or not data.get("orders"):
        return f"No order data found in the last {days} days."

    orders = data["orders"]
    total = len(orders)
    fulfilled = [o for o in orders if o.get("fulfillment_status") == "fulfilled"]
    unfulfilled = [o for o in orders if not o.get("fulfillment_status")]
    pending_value = sum(float(o.get("total_price", 0)) for o in unfulfilled)

    # Average fulfillment time for fulfilled orders
    fulfillment_times = []
    for o in fulfilled:
        created = o.get("created_at")
        updated = o.get("updated_at")
        if created and updated:
            created_dt = datetime.fromisoformat(created[:19])
            updated_dt = datetime.fromisoformat(updated[:19])
            days_to_fulfill = (updated_dt - created_dt).days
            if days_to_fulfill >= 0:
                fulfillment_times.append(days_to_fulfill)

    avg_fulfillment = (
        f"{sum(fulfillment_times)/len(fulfillment_times):.1f} days"
        if fulfillment_times else "not enough data"
    )

    return (
        f"Order insights (last {days} days):\n"
        f"Total orders: {total}\n"
        f"Fulfilled: {len(fulfilled)}\n"
        f"Unfulfilled/pending: {len(unfulfilled)} (₹{pending_value:,.2f} at risk)\n"
        f"Average fulfillment time: {avg_fulfillment}"
    )