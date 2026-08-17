#!/usr/bin/env python3
"""Ship order #1051 - HOUALi Hiba (fresh order, never shipped)."""
import requests, json
s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})
orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10).json()
for o in orders:
    if "#1051" in str(o.get("order_name","")):
        oid = o["id"]
        phone = o.get("customer_phone","")
        cname = o.get("customer_name","")
        print(f"Shipping #1051 id={oid} phone={phone} customer={cname}")
        r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print(r.text[:2000])
        break
