#!/usr/bin/env python3
"""Check Dashboard page directly."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

# Login
s = requests.Session()
s.get("http://localhost:5050/login", timeout=10)
s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})
# Get dashboard
r = s.get("http://localhost:5050/", timeout=10)
html = r.text
print(f"URL: {r.url}")
print(f"Length: {len(html)}")
print(f"Is Dashboard: {'managerVars' in html or 'StatsGrid' in html or 'chart.js' in html[:2000]}")
print(f"Contains 'PWA': {'manifest.json' in html}")
print(f"Contains 'Chart.js': {'chart.js' in html.lower()}")
print(f"Contains 'Gold': {'c9a96e' in html.lower()}")
print(f"Contains 'Playfair': {'Playfair' in html}")
print(f"Contains 'btn-gold': {'btn-gold' in html}")
print(f"Contains '<canvas': {'<canvas' in html}")
print(f"Contains 'showToast': {'showToast' in html}")
print(f"Contains 'exportPdf': {'exportPdf' in html}")
print(f"Contains 'beforeinstallprompt': {'beforeinstallprompt' in html}")
print(f"Contains 'Notification': {'Notification' in html}")
print(f"Contains 'install-btn': {'install-btn' in html}")
print(f"Contains 'data-theme': {'data-theme' in html}")
print(f"Contains 'service-worker': {'service-worker' in html}")
