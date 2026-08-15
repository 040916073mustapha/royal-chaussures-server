#!/usr/bin/env python
"""Test all Meta tokens"""
import requests, json, sys

tokens = {
    "WhatsApp": "EAApLUGZCmWU8BSJ8Ecxnr24deqKmFwm9Sh3AdDZBKFFvWPJr1nAzS7rcN918dbeuQ5ILpFTXg5gyiKt4JejBDNzojSKZCWVBgeuYrGOJ382OelqKa77RDbFbtMMBDhOfbF4JnpgepwIdQMrTMrPkKaXfy4d0PpmuSMpo9fTjRm9usqoMVGnmxyciPEPicjuApPMQyGIvpiZCQasOZBKMcqhwR65C1OxVsH8IR",
    "FB/IG": "EAASvxCcZCEgkBSNCLaZAvUZAEX48R0Ek2tNAvK50WOKbmiuLifAZANYdwODypZATvvQAebAGEqoMvEyb59q2gHUB5rGbaINRKO8xbJ817s1SuI3CY1y9zt15J2QeYKciUjFtGp1kjZA8jQQDF3vwQdULrrJmnrIarcGPB8AaoK5sLbNZB3nigX7MO9ZC8UXdFHIVqpNWM6Tjz6U8juIKawZAdMuLgbOBDE8YRZCuJk"
}

for name, token in tokens.items():
    print(f"=== {name} Token ===")
    url = "https://graph.facebook.com/v21.0/debug_token?input_token=" + token
    headers = {"Authorization": "Bearer " + token}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json().get("data", {})
        print(f"  Status: {resp.status_code}")
        print(f"  Valid: {data.get('is_valid', 'N/A')}")
        print(f"  Type: {data.get('type', 'N/A')}")
        print(f"  App: {data.get('application', 'N/A')}")
        print(f"  User ID: {data.get('user_id', 'N/A')}")
        print(f"  Scopes: {data.get('scopes', [])}")
        print(f"  Expires at: {data.get('expires_at', 'N/A')}")
        if data.get("expires_at") and isinstance(data.get("expires_at"), int):
            from datetime import datetime
            print(f"  Expiry date: {datetime.fromtimestamp(data['expires_at'])}")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()

# Test WhatsApp API
print("=== WhatsApp API Test ===")
wa_token = tokens["WhatsApp"]
phone_id = "1212786725251029"
url = f"https://graph.facebook.com/v21.0/{phone_id}"
headers = {"Authorization": "Bearer " + wa_token}
resp = requests.get(url, headers=headers, timeout=10)
data = resp.json()
print(f"  Status: {resp.status_code}")
if "display_phone_number" in data:
    print(f"  Phone: {data['display_phone_number']}")
    print(f"  Verified: {data.get('code_verification_status', 'N/A')}")
    print(f"  Quality: {data.get('quality_rating', 'N/A')}")
    print(f"  Webhook URL: {data.get('webhook_configuration', {}).get('application', 'N/A')}")
else:
    print(f"  Error: {json.dumps(data, ensure_ascii=False)[:300]}")

# Test FB Page API
print()
print("=== Facebook Page API Test ===")
fb_token = tokens["FB/IG"]
url = "https://graph.facebook.com/v20.0/me"
headers = {"Authorization": "Bearer " + fb_token}
resp = requests.get(url, headers=headers, timeout=10)
data = resp.json()
print(f"  Status: {resp.status_code}")
if "name" in data:
    print(f"  Page name: {data['name']}")
    print(f"  Page ID: {data.get('id', 'N/A')}")
else:
    print(f"  Error: {json.dumps(data, ensure_ascii=False)[:300]}")
