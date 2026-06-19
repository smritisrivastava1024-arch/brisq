import sqlite3

conn = sqlite3.connect("store.db")
cursor = conn.cursor()

# Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    item TEXT NOT NULL,
    status TEXT NOT NULL,
    delivery_date TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS refunds (
    order_id TEXT PRIMARY KEY,
    eligible TEXT NOT NULL,
    note TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory (
    item TEXT PRIMARY KEY,
    stock INTEGER NOT NULL,
    warehouse TEXT NOT NULL
)
""")

# Insert sample data
orders_data = [
    ("1234", "Wireless Headphones", "Shipped", "June 20"),
    ("5678", "Running Shoes", "Processing", "June 25"),
    ("9999", "Phone Case", "Delivered", "June 14"),
]
cursor.executemany("INSERT OR REPLACE INTO orders VALUES (?, ?, ?, ?)", orders_data)

refunds_data = [
    ("1234", "No", "Order not delivered yet"),
    ("9999", "Yes", "Processed within 3-5 business days"),
]
cursor.executemany("INSERT OR REPLACE INTO refunds VALUES (?, ?, ?)", refunds_data)

inventory_data = [
    ("Wireless Headphones", 45, "Mumbai"),
    ("Running Shoes", 0, "Delhi"),
    ("Phone Case", 230, "Bangalore"),
]
cursor.executemany("INSERT OR REPLACE INTO inventory VALUES (?, ?, ?)", inventory_data)

conn.commit()
conn.close()

print("Database created successfully: store.db")