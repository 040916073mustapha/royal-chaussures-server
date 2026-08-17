import urllib.request, urllib.error, json

FB_SYSTEM_USER_TOKEN = "EAASvxCcZCEgkBSNCLaZAvUZAEX48R0Ek2tNAvK50WOKbmiuLifAZANYdwODypZATvvQAebAGEqoMvEyb59q2gHUB5rGbaINRKO8xbJ817s1SuI3CY1y9zt15J2QeYKciUjFtGp1kjZA8jQQDF3vwQdULrrJmnrIarcGPB8AaoK5sLbNZB3nigX7MO9ZC8UXdFHIVqpNWM6Tjz6U8juIKawZAdMuLgbOBDE8YRZCuJk"

def fb_api(path, params=None):
    url = f"https://graph.facebook.com/v18.0/{path}?access_token={FB_SYSTEM_USER_TOKEN}"
    if params:
        url += "&" + "&".join(f"{k}={v}" for k,v in params.items())
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "body": e.read().decode()[:1000]}
    except Exception as e:
        return {"error": str(e)}

# Get page first
pages = fb_api("me/accounts")
page_id = pages["data"][0]["id"]
page_token = pages["data"][0]["access_token"]

# Check the App's webhook config
print("=" * 60)
print("=== App Webhook Subscriptions (App level) ===")
app_id = "1319156913738249"
app_token = FB_SYSTEM_USER_TOKEN  # Need app token ideally

# API to check app subscriptions
subs = fb_api(f"{app_id}/subscriptions")
print(json.dumps(subs, indent=2, ensure_ascii=False)[:1500])

# Check callback URL
print("\n" + "=" * 60)
print("=== Page Subscribed Apps with All Fields ===")
apps_detail = fb_api(f"{page_id}/subscribed_apps?fields=id,name,subscribed_fields, callback_url")
print(json.dumps(apps_detail, indent=2, ensure_ascii=False)[:1500])

# Test: Send a subscribe command to force callback URL registration
print("\n" + "=" * 60)
print("=== Subscribing app to page (re-register webhook) ===")
import urllib.parse
data = urllib.parse.urlencode({
    "subscribed_fields": "messages,message_reads,messaging_optins,messaging_postbacks,messaging_referrals"
}).encode()
req = urllib.request.Request(
    f"https://graph.facebook.com/v18.0/{page_id}/subscribed_apps?access_token={page_token}",
    data=data,
    method="POST"
)
try:
    resp = urllib.request.urlopen(req, timeout=15)
    print(f"Status: {resp.status}")
    print(resp.read().decode()[:500])
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Error {e.code}: {body[:800]}")

# Send actual test webhook event from Meta test tool
print("\n" + "=" * 60)
print("✅ Check List for Meta Dashboard:")
print()
print("1. GO TO: https://developers.facebook.com/apps/1319156913738249/")
print("2. Messenger → Settings → Webhooks")
print("3. Verify Callback URL:")
print("   URL: https://royal-chaussures-server.onrender.com/webhook")
print("   Verify Token: ROYAL-ROYAL-CH2026")
print()
print("4. OR WhatsApp → Configuration → Webhook URLs")
print("   URL: https://royal-chaussures-server.onrender.com/whatsapp/webhook")
print("   Verify Token: ROYAL-ROYAL-CH2026")
