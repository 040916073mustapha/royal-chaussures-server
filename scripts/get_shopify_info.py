#!/usr/bin/env python
"""جلب معلومات Shopify: locations, orders count, latest order"""
import requests, json, os
from dotenv import load_dotenv

load_dotenv()

store = os.getenv("SHOPIFY_STORE", "rwqchh-na")
token = os.getenv("SHOPIFY_ORDERS_TOKEN", "")
api_ver = os.getenv("SHOPIFY_API_VERSION", "2024-10")
base = f"https://{store}.myshopify.com/admin/api/{api_ver}"
headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}

results = {}

# 1. Get Locations
try:
    r = requests.get(f"{base}/locations.json", headers=headers, timeout=10)
    if r.status_code == 200:
        locs = r.json().get("locations", [])
        results["locations"] = [{"id": loc["id"], "name": loc["name"]} for loc in locs]
    else:
        results["locations_error"] = f"{r.status_code}: {r.text[:200]}"
except Exception as e:
    results["locations_error"] = str(e)

# 2. Get first location ID (default)
if "locations" in results and results["locations"]:
    results["default_location_id"] = results["locations"][0]["id"]
    results["default_location_name"] = results["locations"][0]["name"]

# 3. Get recent orders count
try:
    r = requests.get(f"{base}/orders.json?status=any&limit=1", headers=headers, timeout=10)
    if r.status_code == 200:
        data = r.json()
        results["orders_count"] = len(data.get("orders", []))
        results["sample_order"] = data.get("orders", [{}])[0].get("name", "N/A")
    else:
        results["orders_error"] = f"{r.status_code}"
except Exception as e:
    results["orders_error"] = str(e)

# 4. Get products count
try:
    r = requests.get(f"{base}/products.json?limit=1", headers=headers, timeout=10)
    if r.status_code == 200:
        results["products_count"] = r.json().get("count", "?")
except:
    pass

print(json.dumps(results, indent=2, ensure_ascii=False))
