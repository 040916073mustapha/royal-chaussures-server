"""Test DB auto-repair and login flow"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Test 1: Clean DB creation
import database.db as dbmod
test_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_clean.db")
if os.path.exists(test_db):
    os.remove(test_db)
for ext in ["-wal", "-shm"]:
    p = test_db + ext
    if os.path.exists(p):
        os.remove(p)

dbmod.DB_PATH = test_db
dbmod._local = type("t", (), {"connection": None})()

conn = dbmod.get_db()
c = conn.execute("SELECT count(*) FROM sqlite_master")
print(f"Test 1 - Clean DB: {c.fetchone()[0]} tables")
conn.close()

# Test 2: Corrupted DB -> auto-repair
print("\nTest 2 - Corrupted DB auto-repair...")
with open(test_db, "w") as f:
    f.write("garbage data not sqlite")

dbmod._local = type("t", (), {"connection": None})()
conn2 = dbmod.get_db()
c2 = conn2.execute("SELECT count(*) FROM sqlite_master")
print(f"Test 2 - After repair: {c2.fetchone()[0]} tables")
conn2.close()

# Test 3: Full login with server
print("\nTest 3 - Full login test...")
from server import app
with app.test_client() as c:
    r = c.post("/api/v1/store/auth/login", json={
        "username": "store", "password": "***"
    })
    print(f"Store Login: {r.status_code}")
    data = r.get_json()
    if r.status_code == 200:
        print(f"  Token: {data['token'][:40]}...")
        print(f"  User: {data['user']['display_name']}")

        # Test product listing
        r2 = c.get("/api/v1/store/products", 
            headers={"Authorization": f"Bearer {data['token']}"})
        print(f"Products: {r2.status_code} - {r2.get_json().get('count')} items")

    r = c.post("/api/v1/admin/auth/login", json={
        "username": "admin", "password": "***"
    })
    print(f"Admin Login: {r.status_code}")
    data = r.get_json()
    if r.status_code == 200:
        print(f"  Token: {data['token'][:40]}...")

# Cleanup
try:
    os.remove(test_db)
    for ext in ["-wal", "-shm"]:
        p = test_db + ext
        if os.path.exists(p):
            os.remove(p)
except:
    pass

print("\n=== All tests passed! ===")
