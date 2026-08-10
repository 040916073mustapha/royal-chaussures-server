#!/usr/bin/env python3
"""Login + Ship Order #1071."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
r = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})
print("Login:", "OK" if "Dashboard" in r.text else "FAILED")

# Get orders & find #1071
orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10)
data = orders.json()

target = None
for o in data:
    if "#1071" in o.get("order_name", ""):
        target = o
        break

if target:
    oid = target["id"]
    print(f"\nOrder #1071 (id={oid}): {target.get('customer_name')} | {target.get('customer_phone')}")
    
    # SHIP IT!
    ship = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print(f"\n=== Shipment Result ===")
    print(f"Status: {ship.status_code}")
    print(json.dumps(ship.json(), indent=2, ensure_ascii=False)[:1200])
else:
    print("Order #1071 not found")
    for o in data[:5]:
        print(f"  id={o['id']} name={o.get('order_name')} phone={o.get('customer_phone')}")
