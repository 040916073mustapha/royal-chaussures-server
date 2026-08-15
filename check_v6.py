#!/usr/bin/env python3
"""Final check v6."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

s = requests.Session()
s.get("http://localhost:5050/login", timeout=10)
s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})
r = s.get("http://localhost:5050/", timeout=10)
html = r.text
is_logged_in = "لوحة" in html[:500] or "Dashboard" in html[:500] or "Charts" in html[:500] or "<canvas" in html
print(f"Logged in: {is_logged_in}")
print(f"HTML length: {len(html)}")
if not is_logged_in:
    print(f"First 100 chars: {html[:100]}")
else:
    checks = [
        ("PWA manifest", "manifest.json" in html),
        ("Chart.js CDN", "chart.js" in html.lower()),
        ("html2pdf CDN", "html2pdf" in html.lower()),
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
