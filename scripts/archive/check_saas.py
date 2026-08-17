# check_saas.py
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('server.py', 'r', encoding='utf-8') as f:
    c = f.read()
print('Lines:', len(c.split('\n')))
items = [
    ('init_db', 'init_db()'),
    ('Orders table', 'CREATE TABLE IF NOT EXISTS orders'),
    ('Clients table', 'CREATE TABLE IF NOT EXISTS clients'),
    ('sync_shopify_orders', 'def sync_shopify_orders'),
    ('get_zr_shipments', 'def get_zr_shipments'),
    ('Stats API', 'def api_stats'),
    ('Orders API', 'def api_orders'),
    ('Update Status', 'def api_update_status'),
    ('Products API', 'def api_products'),
    ('Clients API', 'def api_clients'),
    ('Shipments API', 'def api_shipments'),
    ('Dashboard route', "app.route('/dashboard')"),
    ('Dashboard orders', "app.route('/dashboard/orders')"),
    ('Dashboard products', "/dashboard/products"),
    ('Dashboard clients', "/dashboard/clients"),
    ('Dashboard settings', "/dashboard/settings"),
    ('AI generate', 'def generate_ai_reply'),
    ('Webhook', 'def webhook()'),
    ('FB Messenger', 'def send_fb_reply'),
    ('Instagram', 'def send_ig_reply'),
    ('WhatsApp', 'def send_whatsapp_reply'),
]
all_ok = True
for name, pattern in items:
    ok = pattern in c
    print(f'  {name}: {chr(10004) if ok else chr(10060)}')
    if not ok:
        all_ok = False
print(f'\nOverall: {chr(9989) if all_ok else chr(10060)}')
