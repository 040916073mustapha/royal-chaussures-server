#!/usr/bin/env python
"""Check ngrok for Instagram webhook requests"""
import requests, base64, json, re

r = requests.get("http://localhost:4040/api/requests/http", timeout=5)
for x in r.json().get("requests", []):
    dt = requests.get("http://localhost:4040/api/requests/http/" + x["id"], timeout=5).json()
    req = dt.get("request", {})
    ua = str(req.get("headers", {}).get("User-Agent", [""])[0]).lower()
    method = req.get("method", "")
    sc = dt.get("response", {}).get("status_code", "")
    start = dt.get("start", "")

    if "facebook" in ua and method == "POST":
        body = base64.b64decode(req.get("raw", "")).decode("utf-8", errors="replace")
        match = re.search(r'"object"\s*:\s*"(\w+)"', body)
        obj_type = match.group(1) if match else "?"
        print(f"[{start}] {method} -> {sc} | object: {obj_type}")
