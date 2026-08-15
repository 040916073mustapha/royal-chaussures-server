#!/usr/bin/env python
"""Test OpenClaw Gateway API"""
import requests, json, sys

token = "40bc9bc11cee10397ec403a219f89274eac3682aa0a8a793"
url = "http://127.0.0.1:18789/v1/chat/completions"

models = ["openclaw", "openclaw/default", "openclaw/louve"]

for model in models:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "قول مرحبا في 4 كلمات بالدارجة"}]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=30)
        data = r.json()
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            print(f"OK {model}: {r.status_code} -> {reply[:150]}")
        else:
            print(f"FAIL {model}: {r.status_code} -> {json.dumps(data, ensure_ascii=False)[:200]}")
    except Exception as e:
        print(f"ERR {model}: Error - {e}")
