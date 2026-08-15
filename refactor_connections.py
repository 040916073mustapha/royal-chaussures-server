"""Replace ALL raw sqlite3.connect(_DB_PATH) calls with get_orders_db() in server.py"""
import re

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# Pattern: conn = sqlite3.connect(_DB_PATH) (with optional timeout)
# We need to replace with conn = get_orders_db()

def replace_connect(m):
    """Replace raw connect with get_orders_db()"""
    global changes
    full = m.group(0)
    changes += 1
    # Return just conn = get_orders_db()
    indent = m.group(1)
    return indent + "conn = get_orders_db()"

# Match all conn = sqlite3.connect(_DB_PATH...) except inside get_orders_db and init_db
pattern = r'(\s*)conn\s*=\s*sqlite3\.connect\(_DB_PATH[^)]*\)'

# We need to exclude the helper function itself and init_db
# Strategy: process in blocks
lines = content.split('\n')
new_lines = []
in_get_orders = False
in_init_db = False

for i, line in enumerate(lines):
    if "def get_orders_db(" in line:
        in_get_orders = True
    if "def init_db(" in line:
        in_init_db = True
    if in_get_orders:
        if line.strip().startswith("def ") and "get_orders" not in line:
            in_get_orders = False
        new_lines.append(line)
        continue
    if in_init_db:
        if line.strip().startswith("def ") and "init_db" not in line:
            in_init_db = False
        new_lines.append(line)
        continue
    
    # Replace sqlite3.connect with get_orders_db()
    new_line = re.sub(r'(\s*)conn\s*=\s*sqlite3\.connect\(_DB_PATH(?:\s*,\s*\w+\s*=\s*\w+)?\)',
                      r'\1conn = get_orders_db()', line)
    
    # Also handle _conn, _conn2, conn2 patterns
    new_line = re.sub(r'(\s*)(_?conn\d?)\s*=\s*sqlite3\.connect\(_DB_PATH(?:\s*,\s*\w+\s*=\s*\w+)?\)',
                       r'\1\2 = get_orders_db()', new_line)
    
    if new_line != line:
        changes += 1
    
    new_lines.append(new_line)

content = '\n'.join(new_lines)

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Replaced {changes} connections")
