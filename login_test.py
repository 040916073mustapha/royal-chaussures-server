#!/usr/bin/env python3
"""Test login with debug."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import requests

s = requests.Session()
r = s.post("http://localhost:5050/login", data={"username":"admin","password":"RoyalChaussures2026!"})
print("URL:", r.url)
print("Status:", r.status_code)
print("Cookies:", dict(s.cookies))
print("Text contains 'تسجيل':", "تسجيل" in r.text)
print("Text contains 'Dashboard':", "Dashboard" in r.text)
print("Text contains 'error':", "error" in r.text)
print("Text[200:400]:", repr(r.text[200:400]))

# If login page still, check for error message
if "غير صحيحة" in r.text:
    print("ERROR: Password or username incorrect!")
elif "Dashboard" in r.text:
    print("SUCCESS: Logged in!")
