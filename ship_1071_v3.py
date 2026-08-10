#!/usr/bin/env python3
"""Login + Ship Order #1071 with dynamic ID lookup."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})

orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10)
data = orders.json()

target = None
for o in data:
    if "#1071" in o.get("order_name", ""):
        target = o
        break

if target:
    oid = target["id"]
    print(f"Order #1071 (id={oid}): {target.get('customer_name')} | {target.get('customer_phone')}")
    
    # SHIP IT!
    ship = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print(f"Status: {ship.status_code}")
    print(json.dumps(ship.json(), indent=2, ensure_ascii=False)[:1200])
    
    # Check if debug payload was written
    import os
    debug_path = "zr_debug_payload.json"
    if os.path.exists(debug_path):
        print(f"\n=== DEBUG PAYLOAD ===")
        with open(debug_path, "r") as f:
            print(f.read()[:800])
else:
    print("Order #1071 not found")
    for o in data[:3]:
        print(f"  id={o['id']} name={o.get('order_name')} phone={o.get('customer_phone')}")
