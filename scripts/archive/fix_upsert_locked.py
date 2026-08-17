with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = "        conn = sqlite3.connect(_DB_PATH)\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, \nmunicipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET \ntotal_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, \ntotal))"

new = "        conn = sqlite3.connect(_DB_PATH, timeout=30)\n        conn.execute(\"PRAGMA busy_timeout=30000\")\n        conn.execute(\"PRAGMA journal_mode=WAL\")\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))"

if old in content:
    content = content.replace(old, new, 1)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: upsert_order_from_shopify fixed')
else:
    print('FAIL: pattern not found')
    # Try with CRLF
    old_crlf = old.replace('\n', '\r\n')
    if old_crlf in content:
        print('Found with CRLF!')
        new_crlf = new.replace('\n', '\r\n')
        content = content.replace(old_crlf, new_crlf, 1)
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print('SUCCESS: upsert_order_from_shopify fixed (CRLF)')
    else:
        # Find the right text
        import re
        # Search for the INSERT statement
        pattern = r"conn = sqlite3\.connect\(_DB_PATH\)\s*\n\s*c = conn\.cursor\(\)\s*\n\s*c\.execute\(\"INSERT INTO orders"
        m = re.search(pattern, content)
        if m:
            print(f'Pattern found at offset {m.start()}: {repr(content[m.start():m.start()+100])}')
        else:
            print('Pattern not even with regex')
