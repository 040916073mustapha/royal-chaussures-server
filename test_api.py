import requests, json, time

API_KEY = 'VrXFwDAmosJPXjnmyECE6TRHWycyXKbQ'
headers = {'Authorization': 'Bearer ' + API_KEY, 'Content-Type': 'application/json'}

print('Test 1: DeepSeek-V4-Flash')
t1 = time.time()
r = requests.post('https://api.deepinfra.com/v1/openai/chat/completions',
    json={
        'model': 'deepseek-ai/DeepSeek-V4-Flash',
        'messages': [{'role': 'user', 'content': 'قول مرحبا'}],
    },
    headers=headers, timeout=15)
t2 = time.time()
print(f'  Status: {r.status_code} in {(t2-t1)*1000:.0f}ms')
if r.status_code == 200:
    data = r.json()
    reply = data['choices'][0]['message']['content']
    print(f'  Reply: {reply[:200]}')
else:
    print(f'  Error: {r.text[:300]}')

print()
print('Test 2: GPT-4o-mini (vision)')
t3 = time.time()
r2 = requests.post('https://api.deepinfra.com/v1/openai/chat/completions',
    json={
        'model': 'openai/gpt-4o-mini',
        'messages': [{'role': 'user', 'content': 'قول مرحبا بالعربية'}],
    },
    headers=headers, timeout=15)
t4 = time.time()
print(f'  Status: {r2.status_code} in {(t4-t3)*1000:.0f}ms')
if r2.status_code == 200:
    data2 = r2.json()
    reply2 = data2['choices'][0]['message']['content']
    print(f'  Reply: {reply2[:200]}')
else:
    print(f'  Error: {r2.text[:300]}')

print()
print('Test 3: Vision with image URL')
t5 = time.time()
payload3 = {
    'model': 'openai/gpt-4o-mini',
    'messages': [{
        'role': 'user',
        'content': [
            {'type': 'text', 'text': 'شنو هذا المنتج؟ وصفه بالعربية'},
            {'type': 'image_url', 'image_url': {'url': 'https://cdn.shopify.com/s/files/1/0781/8380/5548/files/escarpin-royal-01.jpg', 'detail': 'high'}}
        ]
    }],
}
r3 = requests.post('https://api.deepinfra.com/v1/openai/chat/completions',
    json=payload3, headers=headers, timeout=15)
t6 = time.time()
print(f'  Status: {r3.status_code} in {(t6-t5)*1000:.0f}ms')
if r3.status_code == 200:
    reply3 = r3.json()['choices'][0]['message']['content']
    print(f'  Reply: {reply3[:200]}')
else:
    print(f'  Error: {r3.text[:300]}')
