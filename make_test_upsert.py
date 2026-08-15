import ast

with open('server.py', 'rb') as f:
    raw = f.read()

idx1 = raw.find(b'def upsert_order_from_shopify')
idx2 = raw.find(b'def get_zr_shipments()')
idx3 = raw.find(b'\ndef ', idx2 + 30)
if idx3 == -1:
    idx3 = len(raw)

block = raw[idx1:idx3]

preamble = (
    b'import os\n'
    b'import sqlite3\n'
    b'import logging\n'
    b'logger = logging.getLogger("test")\n'
    b'_DB_PATH = "test.db"\n'
    b'\n'
    b'def get_orders_db(timeout=30):\n'
    b'    conn = sqlite3.connect(_DB_PATH, timeout=timeout)\n'
    b'    conn.execute("PRAGMA busy_timeout=30000")\n'
    b'    conn.execute("PRAGMA journal_mode=WAL")\n'
    b'    conn.execute("PRAGMA synchronous=NORMAL")\n'
    b'    conn.execute("PRAGMA foreign_keys=OFF")\n'
    b'    conn.row_factory = sqlite3.Row\n'
    b'    return conn\n'
    b'\n'
    b'def _safe_str(val):\n'
    b'    return str(val)\n'
    b'\n'
)

with open('test_upsert_only.py', 'wb') as f:
    f.write(preamble + block)

with open('test_upsert_only.py', 'r', encoding='utf-8') as f:
    ast.parse(f.read())
print('Syntax OK in isolated test!')
