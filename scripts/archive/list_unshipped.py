#!/usr/bin/env python3
"""Find truly unshipped order for Phase 2 test."""
import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import requests,json

s=requests.Session()
s.post('http://localhost:5050/login',data={'username':'admin','password':'RoyalChaussures2026!'})
orders=s.get('http://localhost:5050/api/orders',params={'limit':50},timeout=10).json()

for o in orders:
    zr=o.get('zr_parcel_id','') or ''
    phone=str(o.get('customer_phone',''))
    if not zr and phone:
        print(f'id={o["id"]:>6} name={str(o.get("order_name","")):>8} phone={phone[:18]:>18} cust={str(o.get("customer_name",""))[:20]:>20} amount={o.get("total_amount")}')
