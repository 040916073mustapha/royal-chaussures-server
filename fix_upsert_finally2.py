with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_start = "conn = get_orders_db()\n        conn.execute(\"PRAGMA busy_timeout=30000\")\n        conn.execute(\"PRAGMA journal_mode=WAL\")\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n            if phone:\n                c.execute(\"SELECT id FROM clients WHERE phone=?\")"

new_start = "conn = get_orders_db()\n        try:\n            conn.execute(\"PRAGMA busy_timeout=30000\")\n            conn.execute(\"PRAGMA journal_mode=WAL\")\n            c = conn.cursor()\n            c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n            if phone:\n                c.execute(\"SELECT id FROM clients WHERE phone=?\")"

idx = content.find(old_start)
if idx >= 0:
    content = content[:idx] + new_start + content[idx+len(old_start):]
    print(f"Start replaced at {idx}")
else:
    print("Start NOT found")
    # Try to find just the first unique part
    idx2 = content.find("conn = get_orders_db()\n        conn.execute")
    if idx2 >= 0:
        print(f"Found partial at {idx2}")
        print(repr(content[idx2:idx2+100]))

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
