#!/usr/bin/env python3
"""Test what /dashboard/agents actually returns from Flask"""
import sys, os
sys.path.insert(0, 'C:\\Users\\Micro-Tech\\.openclaw\\workspace')

# Set minimal env to start Flask without DB
os.environ['AI_API_KEY'] = 'test'
os.environ['AI_API_URL'] = 'http://localhost:9999'

from server import app

with app.test_client() as client:
    resp = client.get('/dashboard/agents', follow_redirects=False)
    print(f'Status: {resp.status_code}')
    print(f'Location header: {resp.headers.get("Location", "none")}')
    print(f'Content-Type: {resp.content_type}')
    print(f'Content-Length: {resp.content_length}')
    body = resp.get_data(as_text=True)
    
    # Check what template was actually rendered
    if '<title>RC Agents — Agent' in body:
        print('✅ Rendered: agents_dashboard.html')
    elif 'ONE BRAIN' in body or 'dashboard_base' in body:
        print('Rendered: dashboard_base.html based template')
    elif 'landing' in body.lower() or 'Get Started' in body:
        print('❌ Rendered: landing.html!')
    elif 'Authentication required' in body:
        print('❌ Auth required (401)')
    else:
        print(f'Unknown template. First 500 chars:')
        print(body[:500])
    
    print(f'\nBody length: {len(body)} bytes')
    print(f'Status: {resp.status_code}')
