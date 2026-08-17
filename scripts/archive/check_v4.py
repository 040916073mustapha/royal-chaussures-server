#!/usr/bin/env python3
"""Full dashboard feature check V4."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

s = requests.Session()
s.post("http://localhost:5050/login", data={"username":"admin","password":"***"})

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
    ("Charts canvases", '<canvas' in html),
]
for name, result in checks:
    print(f'{"OK" if result else "MISSING"}: {name}')
print(f"\nTotal: {sum(1 for _,r in checks if r)}/{len(checks)}")
