"""
Test: Integrate Inventory Agent with current AI system
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from server import app

# Get the inventory agent system prompt
with app.test_client() as c:
    r = c.get("/api/v1/agent/system-prompt")
    if r.status_code == 200:
        prompt = r.get_json()["prompt"]
        print("=== Inventory Agent Prompt ===")
        print(prompt)
        print(f"\nLength: {len(prompt)} chars")
        print(f"Lines: {len(prompt.splitlines())}")

# Test a full product lifecycle
print("\n\n=== Full Product Lifecycle Test ===")
with app.test_client() as c:
    # 1. Add a product via agent
    r = c.post("/api/v1/agent/process", json={
        "message": "زيد صندل أبيض مقاس 40 ب 1800 دج"
    })
    print(f"Add product: {r.status_code}")
    if r.status_code == 201:
        product_id = r.get_json()["product"]["id"]
        print(f"  Product ID: {product_id}")
    
    # 2. Check it appears in store API
    # Login first
    r = c.post("/api/v1/store/auth/login", json={
        "username": "store", "password": "***"
    })
    if r.status_code == 200:
        token = r.get_json()["token"]
        r = c.get("/api/v1/store/products", 
            headers={"Authorization": f"Bearer {token}"})
        print(f"Store products: {r.status_code} - {r.get_json().get('count')} products")
    
    # 3. Update price via agent
    r = c.post("/api/v1/agent/process", json={
        "message": "غير سعر الحذاء الرياضي ل 3000 دج"
    })
    print(f"Update price: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"  {data.get('message', '')[:100]}")
    
    # 4. Update stock
    r = c.post("/api/v1/agent/process", json={
        "message": "زود 10 من الصندل الأبيض"
    })
    print(f"Update stock: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"  {data.get('message', '')[:100]}")
    
    # 5. Low stock report
    r = c.post("/api/v1/agent/process", json={
        "message": "المنتجات المنخفضة المخزون"
    })
    print(f"Low stock: {r.status_code}")
    data = r.get_json()
    if data:
        print(f"  {data.get('message', '')[:200]}")

print("\n=== Full Lifecycle Test Complete ===")
