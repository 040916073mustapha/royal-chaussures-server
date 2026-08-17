#!/usr/bin/env python3
"""List orders and test ZR shipment."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

s = requests.Session()
r = s.get("http://localhost:5050/login", timeout=10)
# First get login page, then POST
s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})
# Check if logged in
r2 = s.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10)
print(f"Orders status: {r2.status_code}")
if r2.status_code == 200:
    orders = r2.json()
    targets = [o for o in orders if "#107" in str(o.get("order_name",""))]
    for t in targets:
        zr = t.get("zr_parcel_id", "") or ""
        print(f'id={t["id"]:>6} name={t.get("order_name"):>8} phone={str(t.get("customer_phone",""))[:16]:>16} '
              f'cust={str(t.get("customer_name",""))[:15]:>15} amount={t.get("total_amount"):>6} zr={str(zr)[:20]}')
    
    # Pick first unshipped
    unshipped = [t for t in targets if not t.get("zr_parcel_id")]
    if unshipped:
        t = unshipped[0]
        oid = t["id"]
        print(f"\n=== Shipping order id={oid} ({t.get('order_name')}) ===")
        r3 = s.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
        print(json.dumps(r3.json(), indent=2, ensure_ascii=False)[:1000])
else:
    print("Login failed:", r2.text[:200])
