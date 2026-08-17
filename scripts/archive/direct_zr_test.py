#!/usr/bin/env python3
"""Create ZR shipment directly using zr_express_client functions."""
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

# Use known customer ID from ZR
customer_id = "e28547c8-7811-4e53-83f5-1c874258049a"  # Mustapha chabni

# Load territory mapping
map_path = r"C:\Users\Micro-Tech\.openclaw\workspace-shipment\scripts\territory_mapping.json"
with open(map_path, "r", encoding="utf-8") as f:
    tmap = json.load(f)

# Lookup "EL BRAYA" commune
city_id = None
district_id = None
for name, data in tmap.get("communes", {}).items():
    if "braya" in name.lower():
        city_id = data["id"]
        district_id = data["parentId"]
        print(f"Found commune: {name} -> id={city_id}, parent={district_id}")
        break

# Also lookup Alger wilaya
for name, wid in tmap.get("wilayas", {}).items():
    if "alger" in name.lower():
        print(f"Wilaya Alger: {name} -> id={wid}")
        if not district_id:
            district_id = wid
        break

print(f"Using: customer_id={customer_id}, cityTerritoryId={district_id}, districtTerritoryId={city_id}")

# Create shipment
payload = {
    "customer": {
        "customerId": customer_id,
        "name": "Kamilia snousi",
        "phone": {"number1": "+213659832856"}
    },
    "deliveryAddress": {
        "street": "EL BRAYA",
        "city": "Alger",
        "district": "EL BRAYA",
        "postalCode": "",
        "country": "algeria",
    },
    "orderedProducts": [{
        "unitPrice": 0,
        "quantity": 1,
        "productName": "Pochette Royal 06",
        "stockType": "none"
    }],
    "amount": 3200,
    "description": "Pochette Royal 06",
    "deliveryType": "home",
    "externalId": "#1076"
}

# Add territory IDs
if district_id:
    payload["deliveryAddress"]["cityTerritoryId"] = district_id
if city_id:
    payload["deliveryAddress"]["districtTerritoryId"] = city_id

print("\n=== Creating shipment ===")
resp = requests.post(f"{ZR_BASE_URL}/parcels", json=payload, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
try:
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False)[:500])
except:
    print(resp.text[:500])

# If it fails, try without territory IDs
if resp.status_code != 200:
    print("\n=== Retry: without territory IDs ===")
    payload2 = payload.copy()
    payload2["deliveryAddress"] = {
        "street": "EL BRAYA",
        "city": "Alger",
        "district": "EL BRAYA",
        "country": "algeria"
    }
    if district_id:
        payload2["deliveryAddress"]["cityTerritoryId"] = district_id
    if city_id:
        payload2["deliveryAddress"]["districtTerritoryId"] = city_id
    
    resp2 = requests.post(f"{ZR_BASE_URL}/parcels", json=payload2, headers=headers, timeout=15)
    print(f"Status: {resp2.status_code}")
    try:
        print(json.dumps(resp2.json(), indent=2, ensure_ascii=False)[:500])
    except:
        print(resp2.text[:500])
