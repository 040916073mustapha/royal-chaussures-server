import ast

with open('server.py', 'rb') as f:
    raw = f.read()

idx = raw.find(b'        conn = get_orders_db()\r\n        conn.execute("PRAGMA')

if idx >= 0:
    end_marker = b'        conn.close()\r\n    except Exception as e:\r\n        logger.error(f"upsert error: {_safe_str(e)}")'
    end_idx = raw.find(end_marker, idx)
    if end_idx >= 0:
        end_p = end_idx + len(end_marker)
        print(f'Block found: bytes {idx} to {end_p}')

        new_block = (
            b'        conn = get_orders_db()\r\n'
            b'        try:\r\n'
            b'            conn.execute("PRAGMA busy_timeout=30000")\r\n'
            b'            conn.execute("PRAGMA journal_mode=WAL")\r\n'
            b'            c = conn.cursor()\r\n'
            b'            c.execute("INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime(\'now\')", (oid, name, phone, wilaya, city, product, variant, total))\r\n'
            b'            if phone:\r\n'
            b'                c.execute("SELECT id FROM clients WHERE phone=?", (phone,))\r\n'
            b'                if c.fetchone():\r\n'
            b'                    c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime(\'now\') WHERE phone=?", (total, phone))\r\n'
            b'                else:\r\n'
            b'                    c.execute("INSERT INTO clients (name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,1,?,datetime(\'now\'))", (name, phone, wilaya, city, total))\r\n'
            b'            conn.commit()\r\n'
            b'        except Exception as e:\r\n'
            b'            logger.error(f"upsert error: {_safe_str(e)}")\r\n'
            b'        finally:\r\n'
            b'            try:\r\n'
            b'                conn.close()\r\n'
            b'            except:\r\n'
            b'                pass'
        )

        raw = raw[:idx] + new_block + raw[end_p:]
        with open('server.py', 'wb') as f:
            f.write(raw)
        print(f'Replaced {len(raw)} bytes')

        with open('server.py', 'r', encoding='utf-8') as f2:
            ast.parse(f2.read())
        print('Syntax OK!')
    else:
        print('End marker not found')
else:
    print('Block not found at all')
