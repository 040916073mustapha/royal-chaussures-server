#!/usr/bin/env python3
"""Final ZR test - direct API call no session needed."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
# Login
login = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!…026!"}, allow_redirects=False)
has_cookie = "session" in s.cookies
print("Login:", login.status_code, "Has cookie:", has_cookie)
# Try orders
orders = s.get("http://localhost:5050/api/orders?limit=1", timeout=10)
print("Orders:", orders.status_code)
if orders.status_code == 200:
    data = orders.json()
    if data:
        oid = data[0]["id"]
        print(f"First order: id={oid}, name={data[0].get('order_name')}, phone={data[0].get('customer_phone')}")
        
        # Try ship
        r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print("Ship status:", r.status_code)
        print(json.dumps(r.json(), indent=2, ensure_ascii=False)[:800])
else:
    print("Body:", orders.text[:200])
