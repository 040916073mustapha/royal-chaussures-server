import requests

endpoints = ['shipments', 'shipping', 'order', 'parcel', 'parcels', 'delivery', 'tracking']
headers = {
    'X-Tenant': 'd2217f31-20f1-43c6-abd4-c420788a63ed',
    'X-Api-Key': 'hoNZBCBMQghSLha9h4KjSFpj558c6PVutJg7x5e0GOQJpGMdNAZsLOW8X39vh7nf',
    'Accept': 'application/json'
}

for ep in endpoints:
    url = f'https://api.zrexpress.app/api/v1/{ep}'
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f'Endpoint /{ep}: {response.status_code}')
        if response.status_code == 200:
            print(f'--- Success on /{ep}! ---')
            break
    except:
        pass
