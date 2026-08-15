import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The upsert_order_from_shopify function start
old = """        items = od.get("line_items", [])
        product = items[0].get("title", "") if items else ""
        variant = items[0].get("variant_title", "") if items else ""
        conn = get_orders_db()
        conn.execute("PRAGMA busy_timeout=30000")
        conn.execute("PRAGMA journal_mode=WAL")
        c = conn.cursor()
        c.execute("INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')", (oid, name, phone, wilaya, city, product, variant, total))
        if phone:
            c.execute("SELECT id FROM clients WHERE phone=?", (phone,))
            if c.fetchone():
                c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime('now') WHERE phone=?", (total, phone))
            else:
                c.execute("INSERT INTO clients (name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,1,?,datetime('now'))", (name, phone, wilaya, city, total))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"upsert error: {_safe_str(e)}")"""

new = """        items = od.get("line_items", [])
        product = items[0].get("title", "") if items else ""
        variant = items[0].get("variant_title", "") if items else ""
        conn = get_orders_db()
        try:
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
            c = conn.cursor()
            c.execute("INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')", (oid, name, phone, wilaya, city, product, variant, total))
            if phone:
                c.execute("SELECT id FROM clients WHERE phone=?", (phone,))
                if c.fetchone():
                    c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime('now') WHERE phone=?", (total, phone))
                else:
                    c.execute("INSERT INTO clients (name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,1,?,datetime('now'))", (name, phone, wilaya, city, total))
            conn.commit()
        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
        finally:
            try:
                conn.close()
            except:
                pass"""

if old in content:
    idx = content.find(old)
    print(f"Found at {idx}")
    content = content[:idx] + new + content[idx+len(old):]
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced")
else:
    print("Not found - checking with CRLF")
    old_crlf = old.replace('\n', '\r\n')
    if old_crlf in content:
        new_crlf = new.replace('\n', '\r\n')
        content = content.replace(old_crlf, new_crlf, 1)
        with open('server.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Replaced (CRLF)")
    else:
        print("Not found at all")
        # Debug
        idx = content.find("items = od.get")
        if idx >= 0:
            print(repr(content[idx:idx+50]))

# Verify syntax
import ast
with open('server.py', 'r', encoding='utf-8') as f:
    try:
        ast.parse(f.read())
        print("Syntax OK")
    except SyntaxError as e:
        print(f"SyntaxError: {e}")
