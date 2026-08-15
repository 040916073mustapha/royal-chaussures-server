#!/usr/bin/env python3
"""Final ZR test via Dashboard."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
# Login with redirects
r = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!…026!"})
print("Login:", r.status_code)

# Get orders
r = s.get("http://localhost:5050/api/orders?limit=50", timeout=10)
print("Orders:", r.status_code)
data = r.json()
print(f"Retrieved {len(data)} orders")

# Find #1071
target = None
for o in data:
    if "#1071" in o.get("order_name", ""):
        target = o
        break

if target:
    oid = target["id"]
    print(f"\n=== Order #1071 (id={oid}) ===")
    print(f"Customer: {target.get('customer_name')}")
    print(f"Phone: {target.get('customer_phone')}")
    
    # Ship
    r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print(f"\n=== Shipment Result ===")
    print(f"Status: {r.status_code}")
    result = r.json()
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1200])
else:
    print("Order #1071 not found")
    for o in data[:10]:
        print(f"  {o.get('id')}: {o.get('order_name')} - {o.get('customer_phone')}")
