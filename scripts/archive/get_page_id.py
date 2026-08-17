import requests

# Read FB token from .env
with open(r'C:\Users\Micro-Tech\.openclaw\workspace\.env', 'r') as f:
    content = f.read()

fb_token = ''
for line in content.split('\n'):
    line = line.strip()
    if line.startswith('FB_SYSTEM_USER_TOKEN='):
        fb_token = line.split('=', 1)[1].strip()

print('FB Token length:', len(fb_token))

# Get Facebook Pages
url = 'https://graph.facebook.com/v21.0/me/accounts'
params = {'access_token': fb_token, 'limit': '10'}
resp = requests.get(url, params=params, timeout=15)
data = resp.json()

print('Status:', resp.status_code)
if 'data' in data and len(data['data']) > 0:
    for page in data['data']:
        pid = page.get('id', '?')
        pname = page.get('name', '?')
        print()
        print('=== PAGE FOUND ===')
        print('Page ID:', pid)
        print('Page Name:', pname)
        
        # Check Instagram
        ig_url = f'https://graph.facebook.com/v21.0/{pid}'
        ig_params = {
            'fields': 'instagram_business_account',
            'access_token': page.get('access_token', '')
        }
        ig_resp = requests.get(ig_url, params=ig_params, timeout=10)
        ig_data = ig_resp.json()
        ig_biz = ig_data.get('instagram_business_account')
        if ig_biz:
            print('Instagram Business ID:', ig_biz.get('id', '?'))
        else:
            print('No Instagram linked')
        
        print()
        print('ADD TO RENDER ENV VARS:')
        print('FB_PAGE_ID=' + pid)
        print('INSTAGRAM_BUSINESS_ID=' + (ig_biz.get('id', '') if ig_biz else '(not found)'))
        print()
else:
    err = data.get('error', {}).get('message', str(data)[:300])
    print('No pages found or error:', err)
