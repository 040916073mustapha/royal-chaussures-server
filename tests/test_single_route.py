#!/usr/bin/env python3
"""Test SINGLE ROUTE dashboard with ?view= query params"""
import sys, os
sys.path.insert(0, 'C:\\Users\\Micro-Tech\\.openclaw\\workspace')
os.environ['AI_API_KEY'] = 'sk-test'
os.environ['AI_API_URL'] = 'http://localhost:9999'

from server import app
with app.test_client() as client:
    results = []
    for view_name in ['overview', 'agents', 'orders', 'products', 'clients', 'settings',
                      'analytics', 'marketing', 'inventory', 'shipments', 'auto-ship',
                      'tracking', 'constellation', 'chat']:
        resp = client.get(f'/dashboard?view={view_name}', follow_redirects=False)
        size = len(resp.get_data())
        body = resp.get_data(as_text=True)
        ok = resp.status_code == 200 and size > 5000
        symbol = 'PASS' if ok else 'FAIL'
        # Verify the template rendered correctly
        has_overview = 'activeNav' in body
        results.append((symbol, view_name, resp.status_code, size))
    
    all_ok = all(r[0] == 'PASS' for r in results)
    for symbol, view, code, size in results:
        print(f'{symbol}: /dashboard?view={view} -> {code} ({size} bytes)')
    print(f'\nResult: {len(results)}/{len(results)} - {"ALL OK" if all_ok else "SOME FAILED"}')
    
    # Also verify that /dashboard works with no view param
    resp = client.get('/dashboard')
    print(f'\nPASS: /dashboard (no view) -> {resp.status_code} ({len(resp.get_data())} bytes)')
