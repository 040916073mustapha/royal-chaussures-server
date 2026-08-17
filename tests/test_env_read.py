#!/usr/bin/env python3
"""Test reading .env directly."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os

_key = os.getenv("ZR_SECRET_KEY", "")
if not _key:
    _key = os.getenv("ZR_API_KEY", "")
if not _key:
    _env_paths = [".env", r"C:\Users\Micro-Tech\.openclaw\workspace-shipment\scripts\.env"]
    for _p in _env_paths:
        if os.path.exists(_p):
            with open(_p, "r", encoding="utf-8") as _f:
                for _line in _f:
                    if _line.startswith("ZR_SECRET_KEY="):
                        _key = _line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
                    if _line.startswith("ZR_API_KEY="):
                        _key = _line.split("=", 1)[1].strip().strip('"').strip("'")
            if _key:
                break

print("Found key:", _key[:15] if _key else "NOT FOUND")
