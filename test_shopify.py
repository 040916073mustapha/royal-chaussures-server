# test_shopify.py
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

# Only import what we need without running the server
with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract just the Shopify functions and required imports
shopify_code = []
capture = False
for line in lines:
    if 'def shopify_api' in line or 'def search_shopify_products' in line or 'def check_product_inventory' in line:
        capture = True
        indent = len(line) - len(line.lstrip())
    if capture:
        shopify_code.append(line)
        if line.strip() == '' and len(shopify_code) > 2:
            cur_indent = len(line) - len(line.lstrip())
            if cur_indent <= indent and line.strip():
                shopify_code = shopify_code[:-1]
                break
        # Stop at next def or if we have empty line after block
        if line.strip().startswith('def ') and len(shopify_code) > 1:
            shopify_code = shopify_code[:-1]
            break

shopify_src = ''.join(shopify_code)
print("=== Shopify functions extracted ===")
print(shopify_src[:200])
