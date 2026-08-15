#!/usr/bin/env python
"""Test Facebook Messenger token and API"""
import requests, json

fb_token = "EAASvxCcZCEgkBSNCLaZAvUZAEX48R0Ek2tNAvK50WOKbmiuLifAZANYdwODypZATvvQAebAGEqoMvEyb59q2gHUB5rGbaINRKO8xbJ817s1SuI3CY1y9zt15J2QeYKciUjFtGp1kjZA8jQQDF3vwQdULrrJmnrIarcGPB8AaoK5sLbNZB3nigX7MO9ZC8UXdFHIVqpNWM6Tjz6U8juIKawZAdMuLgbOBDE8YRZCuJk"

# Test 1: /me with token in query
print("=== Test 1: /me with query token ===")
url = "https://graph.facebook.com/v20.0/me?access_token=" + fb_token
resp = requests.get(url, timeout=10)
d = resp.json()
print(f"Status: {resp.status_code}")
print(d)

# Test 2: Get page access tokens
print("\n=== Test 2: /me/accounts ===")
url2 = "https://graph.facebook.com/v20.0/me/accounts?access_token=" + fb_token
resp2 = requests.get(url2, timeout=10)
d2 = resp2.json()
print(f"Status: {resp2.status_code}")
print(json.dumps(d2, indent=2, ensure_ascii=False)[:800])

# If we get a page token, test sending
if "data" in d2 and len(d2["data"]) > 0:
    page = d2["data"][0]
    page_token = page.get("access_token")
    page_name = page.get("name")
    page_id_target = page.get("id")
    print(f"\n✅ Page found: {page_name} (ID: {page_id_target})")
    
    # Test send message to yourself (need a user id to test)
    # Just verify we can call /me/messages
    url3 = f"https://graph.facebook.com/v20.0/{page_id_target}?access_token=" + page_token
    resp3 = requests.get(url3, timeout=10)
    print(f"Page info: {resp3.status_code} - {resp3.text[:200]}")

# Test 3: Send test message to a known sender (from ngrok logs: 27698473049760867)
test_sender = "27698473049760867"
# Try with token in query first
url4 = f"https://graph.facebook.com/v20.0/me/messages?access_token={fb_token}"
payload = {
    "recipient": {"id": test_sender},
    "message": {"text": "مرحباً، هذا رد اختباري من السيرفر للتحقق من عمل الماسنجر ✅"}
}
resp4 = requests.post(url4, json=payload, timeout=10)
result4 = resp4.json()
print(f"\n=== Test Send Message ===")
print(f"Status: {resp4.status_code}")
print(json.dumps(result4, indent=2, ensure_ascii=False))
