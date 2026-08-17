#!/usr/bin/env python3
"""Final Phase 2 test - ZR + Shopify + WhatsApp."""
import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import requests,json

s=requests.Session()
s.post('http://localhost:5050/login',data={'username':'admin','password':'RoyalChaussures2026!'})
orders=s.get('http://localhost:5050/api/orders',params={'limit':50},timeout=10).json()

target=None
for o in orders:
    phone=str(o.get('customer_phone',''))
    if not o.get('zr_parcel_id') and ('+213' in phone or phone.startswith('05') or phone.startswith('06')):
        target=o
        break
if not target:
    target=[o for o in orders if not o.get('zr_parcel_id')][0]

oid=target['id']
oname=target.get('order_name','')
phone=target.get('customer_phone','')
cname=target.get('customer_name','')
print(f'Shipping id={oid} name={oname} phone={phone} customer={cname}')
r=s.post(f'http://localhost:5050/api/orders/{oid}/ship',timeout=30)
print(json.dumps(r.json(),indent=2,ensure_ascii=False))
