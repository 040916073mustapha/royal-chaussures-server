#!/usr/bin/env python3
"""Test ZR shipment from Dashboard API."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

# Login first
session = requests.Session()
login = session.post(
    "http://localhost:5050/login",
    data={"username": "admin", "password": "RoyalChaussures2026!haussures2026!"},
    allow_redirects=False
)
print(f"Login status: {login.status_code}")

# Get orders
orders = session.get("http://localhost:5050/api/orders?limit=3", timeout=10)
orders_data = orders.json()
print(f"Orders count: {len(orders_data)}" if isinstance(orders_data, list) else f"Response: {orders_data}")

if isinstance(orders_data, list) and len(orders_data) > 0:
    first = orders_data[1]  # second order (might have more complete data)
    oid = first.get("id", "")
    print(f"Order: id={oid}, name={first.get('order_name')}, phone={first.get('customer_phone')}")
    
    # Try creating ZR shipment
    print(f"\n=== Creating ZR Shipment for Order #{oid} ===")
    resp = session.post(f"http://localhost:5050/api/orders/{oid}/ship", timeout=20)
    result = resp.json()
    print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
else:
    print("No orders found. Profile:")
    # Try stats
    stats = session.get("http://localhost:5050/api/stats", timeout=10)
    print(f"Stats: {stats.json()}")
