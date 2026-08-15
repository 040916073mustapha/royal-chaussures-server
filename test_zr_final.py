#!/usr/bin/env python3
"""Test ZR shipment creation from Dashboard API - Final test."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

session = requests.Session()

# Login
login = session.post(
    "http://localhost:5050/login",
    data={"username": "admin", "password": "RoyalChaussures2026!haussures2026!"},
    allow_redirects=False
)
print("Login:", login.status_code)
print("Session cookie present:", bool(session.cookies.get("session")))

# Get order #1077 - Salma guelil - has phone
resp = session.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10)
orders = resp.json()

# Find order with phone number
target = None
for o in orders:
    phone = o.get("customer_phone", "")
    if phone and phone.strip():
        target = o
        break

if target:
    oid = target["id"]
    oname = target["order_name"]
    phone = target["customer_phone"]
    name = target["customer_name"]
    addr = target.get("shipping_address", "{}")
    items_info = target.get("items", "[]")
    
    print(f"\nCreating shipment for order #{oid} / {oname}:")
    print(f"  Customer: {name}")
    print(f"  Phone: {phone}")
    print(f"  Address: {str(addr)[:200]}")
    print(f"  Items: {str(items_info)[:200]}")
    print()
    
    # Create ZR shipment
    ship_resp = session.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=30)
    print(f"Status: {ship_resp.status_code}")
    try:
        result = ship_resp.json()
        print(json.dumps(result, indent=2, ensure_ascii=False)[:800])
    except:
        print(f"Raw: {ship_resp.text[:500]}")
else:
    print("No order with phone found.")
    for o in orders[:3]:
        print(f"  {o.get('id')}: {o.get('order_name')} phone={o.get('customer_phone')}")
