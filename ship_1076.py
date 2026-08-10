#!/usr/bin/env python3
"""Ship order #1076 via ZR Express."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!haussures2026!"}, allow_redirects=False)

# Find 1076
orders = s.get("http://localhost:5050/api/orders?limit=50", timeout=10).json()
oid = None
for o in orders:
    if "#1076" in o.get("order_name",""):
        oid = o["id"]
        print("Order #1076: id=", oid)
        print("Customer:", o.get("customer_name"))
        print("Phone:", o.get("customer_phone"))
        addr = o.get("shipping_address")
        if isinstance(addr, str):
            try: addr = json.loads(addr)
            except: addr = {}
        print("City:", addr.get("city",""), "/ Province:", addr.get("province",""))
        break

if oid:
    r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print("Ship status:", r.status_code)
    print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:1000])
else:
    print("Order not found")
