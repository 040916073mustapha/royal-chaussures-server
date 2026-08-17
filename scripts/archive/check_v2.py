#!/usr/bin/env python3
"""Full dashboard feature check."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests

r = requests.get("http://localhost:5050/login", timeout=10)
html = r.text
checks = [
    ("PWA manifest", "manifest.json" in html),
    ("Chart.js CDN", "chart.js" in html.lower()),
    ("html2pdf CDN", "html2pdf" in html.lower()),
    ("Gold color (luxury)", "#c9a96e" in html.lower() or "gold" in html.lower()),
    ("Playfair Display font", "Playfair" in html),
    ("Inter font", "Inter" in html),
    ("Font Awesome 6", "fontawesome" in html.lower()),
    ("Glassmorphism effect", "backdrop-filter" in html.lower()),
    ("Dark/Light mode toggle", "data-theme" in html.lower()),
    ("Service Worker", "service-worker" in html.lower()),
    ("Notification permission", "Notification" in html),
    ("PWA install button", "install-btn" in html.lower() or "beforeinstallprompt" in html.lower()),
    ("Toast notifications", "showToast" in html or "toast" in html.lower()),
    ("PDF export function", "exportPdf" in html or "html2pdf" in html.lower()),
]
for name, result in checks:
    print(f'{"OK" if result else "MISSING"}: {name}')
print(f"\nTotal: {sum(1 for _,r in checks if r)}/{len(checks)}")
