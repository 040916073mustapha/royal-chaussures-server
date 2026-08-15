#!/usr/bin/env python3
"""Quick test dashboard."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

s = requests.Session()
r = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!haussures2026!"}, allow_redirects=False)
has_cookie = "session" in s.cookies
print("Login:", r.status_code, "Cookie:", has_cookie)

r2 = s.get("http://localhost:5050/api/stats", timeout=10)
print("Stats:", r2.status_code)

r3 = s.get("http://localhost:5050/api/orders?limit=1", timeout=10)
print("Orders:", r3.status_code)
if r3.status_code == 200:
    import json
    orders = r3.json()
    if orders:
        oid = orders[0]["id"]
        print("First order ID:", oid)
        print("Name:", orders[0].get("order_name"))
        print("Phone:", orders[0].get("customer_phone"))
        
        # Try ship
        r4 = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print("Ship status:", r4.status_code)
        print(json.dumps(r4.json(), indent=2, ensure_ascii=False)[:800])
    else:
        print("No orders")
else:
    print(r3.text[:200])
