"""Test Inventory Agent"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from server import app

# Print agent routes
for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
    methods = ",".join(sorted(rule.methods - {"HEAD", "OPTIONS"}))
    if "/api/v1/agent" in rule.rule:
        print(f"  {methods:8s} {rule.rule}")

with app.test_client() as c:
    # Test 1: Add product
    print("\n--- Test 1: Add product ---")
    r = c.post("/api/v1/agent/process", json={
        "message": "زيد حذاء رياضي أحمر مقاس 38 ب 2500 دج"
    })
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"  Success: {data.get('success')}")
        print(f"  Action: {data.get('action')}")
        msg = data.get("message", "")
        print(f"  Message: {msg[:200]}")
    
    # Test 2: Check stock
    print("\n--- Test 2: Check stock ---")
    r = c.post("/api/v1/agent/process", json={
        "message": "شنو عندك في المخزون؟"
    })
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        msg = data.get("message", "")
        print(f"  Message: {msg[:200]}")
    
    # Test 3: Unknown command
    print("\n--- Test 3: Unknown command ---")
    r = c.post("/api/v1/agent/process", json={
        "message": "مرحبا كيف الحال"
    })
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        msg = data.get("message", "")
        print(f"  Message: {msg[:200]}")

    # Test 4: System prompt
    print("\n--- Test 4: System prompt ---")
    r = c.get("/api/v1/agent/system-prompt")
    print(f"Status: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"  Length: {data.get('prompt_length', 0)}")

    # Test 5: Check health
    print("\n--- Test 5: Health check ---")
    r = c.get("/health")
    print(f"Status: {r.status_code}")

print("\n=== Inventory Agent Test Complete ===")
