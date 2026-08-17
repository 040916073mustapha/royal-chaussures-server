import urllib.request, urllib.error, json, sys
sys.stdout.reconfigure(encoding='utf-8')

FB_SYSTEM_USER_TOKEN = "EAASvxCcZCEgkBSNCLaZAvUZAEX48R0Ek2tNAvK50WOKbmiuLifAZANYdwODypZATvvQAebAGEqoMvEyb59q2gHUB5rGbaINRKO8xbJ817s1SuI3CY1y9zt15J2QeYKciUjFtGp1kjZA8jQQDF3vwQdULrrJmnrIarcGPB8AaoK5sLbNZB3nigX7MO9ZC8UXdFHIVqpNWM6Tjz6U8juIKawZAdMuLgbOBDE8YRZCuJk"

def fb_api(path, token=None):
    url = f"https://graph.facebook.com/v18.0/{path}"
    if token:
        url += f"?access_token={token}"
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:500]}
    except Exception as e:
        return {"error": str(e)}

# Step 1: Get page access token
print("=== Getting Page Access Token ===")
pages = fb_api("me/accounts", FB_SYSTEM_USER_TOKEN)
print(json.dumps(pages, indent=2, ensure_ascii=False)[:800])

if "data" in pages and pages["data"]:
    page = pages["data"][0]
    page_id = page["id"]
    page_name = page["name"]
    page_token = page["access_token"]
    print(f"\n✅ Page: {page_name} (ID: {page_id})")
    
    # Step 2: Check subscribed apps
    print("\n=== Subscribed Apps ===")
    apps = fb_api(f"{page_id}/subscribed_apps", page_token)
    print(json.dumps(apps, indent=2, ensure_ascii=False)[:800])
    
    # Step 3: Send test message to webhook
    print("\n=== Test Webhook POST ===")
    test_data = {
        "object": "page",
        "entry": [{
            "id": page_id,
            "time": 1720000000,
            "messaging": [{
                "sender": {"id": "test"},
                "recipient": {"id": page_id},
                "timestamp": 1720000000,
                "message": {"text": "Test from Louve 🤖"}
            }]
        }]
    }
    
    # Send to Render
    import urllib.request
    data_bytes = json.dumps(test_data).encode('utf-8')
    req = urllib.request.Request(
        "https://royal-chaussures-server.onrender.com/webhook",
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        print(f"Webhook test response: {resp.status}")
        print(resp.read().decode()[:300])
    except Exception as e:
        print(f"Webhook test error: {e}")
else:
    print("\n❌ No pages found or token expired")
    # Try to debug token
    print("\n=== Token Debug ===")
    me = fb_api("me", FB_SYSTEM_USER_TOKEN)
    print(json.dumps(me, indent=2, ensure_ascii=False)[:500])
