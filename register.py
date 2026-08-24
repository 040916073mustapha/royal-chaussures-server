import json, urllib.request

payload = json.dumps({"email":"admin@royalchaussures.com","password":"Royal2026!","name":"Mustapha"}).encode()
req = urllib.request.Request("https://rcagents.space/api/auth/register", data=payload, headers={"Content-Type":"application/json"})
try:
    resp = urllib.request.urlopen(req, timeout=10)
    print("RESULT:", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"ERROR {e.code}:", e.read().decode())
