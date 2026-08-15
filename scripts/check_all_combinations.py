import requests

base_urls = [
    'https://api.zrexpress.app/api/v1/',
    'https://api.zrexpress.app/api/',
    'https://api.zrexpress.app/',
]
endpoints = ['orders', 'shipments', 'tracking', 'parcels', 'external/orders', 'merchant/orders']

headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json'
}

for base in base_urls:
    for ep in endpoints:
        url = f'{base}{ep}'
        try:
            response = requests.get(url, headers=headers, timeout=5)
            print(f'URL {url}: {response.status_code}')
            if response.status_code == 200:
                print(f'*** SUCCESS: {url} ***')
                exit(0)
        except Exception as e:
            print(f'Error testing {url}: {str(e)}')
