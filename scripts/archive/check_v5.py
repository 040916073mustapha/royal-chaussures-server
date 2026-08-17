#!/usr/bin/env python3
"""Final check v5 - with proper session."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

s = requests.Session()
# Step 1: Get login page first
s.get("http://localhost:5050/login", timeout=10)
# Step 2: Post login
r = s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})
# Step 3: Get dashboard
r = s.get("http://localhost:5050/", timeout=10)
html = r.text

checks = [
    ("PWA manifest", "manifest.json" in html),
    ("Chart.js CDN", "chart.js" in html.lower()),
    ("html2pdf CDN", "html2pdf" in html.lower()),
    ("Gold luxury (#c9a96e)", "c9a96e" in html.lower()),
    ("Playfair Display font", "Playfair" in html),
    ("Inter font", "Inter" in html),
    ("Font Awesome 6", "fontawesome" in html.lower()),
    ("Dark/Light mode toggle", "data-theme" in html.lower()),
    ("Service Worker", "service-worker" in html.lower()),
    ("Notification permission", "Notification" in html),
    ("PWA install button", "install-btn" in html.lower()),
    ("Toast notifications", "showToast" in html),
    ("PDF export function", "exportPdf" in html),
    ("ZR Express status", "ZR" in html and "Express" in html),
    ("Charts canvases", "<canvas" in html),
    ("Gold gradient buttons", "btn-gold" in html),
    ("Glass section", "glass-section" in html.lower()),
]
print(f"URL after login: {r.url}")
print(f"Login success: {'Dashboard' in html[:500] or 'لوحة' in html[:500]}")
print()
for name, result in checks:
    print(f'{"OK" if result else "MISSING"}: {name}')
print(f"\nTotal: {sum(1 for _,r in checks if r)}/{len(checks)}")
