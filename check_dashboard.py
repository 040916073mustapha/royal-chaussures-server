#!/usr/bin/env python3
"""Check dashboard features."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import requests
r = requests.get("http://localhost:5050/login", timeout=10)
html = r.text
checks = [
    ("PWA manifest", "manifest.json" in html),
    ("Chart.js", "chart.js" in html.lower()),
    ("html2pdf", "html2pdf" in html.lower()),
    ("Gold color (#c9a96e)", "c9a96e" in html.lower()),
    ("Playfair Display font", "Playfair" in html),
    ("Font Awesome", "fontawesome" in html.lower()),
    ("Glassmorphism (rgba backdrop)", "rgba" in html.lower()),
    ("Dark/Light mode", "dark" in html.lower() and "light" in html.lower()),
    ("Service Worker", "service-worker" in html.lower()),
    ("Notification permission", "notification" in html.lower()),
    ("Inter font", "Inter" in html),
]
for name, result in checks:
    icon = "OK" if result else "MISSING"
    print(f"[{icon}] {name}")
print()
print("Total features:", sum(1 for _, r in checks if r), "/", len(checks))
