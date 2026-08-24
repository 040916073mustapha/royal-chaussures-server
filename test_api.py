import json, urllib.request

# Test health
r = urllib.request.urlopen('https://rcagents.space/api/health', timeout=10)
print('Health:', r.read().decode())

# Test register
d = json.dumps({'email':'test@test.com','password':'test123','name':'test'}).encode()
req = urllib.request.Request('https://rcagents.space/api/auth/register', data=d, headers={'Content-Type':'application/json'})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print('Register:', resp.read().decode())
except urllib.error.HTTPError as e:
    print(f'Register error {e.code}:', e.read().decode())

# Test login
d2 = json.dumps({'email':'test@test.com','password':'test123'}).encode()
req2 = urllib.request.Request('https://rcagents.space/api/auth/login', data=d2, headers={'Content-Type':'application/json'})
try:
    resp2 = urllib.request.urlopen(req2, timeout=10)
    print('Login:', resp2.read().decode())
except urllib.error.HTTPError as e:
    print(f'Login error {e.code}:', e.read().decode())
