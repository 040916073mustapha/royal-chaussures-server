with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add helper function right after init_db()
old = "init_db()\n\n_SHOP_NAME = \"Royal Chaussures\""
new = '''def get_orders_db(timeout=30):
    """Get a connection to royal_orders.db with safe PRAGMA settings"""
    conn = sqlite3.connect(_DB_PATH, timeout=timeout)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.row_factory = sqlite3.Row
    return conn


def exec_orders(sql, params=None, fetch=False, fetchone=False):
    """Execute SQL on orders DB with auto-close"""
    conn = get_orders_db()
    try:
        c = conn.cursor()
        if params:
            c.execute(sql, params)
        else:
            c.execute(sql)
        if fetchone:
            result = c.fetchone()
        elif fetch:
            result = c.fetchall()
        else:
            conn.commit()
            result = c.lastrowid
        return result
    finally:
        conn.close()


init_db()

_SHOP_NAME = "Royal Chaussures"'''

if old in content:
    content = content.replace(old, new, 1)
    with open('server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: helper functions added")
else:
    print("FAIL: pattern not found")
    idx = content.find("init_db()")
    if idx >= 0:
        print(repr(content[idx:idx+50]))
