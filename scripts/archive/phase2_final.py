#!/usr/bin/env python3
"""Find #1067 in new DB and test ship."""
import requests, json
s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})
orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10).json()
for o in orders:
    if "#1067" in str(o.get("order_name","")):
        oid = o["id"]
        phone = o.get("customer_phone","")
        print(f"Found #{o.get('order_name')} id={oid} phone={phone}")
        r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print(r.text[:1500])
        break
