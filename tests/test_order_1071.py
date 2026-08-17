#!/usr/bin/env python3
"""Find order #1071 and create ZR shipment."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!…026!"}, allow_redirects=False)

orders = s.get("http://localhost:5050/api/orders?limit=50", timeout=10).json()

target = None
for o in orders:
    if "#1071" in o.get("order_name", ""):
        target = o
        break

if target:
    oid = target["id"]
    print("=== Order #1071 Found ===")
    print("ID:", oid)
    print("Customer:", target.get("customer_name"))
    print("Phone:", target.get("customer_phone"))
    print("Amount:", target.get("total_amount"))
    addr = target.get("shipping_address")
    if isinstance(addr, str):
        try: addr = json.loads(addr)
        except: pass
    print("Address:", json.dumps(addr, indent=2, ensure_ascii=False))
    items = target.get("items")
    if isinstance(items, str):
        try: items = json.loads(items)
        except: pass
    print("Items:", json.dumps(items, indent=2, ensure_ascii=False))
    
    print("\n=== Creating ZR Shipment ===")
    r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print("Status:", r.status_code)
    result = r.json()
    print(json.dumps(result, indent=2, ensure_ascii=False)[:1200])
else:
    print("Order #1071 not found in recent 50 orders")
    for o in orders[:5]:
        print("  ", o.get("order_name"))
