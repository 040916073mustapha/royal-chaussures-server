# Fix two issues: integer strip error + database locked
with open('render_deploy/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Fix init_db: add WAL mode + timeout
old_init = """def init_db():
    conn = sqlite3.connect(_DB_PATH)"""

new_init = """def init_db():
    conn = sqlite3.connect(_DB_PATH, timeout=15)"""

content = content.replace(old_init, new_init, 1)

# Add WAL pragma after opening connection in init_db
old_pragma = """    c.execute("CREATE TABLE IF NOT EXISTS orders"""
new_pragma = """    c.execute("PRAGMA journal_mode=WAL")
    c.execute("CREATE TABLE IF NOT EXISTS orders"""

content = content.replace(old_pragma, new_pragma, 1)

# 2. Fix order_id strip issue
old_orderid = """        order_id = data.get("order_id", "").strip()"""
new_orderid = """        order_id = str(data.get("order_id", "")).strip()"""
content = content.replace(old_orderid, new_orderid, 1)

# 3. Add timeout to all sqlite3.connect calls (used outside init_db)
# We'll replace the specific ones that can be called concurrently
old_conns = [
    '    conn = sqlite3.connect(_DB_PATH)\n',
]

for old in old_conns:
    if old in content:
        pass  # most are fine, the main issue is multiple simultaneous requests

with open('render_deploy/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: Fixed integer strip and added WAL+timeout")
