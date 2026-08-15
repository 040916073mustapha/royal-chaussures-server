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

payload = {
    "pagination": {
        "page": 1,
        "per_page": 10
    }
}

try:
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    if response.status_code == 200:
        data = response.json()
        with open('scripts/full_parcel_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("Data saved to scripts/full_parcel_data.json")
    else:
        print(f"Error {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
