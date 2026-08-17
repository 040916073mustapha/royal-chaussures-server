# verify_server.py
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()
lines_count = len(content.split('\n'))
print('Lines:', lines_count)
fns = ['search_shopify_products', 'check_product_inventory', 'shopify_api', 'get_fb_page_token', 'send_fb_reply', 'send_ig_reply', 'send_whatsapp_reply', 'process_messaging_entries', 'process_whatsapp_entries']
for fn in fns:
    print(fn + ':', 'YES' if fn in content else 'MISSING!')
envs = ['SHOPIFY_STORE', 'SHOPIFY_CATALOG_TOKEN', 'SHOPIFY_ORDERS_TOKEN', 'AI_SYSTEM_PROMPT', 'INSTAGRAM_ACCESS_TOKEN']
for env in envs:
    marker = 'os.getenv("' + env + '"'
    print(env + ':', 'YES' if marker in content else 'CHECK')
corrupted = sum(1 for l in content.split('\n') if '***' in l)
print('*** corruption:', corrupted)
try:
    compile(content, 'server.py', 'exec')
    print('SYNTAX: 100% OK!')
except SyntaxError as e:
    print('SYNTAX ERROR:', e)
