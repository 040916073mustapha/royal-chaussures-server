#!/usr/bin/env python3
"""Test ZR shipment from Dashboard API v2."""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import json

session = requests.Session()

# Login
login = session.post(
    "http://localhost:5050/login",
    data={"username": "admin", "password": "RoyalChaussures2026!haussures2026!"},
    allow_redirects=False
)
print("Login:", login.status_code)
print("Cookie:", dict(session.cookies))

# Stats
stats = session.get("http://localhost:5050/api/stats", timeout=10)
print("Stats:", stats.status_code)
if stats.status_code == 200:
    print(json.dumps(stats.json(), indent=2, ensure_ascii=False))
else:
    print("Body:", stats.text[:200])
    # Try following redirect
    stats2 = session.get("http://localhost:5050/api/stats", allow_redirects=True, timeout=10)
    print("Stats2:", stats2.status_code)
    print("Body2:", stats2.text[:200])
