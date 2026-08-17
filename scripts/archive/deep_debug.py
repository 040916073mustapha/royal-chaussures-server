#!/usr/bin/env python3
"""Deep debug - test dashboard ship endpoint step by step."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!haussures2026!"}, allow_redirects=False)

# Get Order #1076
orders = s.get("http://localhost:5050/api/orders?limit=50", timeout=10).json()
target = None
for o in orders:
    if "#1076" in o.get("order_name", ""):
        target = o
        break

if target:
    oid = target["id"]
    print(f"Order ID: {oid}")
    
    # Method 1: Call dashboard ship endpoint
    print("\n=== Method 1: Dashboard ship endpoint ===")
    r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print(f"Status: {r.status_code}")
    try: print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:500])
    except: print(r.text[:300])
    
    # Method 2: Direct ZR API call via dashboard server's own internal function
    # Let's look at what the server is actually sending
    print("\n=== Method 2: Get /system/status ===")
    sys_r = s.get("http://localhost:5050/system/status", timeout=10)
    print(json.dumps(sys_r.json(), indent=2, ensure_ascii=False))
else:
    print("Order #1076 not found")
