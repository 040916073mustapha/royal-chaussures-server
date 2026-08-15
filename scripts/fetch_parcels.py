import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

url = 'https://api.zrexpress.app/api/v1/parcels/search'

# Sometimes 'search' requires at least an empty filter object or pagination
payload = {
    "pagination": {
        "page": 1,
        "per_page": 50
    },
    "filters": []
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if response.status_code == 200:
        data = response.json()
        # The structure might be different, let's dump the keys
        if isinstance(data, dict):
            print(f"Response Keys: {list(data.keys())}")
            items = data.get('data', [])
            if not items and 'items' in data: items = data['items']
            
            print(f"Parcels found: {len(items)}")
            for item in items[:5]: # Show first 5
                tracking = item.get('tracking_number') or item.get('code') or 'N/A'
                status = item.get('status', {})
                status_name = status.get('name') if isinstance(status, dict) else status
                customer = item.get('customer', {})
                customer_name = customer.get('name') if isinstance(customer, dict) else 'N/A'
                print(f"- {tracking} | {status_name} | {customer_name}")
        else:
            print(f"Data is a list of length: {len(data)}")
    else:
        print(f"Failed with status {response.status_code}: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
