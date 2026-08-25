#!/usr/bin/env python3
"""Check all dashboard routes in server.py"""
import re
lines = open('C:\\Users\\Micro-Tech\\.openclaw\\workspace\\server.py', 'r', encoding='utf-8').readlines()
routes = []
for i,l in enumerate(lines):
    m = re.search(r"@app\.route\('([^']+)'", l)
    if m:
        routes.append(m.group(1))

dash_routes = [r for r in routes if 'dashboard' in r]
print('Dashboard routes found:')
for r in sorted(dash_routes):
    print(f'  {r}')

expected = ['/dashboard', '/dashboard/', '/dashboard/agents', '/dashboard/analytics',
            '/dashboard/auto-ship', '/dashboard/chat', '/dashboard/clients',
            '/dashboard/inventory', '/dashboard/login', '/dashboard/marketing',
            '/dashboard/orders', '/dashboard/products', '/dashboard/settings',
            '/dashboard/tracking']
for e in expected:
    if e not in dash_routes:
        print(f'  MISSING: {e}')

dash0 = [r for r in dash_routes if r == '/dashboard']
print(f'\n/dashboard count: {len(dash0)} (should be 1)')

api_routes = [r for r in routes if 'agent' in r or 'campaign' in r or 'analytics' in r or 'engagement' in r]
print(f'\nAgent API routes ({len(api_routes)}):')
for r in sorted(api_routes):
    print(f'  {r}')
