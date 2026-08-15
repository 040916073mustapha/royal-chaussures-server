import ast

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# The current upsert block
old = '''        conn = get_orders_db()
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
        logger.error(f"upsert error: {_safe_str(e)}")'''

new = '''        conn = get_orders_db()
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
                pass'''

if old in content:
    idx = content.find(old)
    content = content[:idx] + new + content[idx+len(old):]
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced upsert block')
    try:
        ast.parse(content)
        print('Syntax OK!')
    except SyntaxError as e:
        print(f'SyntaxError line {e.lineno}: {e.msg}')
        lines = content.split('\n')
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+3)):
            print(f'{i+1}: {repr(lines[i])}')
else:
    print('Block not found')
    idx = content.find('conn = get_orders_db()')
    if idx >= 0:
        print(f'Found at {idx}')
        print(repr(content[idx:idx+300]))
