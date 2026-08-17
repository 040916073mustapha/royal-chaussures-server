with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Find the EXACT match using the INSERT statement start
pattern = r"conn = sqlite3\.connect\(_DB_PATH\)\n        c = conn\.cursor\(\)\n        c\.execute\(\"INSERT INTO orders \(shopify_order_id, customer_name, customer_phone, wilaya, \nmunicipality, product, variant, total_price\) VALUES \(\?, \?, \?, \?, \?, \?, \?, \?\) ON CONFLICT\(shopify_order_id\) DO UPDATE SET \ntotal_price=excluded\.total_price, updated_at=datetime\('now'\)\", \(oid, name, phone, wilaya, city, product, variant, \ntotal\)\)"

m = re.search(pattern, content)
if m:
    print(f'Pattern found at offset {m.start()}, length {m.end()-m.start()}')
    matched = content[m.start():m.end()]
    print(f'Matched text: {repr(matched[:100])}...')
    
    # Build replacement with same line endings
    replacement = "conn = sqlite3.connect(_DB_PATH, timeout=30)\n        conn.execute(\"PRAGMA busy_timeout=30000\")\n        conn.execute(\"PRAGMA journal_mode=WAL\")\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))"
    
    content = content[:m.start()] + replacement + content[m.end():]
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: upsert_order_from_shopify fixed')
else:
    print('FAIL: regex not matched')
    # Debug: print the exact insertion block
    idx = content.find('def upsert_order_from_shopify')
    block = content[idx:idx+500]
    # Show repr for analysis
    for i, line in enumerate(block.split('\n')[:10]):
        print(f'{i}: {repr(line)}')
