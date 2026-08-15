import requests
import json
import sys

# Ensure output handles UTF-8
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

url = 'https://api.zrexpress.app/api/v1/parcels/search'

try:
    print(f"Final testing POST on: {url}")
    response = requests.post(url, headers=headers, json={}, timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        # Log to file to be safe with encodings
        with open('scripts/last_zr_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Print a small summary
        items = data.get('data', []) if isinstance(data, dict) else data
        print(f"Total parcels found: {len(items)}")
        if items and len(items) > 0:
            print(f"Sample tracking: {items[0].get('tracking_number') or items[0].get('code')}")
            print(f"Sample status: {items[0].get('status', {}).get('name') if isinstance(items[0].get('status'), dict) else items[0].get('status')}")
except Exception as e:
    print(f'Error: {str(e)}')
