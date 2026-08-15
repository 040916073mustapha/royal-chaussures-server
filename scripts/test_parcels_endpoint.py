import requests
import json

headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

# Try POST on parcels
url = 'https://api.zrexpress.app/api/v1/parcels'
try:
    print(f"Testing POST on: {url}")
    response = requests.post(url, headers=headers, json={}, timeout=10)
    print(f'POST Status: {response.status_code}')
    print(f'POST Response: {response.text[:500]}')
except Exception as e:
    print(f'Error: {str(e)}')

# Try GET with a common list parameter
url = 'https://api.zrexpress.app/api/v1/parcels?page=1'
try:
    print(f"\nTesting GET on: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    print(f'GET Status: {response.status_code}')
    print(f'GET Response: {response.text[:500]}')
except Exception as e:
    print(f'Error: {str(e)}')
