import sys
sys.path.insert(0, '.')
from flask import Flask, jsonify, Response

app = Flask(__name__)

from routes.store import store_bp
app.register_blueprint(store_bp, url_prefix='/api/v1/store')

# Add same route as server.py
@app.route('/api/v1/store/pos/purchases', methods=['GET'])
def api_pos_list_purchases():
    return jsonify({'success': True, 'purchases': []})

@app.route('/api/v1/store/pos/purchases', methods=['POST'])
def api_pos_record_purchase():
    return jsonify({'purchase': {'id': 1}})

@app.route('/api/v1/store/pos/products')
def api_pos_products():
    return jsonify({'success': True, 'products': []})

from werkzeug.test import Client
client = Client(app, Response)

# Test each route
for path in ['/api/v1/store/pos/purchases', '/api/v1/store/pos/products', '/api/v1/store/purchases', '/api/v1/store/pos']:
    resp = client.get(path)
    is_json = resp.data.startswith(b"{")
    print(f'{path}: status={resp.status_code}, json={is_json} ({resp.data[:200]})')
