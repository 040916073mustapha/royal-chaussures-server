#!/usr/bin/env python
"""Test sending a Facebook Messenger reply using the webhook code directly"""
import requests, json, sys

# Replicate the exact logic from webhook_server.py
FB_SYSTEM_USER_TOKEN = "EAASvxCcZCEgkBSNCLaZAvUZAEX48R0Ek2tNAvK50WOKbmiuLifAZANYdwODypZATvvQAebAGEqoMvEyb59q2gHUB5rGbaINRKO8xbJ817s1SuI3CY1y9zt15J2QeYKciUjFtGp1kjZA8jQQDF3vwQdULrrJmnrIarcGPB8AaoK5sLbNZB3nigX7MO9ZC8UXdFHIVqpNWM6Tjz6U8juIKawZAdMuLgbOBDE8YRZCuJk"

def get_page_access_token():
    """الحصول على Page Access Token من System User Token"""
    try:
        url = "https://graph.facebook.com/v20.0/me/accounts?access_token=" + FB_SYSTEM_USER_TOKEN
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if "data" in data and len(data["data"]) > 0:
            for page in data["data"]:
                if "access_token" in page:
                    print("Page:", page.get("name"))
                    print("Token (first 50):", page["access_token"][:50] + "...")
                    return page["access_token"]
    except Exception as e:
        print("Error getting page token:", e)
    return None

# Get page token
page_token = get_page_access_token()
if not page_token:
    print("FAILED to get page token!")
    sys.exit(1)

# Test sending a message
test_sender = "27698473049760867"
url = "https://graph.facebook.com/v20.0/me/messages?access_token=" + page_token
payload = {
    "recipient": {"id": test_sender},
    "message": {"text": "مرحباً بك في Royal Chaussures 👠✨ تم إصلاح نظام الرد التلقائي بنجاح! 🚀"}
}
headers = {"Content-Type": "application/json"}

print("\n=== Sending test message ===")
resp = requests.post(url, json=payload, headers=headers, timeout=15)
result = resp.json()
print(f"Status: {resp.status_code}")
print(json.dumps(result, indent=2, ensure_ascii=False))
