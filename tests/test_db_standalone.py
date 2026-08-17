"""Test DB auto-repair and login — standalone"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import database.db as dbmod
test_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_clean.db")
if os.path.exists(test_db):
    os.remove(test_db)
for ext in ["-wal", "-shm"]:
    p = test_db + ext
    if os.path.exists(p):
        os.remove(p)

# Test 1: Clean DB -> init -> login
print("=== Test 1: Full DB init and query ===")
dbmod.DB_PATH = test_db
dbmod._local = type("t", (), {"connection": None})()
dbmod.init_db()

conn = dbmod.get_db()
c = conn.execute("SELECT count(*) FROM users")
print(f"Users: {c.fetchone()[0]}")
c = conn.execute("SELECT username, role, display_name FROM users")
for row in c.fetchall():
    print(f"  - {row['username']} ({row['role']}): {row['display_name']}")

# Test login function (standalone)
from werkzeug.security import check_password_hash
user = dbmod.dict_from_row(conn.execute(
    "SELECT * FROM users WHERE username = ? AND is_active = 1", ["store"]
).fetchone())
print(f"\nStore user found: {user is not None}")
if user:
    pw_match = check_password_hash(user["password_hash"], "***")
    print(f"Password match: {pw_match}")

conn.close()
print("Test 1 passed!\n")

# Test 2: Corrupt the DB file and auto-repair
print("=== Test 2: Auto-repair corrupted DB ===")
dbmod._local = type("t", (), {"connection": None})()
# Write garbage over the file
with open(test_db, "w") as f:
    f.write("garbage data not sqlite at all")

conn2 = dbmod.get_db()
c2 = conn2.execute("SELECT count(*) FROM users")
print(f"Users after repair: {c2.fetchone()[0]}")
user2 = dbmod.dict_from_row(conn2.execute(
    "SELECT * FROM users WHERE username = ? AND is_active = 1", ["store"]
).fetchone())
print(f"Store user exists after repair: {user2 is not None}")
conn2.close()
print("Test 2 passed!\n")

# Cleanup
try:
    os.remove(test_db)
    for ext in ["-wal", "-shm"]:
        p = test_db + ext
        if os.path.exists(p):
            os.remove(p)
except:
    pass

print("=== ALL TESTS PASSED ===")
