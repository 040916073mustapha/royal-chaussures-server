#!/usr/bin/env python
"""اختبار اللوحة عبر بايثون"""
import requests, json

BASE = "http://localhost:5050"
s = requests.Session()

# Login
r = s.post(f"{BASE}/login", data={"username": "admin", "password": "RoyalChaussures2026!"})
print(f"Login: {r.status_code}")
print(f"URL after login: {r.url}")

# Dashboard
r = s.get(f"{BASE}/")
print(f"\nDashboard: {r.status_code}")
print(f"Title: {'لوحة التحكم' in r.text}")

# Orders page
r = s.get(f"{BASE}/orders")
print(f"\nOrders page: {r.status_code}")
print(f"Title: {'الطلبات' in r.text}")

# API agents
r = s.get(f"{BASE}/api/agents")
print(f"\nAgents API: {r.status_code}")
if r.status_code == 200:
    print(json.dumps(r.json(), ensure_ascii=False)[:200])

# API stats
r = s.get(f"{BASE}/api/stats")
print(f"\nStats API: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    print(f"Total orders: {d.get('total_orders')}")

# Order detail (first order)
r = s.get(f"{BASE}/api/orders?limit=1")
if r.status_code == 200 and len(r.json()) > 0:
    oid = r.json()[0]["id"]
    r2 = s.get(f"{BASE}/orders/{oid}")
    print(f"\nOrder #{oid} detail page: {r2.status_code}")
    print(f"Title: {'معلومات الطلب' in r2.text}")
    
    # Agent info
    r3 = s.get(f"{BASE}/api/orders/{oid}/agent")
    if r3.status_code == 200:
        print(f"Agent info: {json.dumps(r3.json(), ensure_ascii=False)}")
    
    # Conversations
    r4 = s.get(f"{BASE}/api/orders/{oid}/conversations")
    print(f"Conversations: {r4.status_code} count: {r4.json().get('count', 0)}")

print("\n✅ ALL TESTS DONE")
