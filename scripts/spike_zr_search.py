import requests
import json

headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

endpoints = [
    'https://api.zrexpress.app/api/v1/orders/search',
    'https://api.zrexpress.app/api/v1/parcels/search'
]

for url in endpoints:
    try:
        print(f"Testing POST on: {url}")
        # Sending an empty dict as body
        response = requests.post(url, headers=headers, json={}, timeout=10)
        print(f'Status: {response.status_code}')
        print(f'Response: {response.text[:1000]}')
        print("-" * 20)
    except Exception as e:
        print(f'Error testing {url}: {str(e)}')
