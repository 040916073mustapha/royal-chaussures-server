#!/usr/bin/env python3
"""Test all dashboard routes"""
import sys, os
sys.path.insert(0, 'C:\\Users\\Micro-Tech\\.openclaw\\workspace')
os.environ['AI_API_KEY'] = 'sk-test'
os.environ['AI_API_URL'] = 'http://localhost:9999'

from server import app
with app.test_client() as client:
    results = []
    for test_path in [
        '/dashboard', '/dashboard/', '/dashboard/agents', '/dashboard/orders',
        '/dashboard/products', '/dashboard/clients', '/dashboard/settings',
        '/dashboard/marketing', '/dashboard/inventory', '/dashboard/chat',
        '/dashboard/tracking', '/dashboard/shipments', '/dashboard/auto-ship',
        '/dashboard/constellation', '/dashboard/analytics'
    ]:
        resp = client.get(test_path, follow_redirects=False)
        size = len(resp.get_data())
        ok = 'OK' if resp.status_code == 200 and size > 1000 else ('WARN' if resp.status_code == 200 else 'FAIL')
        results.append((ok, test_path, resp.status_code, size))
    
    all_ok = all(r[0] == 'OK' for r in results)
    for ok, path, code, size in results:
        symbol = {'OK': 'PASS', 'WARN': 'WARN', 'FAIL': 'FAIL'}[ok]
        print(f'{symbol}: {path} -> {code} ({size} bytes)')
    print(f'\nResult: {len(results)}/{len(results)} - {"ALL OK" if all_ok else "SOME FAILED"}')
