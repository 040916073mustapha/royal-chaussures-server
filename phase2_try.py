#!/usr/bin/env python3
"""Find unshipped order (not duplicate external ID) and test."""
import requests, json
s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})
orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10).json()
# Find first order with no zr_parcel_id (never shipped before)
for o in orders:
    if not o.get("zr_parcel_id"):
        oid = o["id"]
        phone = o.get("customer_phone","")
        oname = o.get("order_name","")
        cname = o.get("customer_name","")
        if "+213" in phone:
            print(f"Shipping {oname} id={oid} phone={phone} customer={cname}")
            r = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
            print(r.text[:1500])
            break
