#!/usr/bin/env python3
"""Test ZR shipment - find order with Algerian phone."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json

session = requests.Session()
session.post("http://localhost:5050/login", data={"username": "admin", "password": "RoyalChaussures2026!haussures2026!"}, allow_redirects=False)

orders = session.get("http://localhost:5050/api/orders", params={"limit": 50}, timeout=10).json()

print("Orders with Algerian phones:")
for o in orders:
    phone = o.get("customer_phone", "")
    if phone and ("+213" in phone or phone.startswith("05") or phone.startswith("06") or phone.startswith("07")):
        addr = o.get("shipping_address", "{}")
        if isinstance(addr, str):
            try: addr = json.loads(addr)
            except: addr = {}
        wilaya = addr.get("province", addr.get("city", "Alger"))
        commune = addr.get("city", "Alger Centre")
        print(f"  id={o['id']} name={o['order_name']} phone={phone} city={wilaya}/{commune}")
        print(f"    Customer: {o.get('customer_name')}")
        print(f"    Items: {o.get('items', '[]')[:100]}")
        break
