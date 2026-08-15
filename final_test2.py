#!/usr/bin/env python3
"""Final ZR test - manual cookie handling."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

# Step 1: Login with redirect
s = requests.Session()
r1 = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!…026!"})
print("Login URL:", r1.url)
print("Login status:", r1.status_code)
print("Cookies:", dict(s.cookies))

# Step 2: Get orders
r2 = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10)
print(f"Orders status: {r2.status_code}")
print(f"Orders URL: {r2.url}")
print(f"Orders text[:100]: {r2.text[:100]}")
print(f"Orders text contains 'login': {'login' in r2.text.lower()}")

if r2.status_code == 200 and r2.text.strip() and r2.text.strip()[0] == '[':
    data = r2.json()
    print(f"Got {len(data)} orders")
    target = None
    for o in data:
        if "#1071" in o.get("order_name", ""):
            target = o
            break
    
    if target:
        oid = target["id"]
        print(f"\nOrder #1071 (id={oid}): {target.get('customer_name')} - {target.get('customer_phone')}")
        r3 = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print(f"\nShip status: {r3.status_code}")
        print(f"Ship text[:100]: {r3.text[:100]}")
        if r3.status_code == 200:
            print(json.dumps(r3.json(), indent=2, ensure_ascii=False)[:1200])
        else:
            print("Full response:", r3.text[:500])
    else:
        print("Order #1071 not found")
else:
    print("Login failed or redirected to login page")
