#!/usr/bin/env python3
"""Debug ZR lookup directly."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests, json, os
from dotenv import load_dotenv
load_dotenv()

ZR_BASE_URL = os.getenv("ZR_BASE_URL", "https://api.zrexpress.app/api/v1")
ZR_TENANT_ID = os.getenv("ZR_TENANT_ID", "")
ZR_SECRET_KEY = os.getenv("ZR_SECRET_KEY", os.getenv("ZR_API_KEY", ""))

headers = {
    "X-Api-Key": ZR_SECRET_KEY,
    "X-Tenant": ZR_TENANT_ID,
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# 1. Search customers by phone
phone = "+213659832856"
print("=== Customer search ===")
r = requests.post(
    f"{ZR_BASE_URL}/customers/search",
    json={"pageNumber": 1, "pageSize": 50},
    headers=headers, timeout=10
)
print("Status:", r.status_code)
if r.status_code == 200:
    customers = r.json().get("items", [])
    print(f"Total customers: {len(customers)}")
    print("All customers:")
    for c in customers:
        cp = c.get("phone", {})
        c_phone = cp.get("number1", "") if isinstance(cp, dict) else str(cp)
        print(f"  id={c.get('id')} name={c.get('name')} phone={c_phone}")
    # Find by phone
    for c in customers:
        cp = c.get("phone", {})
        c_phone = cp.get("number1", "") if isinstance(cp, dict) else str(cp)
        if phone in c_phone or c_phone in phone:
            print(f"\nMATCH: {c['id']}")
    # Find by name
    for c in customers:
        if "kamilia" in c.get("name","").lower():
            print(f"\nNAME MATCH: {c['id']}")
else:
    print(r.text[:300])

# 2. Territory lookup from mapping file
print("\n=== Territory lookup ===")
map_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts", "territory_mapping.json")
if os.path.exists(map_path):
    with open(map_path, "r", encoding="utf-8") as f:
        tmap = json.load(f)
    
    # Try "EL BRAYA" or "el braya"
    communes = tmap.get("communes", {})
    for name, data in communes.items():
        if "braya" in name.lower():
            print(f"COMMUNE: {name} -> id={data['id']} parentId={data['parentId']}")
    
    # Wilaya for Alger  (since braya is in Alger)
    wilayas = tmap.get("wilayas", {})
    for name, wid in wilayas.items():
        if "alger" in name.lower():
            print(f"WILAYA: {name} -> id={wid}")
else:
    print("Mapping file not found")
