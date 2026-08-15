#!/usr/bin/env python3
"""Debug login issue."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests, re

s = requests.Session()
# Step 1: GET login page
r1 = s.get("http://localhost:5050/login", timeout=10)
print(f"GET login: {r1.status_code}")
print(f"Cookies: {dict(s.cookies)}")

# Step 2: POST login
r2 = s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})
print(f"POST login: {r2.status_code}")
print(f"Cookies after: {dict(s.cookies)}")
print(f"Final URL: {r2.url}")

# Step 3: Try /api/orders
r3 = s.get("http://localhost:5050/api/orders?limit=1", timeout=10)
print(f"API orders: {r3.status_code}")
if r3.status_code == 200:
    import json
    orders = r3.json()
    print(f"Got {len(orders)} orders")
    for o in orders[:2]:
        print(f"  {o['id']}: {o.get('order_name')} - {o.get('customer_phone')}")
else:
    print(f"Body[:200]: {r3.text[:200]}")
