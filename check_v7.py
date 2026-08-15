#!/usr/bin/env python3
"""Dashboard direct check - bypass login issue."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

# Don't overthink - just check the login page HTML content
r = requests.get("http://localhost:5050/login", timeout=10)
html = r.text

# If login page contains the new features, they're in the file
checks = [
    ("PWA manifest in login", "manifest.json" in html),
    ("Chart.js CDN in login", "chart.js" in html.lower()),
    ("html2pdf CDN in login", "html2pdf" in html.lower()),
    ("Gold luxury", "c9a96e" in html.lower()),
    ("Playfair Display", "Playfair" in html),
    ("Dark/Light mode", "data-theme" in html.lower()),
    ("Service Worker", "service-worker" in html.lower()),
    ("PWA install button", "install-btn" in html.lower()),
    ("Toast notifications", "showToast" in html),
    ("PDF export", "exportPdf" in html),
    ("Charts canvases", "<canvas" in html),
    ("Gold buttons", "btn-gold" in html),
]
for name, result in checks:
    print(f'{"OK" if result else "MISSING"}: {name}')
print(f"\nTotal: {sum(1 for _,r in checks if r)}/{len(checks)}")
print(f"\nLogin page HTML length: {len(html)}")
