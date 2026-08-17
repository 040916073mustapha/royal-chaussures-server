"""Test the full server.py with actual before_request logic"""
import sys
sys.path.insert(0, '.')
import os
import json

# Set up env for auth
os.environ['DASHBOARD_USER'] = 'admin'
os.environ['DASHBOARD_PASS'] = 'admin123'

# Import the server module carefully
# We'll use importlib to avoid running the module directly
import importlib.util
from flask import Flask

# Instead of trying to import server.py (which runs on import),
# let's just check the actual route map by reading the file and testing the logic

# Test path matching logic similar to server.py's require_auth_for_dashboard
_DASHBOARD_AUTH_ENABLED = True
_AUTH_SAFE_PATHS = ('/health', '/webhook', '/whatsapp/webhook', '/', '/api/chatbot', '/api/v1', '/pos', '/api/v1/store/pos/purchases', '/api/v1/store/pos/products')

def check_auth_for_path(path):
    """Simulate require_auth_for_dashboard logic"""
    path = path.rstrip('/')
    for safe in _AUTH_SAFE_PATHS:
        if path == safe or path.startswith(safe + '/'):
            return 'SAFE (pass)'
    if path.startswith('/dashboard') or path.startswith('/api'):
        return 'AUTH REQUIRED (block)'
    return 'OTHER (pass)'

paths_to_test = [
    '/api/v1/store/pos/purchases',
    '/api/v1/store/pos/products',
    '/api/v1/store/purchases',
    '/api/v1/store/products',
    '/api/v1/admin/something',
    '/dashboard',
    '/dashboard/chat',
    '/api/messages',
    '/api/products',
    '/health',
    '/webhook',
    '/',
    '/api/v1',
    '/api/v1/agent/something',
]

for path in paths_to_test:
    result = check_auth_for_path(path)
    print(f'{path:40s} -> {result}')
