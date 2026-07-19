"""
setup_sales_history.py
-----------------------
Adds a sales_history table to store.db and populates it with sample
daily sales data for the existing inventory items, so the forecasting
agent has real velocity data to work with.

Run this ONCE after your existing setup_db.py:

    python setup_sales_history.py
"""

import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# ── Create the table ──
cursor.execute("""
CREATE TABLE IF NOT EXISTS sales_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item TEXT NOT NULL,
    date TEXT NOT NULL,
    units_sold INTEGER NOT NULL
)
""")

# Clear out old sample data if this script is re-run
cursor.execute("DELETE FROM sales_history")

# ── Items must match what's in your inventory table ──
items_with_avg_daily_sales = {
    "Wireless Headphones": 4,   # sells ~4 units/day on average
    "Running Shoes": 7,         # faster mover
    "Phone Case": 12,           # high volume, low cost item
}

today = datetime.now()
days_of_history = 30

rows = []
for item, avg_daily in items_with_avg_daily_sales.items():
    for day_offset in range(days_of_history, 0, -1):
        date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        # add randomness so it's not a perfectly flat line
        units_sold = max(0, round(random.gauss(avg_daily, avg_daily * 0.3)))
        rows.append((item, date, units_sold))

cursor.executemany(
    "INSERT INTO sales_history (item, date, units_sold) VALUES (?, ?, ?)",
    rows
)

conn.commit()
conn.close()

print(f"✅ sales_history table created with {len(rows)} rows "
      f"({days_of_history} days x {len(items_with_avg_daily_sales)} items)")