import requests
import json

url = 'https://api.zrexpress.app/api/v1/orders'
headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json'
}

try:
    print(f"Testing URL: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Success! Response: {json.dumps(data, indent=2)[:500]}...')
    else:
        print(f'Response: {response.text}')
except Exception as e:
    print(f'Error: {str(e)}')
