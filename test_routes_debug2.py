import sys
sys.path.insert(0, '.')
import os
os.environ['DASHBOARD_USER'] = 'admin'
os.environ['DASHBOARD_PASS'] = 'admin123'

from flask import Flask, Response, request
from werkzeug.test import Client

app = Flask(__name__)

DASHBOARD_USER = os.environ.get('DASHBOARD_USER', '').strip()
DASHBOARD_PASS = os.environ.get('DASHBOARD_PASS', '').strip()
_DASHBOARD_AUTH_ENABLED = bool(DASHBOARD_USER and DASHBOARD_PASS)
_AUTH_SAFE_PATHS = ('/health', '/webhook', '/whatsapp/webhook', '/', '/api/chatbot', '/api/v1', '/pos', '/api/v1/store/pos/purchases', '/api/v1/store/pos/products')

@app.before_request
def require_auth_for_dashboard():
    if not _DASHBOARD_AUTH_ENABLED:
        return
    path = request.path.rstrip('/')
    if request.method == 'GET' and request.args.get('hub.mode') == 'subscribe':
        return
    for safe in _AUTH_SAFE_PATHS:
        if path == safe or path.startswith(safe + '/'):
            return
    if path.startswith('/dashboard') or path.startswith('/api'):
        auth = request.authorization
        if not auth or auth.username != DASHBOARD_USER or auth.password != DASHBOARD_PASS:
            return Response('auth required', 401, {'WWW-Authenticate': 'Basic realm="Royal"'})

from routes.store import store_bp
app.register_blueprint(store_bp, url_prefix='/api/v1/store')

client = Client(app, Response)

for path in ['/api/v1/store/pos/purchases', '/api/v1/store/pos/products', '/api/v1/store/products', '/dashboard']:
    resp = client.get(path)
    is_json = resp.data.startswith(b'{')
    is_html = resp.data.startswith(b'<!')
    print(f'{path}: status={resp.status_code}, json={is_json}, html={is_html} ({resp.data[:200]})')
