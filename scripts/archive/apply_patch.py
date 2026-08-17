#!/usr/bin/env python3
# Edit inline - find anchor and insert
import sys

with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'r', encoding='utf-8') as f:
    content = f.read()

anchor = "    return json_utf8(info)\n\n\n@app.route('/api/agent/route-test', methods=['POST'])"
insert_code = """    return json_utf8(info)


@app.route('/api/instagram/inspect', methods=['GET'])
def api_instagram_inspect():
    \"\"\"Advanced Instagram Webhook inspection\"\"\"
    result = {
        "server_url": request.host_url.rstrip('/'),
        "has_fb_token": bool(FB_SYSTEM_USER_TOKEN),
        "has_instagram_token": bool(INSTAGRAM_ACCESS_TOKEN),
        "instagram_business_id": INSTAGRAM_BUSINESS_ID or "not set",
        "checks": []
    }
    if not FB_SYSTEM_USER_TOKEN:
        result["error"] = "FB_SYSTEM_USER_TOKEN not configured"
        return json_utf8(result)
    try:
        app_resp = requests.get(
            "https://graph.facebook.com/v21.0/me",
            params={"fields": "id,name,app_id", "access_token": FB_SYSTEM_USER_TOKEN},
            timeout=10
        ).json()
        result["app_info"] = {"user_id": app_resp.get("id","?"), "name": app_resp.get("name","?"), "app_id": app_resp.get("app_id","?")}
        result["checks"].append({"check": "1. User/App info", "status": "ok", "data": result["app_info"]})
    except Exception as e:
        result["checks"].append({"check": "1. User/App info", "status": "error", "error": _safe_str(e)})
    try:
        pages_resp = requests.get(
            "https://graph.facebook.com/v21.0/me/accounts",
            params={"access_token": FB_SYSTEM_USER_TOKEN, "limit": "10"},
            timeout=10
        ).json()
        pages = pages_resp.get("data", [])
        result["page_count"] = len(pages)
        result["pages"] = []
        for page in pages:
            pid, pname, ptok = page.get("id",""), page.get("name","?"), page.get("access_token","")
            pi = {"id": pid, "name": pname}
            if pid and ptok:
                try:
                    ig_resp = requests.get(
                        f"https://graph.facebook.com/v21.0/{pid}",
                        params={"fields": "instagram_business_account", "access_token": ptok},
                        timeout=10
                    ).json()
                    ig_acct = ig_resp.get("instagram_business_account")
                    pi["has_instagram_linked"] = bool(ig_acct)
                    if ig_acct:
                        pi["instagram_business_id"] = ig_acct.get("id","?")
                except:
                    pi["has_instagram_linked"] = "error"
                try:
                    sub_resp = requests.get(
                        f"https://graph.facebook.com/v21.0/{pid}/subscribed_apps",
                        params={"access_token": ptok},
                        timeout=10
                    ).json()
                    pi["subscribed_apps"] = [s.get("name",s.get("id","?")) for s in sub_resp.get("data",[])]
                    pi["subscribed_count"] = len(sub_resp.get("data",[]))
                except Exception as e:
                    pi["subscribed_error"] = _safe_str(e)[:100]
            result["pages"].append(pi)
        result["checks"].append({"check": "2. Pages & Instagram", "status": "ok", "detail": str(len(pages)) + " pages"})
    except Exception as e:
        result["checks"].append({"check": "2. Pages & Instagram", "status": "error", "error": _safe_str(e)})
    if INSTAGRAM_ACCESS_TOKEN and INSTAGRAM_BUSINESS_ID:
        try:
            verify_resp = requests.get(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}",
                params={"fields": "name,username", "access_token": INSTAGRAM_ACCESS_TOKEN},
                timeout=10
            ).json()
            result["instagram_account_info"] = {
                "name": verify_resp.get("name","?"),
                "username": verify_resp.get("username","?"),
                "token_valid": "error" not in verify_resp
            }
            result["checks"].append({"check": "3. IG Token", "status": "ok" if result["instagram_account_info"]["token_valid"] else "warning"})
        except Exception as e:
            result["checks"].append({"check": "3. IG Token", "status": "error", "error": _safe_str(e)})
        try:
            resp = requests.get(
                f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}",
                params={"access_token": INSTAGRAM_ACCESS_TOKEN, "fields": "id,name"},
                timeout=10
            )
            igc = resp.json()
            result["instagram_api_check"] = {
                "status_code": resp.status_code,
                "response": igc.get("name", igc.get("error",{}).get("message",str(igc)[:200]))
            }
            result["checks"].append({"check": "4. IG API", "status": "ok" if resp.status_code == 200 else "fail"})
        except Exception as e:
            result["checks"].append({"check": "4. IG API", "status": "error", "error": _safe_str(e)})
    result["webhook_callback_url"] = request.host_url.rstrip('/') + "/webhook"
    try:
        app_id = result.get("app_info",{}).get("app_id","")
        if app_id:
            wh_resp = requests.get(
                f"https://graph.facebook.com/v21.0/{app_id}/subscriptions",
                params={"access_token": FB_SYSTEM_USER_TOKEN},
                timeout=10
            ).json()
            subs = wh_resp.get("data",[])
            result["webhook_subs"] = wh_resp
            result["checks"].append({"check": "5. Webhook subs", "status": "ok" if subs else "warning", "count": len(subs)})
    except Exception as e:
        result["checks"].append({"check": "5. Webhook subs", "status": "error", "error": _safe_str(e)})
    passed = sum(1 for c in result["checks"] if c["status"] == "ok")
    failed = sum(1 for c in result["checks"] if c["status"] in ("error","fail"))
    result["summary"] = str(passed) + "/" + str(len(result['checks'])) + " checks passed, " + str(failed) + " failed"
    result["instagram_ready"] = passed == len(result["checks"]) and all(c["status"] != "warning" for c in result["checks"])
    return json_utf8(result)


@app.route('/api/agent/route-test', methods=['POST'])"""

if anchor in content:
    content = content.replace(anchor, insert_code, 1)
    with open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\render_deploy\\server.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS - patch applied")
else:
    print("ERROR - anchor not found. Searching...")
    idx = content.find("return json_utf8(info)")
    if idx >= 0:
        print(f"Found at pos {idx}")
        print(content[idx:idx+200])
