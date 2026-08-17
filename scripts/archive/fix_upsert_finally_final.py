with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the conn...conn.close section
old = "        conn = get_orders_db()\n        conn.execute(\"PRAGMA busy_timeout=30000\")\n        conn.execute(\"PRAGMA journal_mode=WAL\")\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n        if phone:\n            c.execute(\"SELECT id FROM clients WHERE phone=?\")"

new = "        conn = get_orders_db()\n        try:\n            conn.execute(\"PRAGMA busy_timeout=30000\")\n            conn.execute(\"PRAGMA journal_mode=WAL\")\n            c = conn.cursor()\n            c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n            if phone:\n                c.execute(\"SELECT id FROM clients WHERE phone=?\")"

# Try matching with \n (LF only — git checkout changed to LF)
old_2 = "        conn.commit()\n        conn.close()\n    except Exception as e:\n        logger.error(f\"upsert error: {_safe_str(e)}\")"
new_2 = "        conn.commit()\n    except Exception as e:\n        logger.error(f\"upsert error: {_safe_str(e)}\")\n    finally:\n        try:\n            conn.close()\n        except:\n            pass"

if old in content:
    content = content.replace(old, new, 1)
    print("Part 1 replaced (LF)")
elif old.replace('\n', '\r\n') in content:
    content = content.replace(old.replace('\n', '\r\n'), new.replace('\n', '\r\n'), 1)
    print("Part 1 replaced (CRLF)")
else:
    # Try with escapes
    old_f = "conn = get_orders_db()\n        conn.execute"
    idx = content.find(old_f)
    if idx >= 0:
        print(f"Found at {idx}: {repr(content[idx:idx+200])}")
    else:
        print("Part 1 NOT found")

if old_2 in content:
    content = content.replace(old_2, new_2, 1)
    print("Part 2 replaced (LF)")
elif old_2.replace('\n', '\r\n') in content:
    content = content.replace(old_2.replace('\n', '\r\n'), new_2.replace('\n', '\r\n'), 1)
    print("Part 2 replaced (CRLF)")
else:
    idx2 = content.find("conn.commit()\n        conn.close()\n    except")
    if idx2 >= 0:
        print(f"Found part 2 at {idx2}: {repr(content[idx2:idx2+100])}")
    else:
        print("Part 2 NOT found")

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done")
