#!/usr/bin/env python3
"""Find unshipped order and test ZR."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalC…026!"})
orders = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10).json()

targets = [o for o in orders if "#107" in o.get("order_name","")]
for t in targets:
    zr_id = t.get("zr_parcel_id", "")
    print(f'id={t["id"]} name={t.get("order_name")} phone={t.get("customer_phone")} name={t.get("customer_name")[:15]} amount={t.get("total_amount")} zr={zr_id[:20] if zr_id else "-"}')
