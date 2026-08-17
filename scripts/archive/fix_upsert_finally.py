with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The get_orders_db() is already in place, just add try/finally around upsert
# Find the block: conn = get_orders_db() in upsert_order_from_shopify

old_start = "        conn = get_orders_db()\n        conn.execute(\"PRAGMA busy_timeout=30000\")\n        conn.execute(\"PRAGMA journal_mode=WAL\")\n        c = conn.cursor()\n        c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n        if phone:\n            c.execute(\"SELECT id FROM clients WHERE phone=?\")"

new_start = "        conn = get_orders_db()\n        try:\n            conn.execute(\"PRAGMA busy_timeout=30000\")\n            conn.execute(\"PRAGMA journal_mode=WAL\")\n            c = conn.cursor()\n            c.execute(\"INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')\", (oid, name, phone, wilaya, city, product, variant, total))\n            if phone:\n                c.execute(\"SELECT id FROM clients WHERE phone=?\")"

old_end = "        conn.commit()\n        conn.close()\n    except Exception as e:\n        logger.error(f\"upsert error: {_safe_str(e)}\")"

new_end = "        conn.commit()\n    except Exception as e:\n        logger.error(f\"upsert error: {_safe_str(e)}\")\n    finally:\n        try:\n            conn.close()\n        except:\n            pass"

if old_start in content:
    content = content.replace(old_start, new_start, 1)
    print("Start replaced")
else:
    print("Start NOT found - checking...")
    idx = content.find("conn = get_orders_db()")
    if idx >= 0:
        print(repr(content[idx:idx+300]))
    else:
        # Try CRLF version
        crlf_start = old_start.replace('\n', '\r\n')
        if crlf_start in content:
            print("Found with CRLF")
            content = content.replace(crlf_start, new_start.replace('\n', '\r\n'), 1)
            print("Start replaced with CRLF")

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    print("End replaced")
else:
    crlf_end = old_end.replace('\n', '\r\n')
    if crlf_end in content:
        print("End found with CRLF")
        content = content.replace(crlf_end, new_end.replace('\n', '\r\n'), 1)
        print("End replaced with CRLF")
    else:
        print("End NOT found")
        # Debug: find the end block
        eidx = content.find("conn.close()\n    except Exception")
        if eidx >= 0:
            print(repr(content[eidx:eidx+200]))

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
