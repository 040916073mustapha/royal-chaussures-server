# fix_shopify.py - Add Shopify product lookup to server.py
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Shopify env vars and functions after AI_MODEL line
shopify_section = r'''

# Shopify API config
SHOPIFY_STORE = os.getenv("SHOPIFY_STORE", "")
SHOPIFY_CATALOG_TOKEN = os.getenv("SHOPIFY_CATALOG_TOKEN", "")
SHOPIFY_ORDERS_TOKEN = os.getenv("SHOPIFY_ORDERS_TOKEN", "")
SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")
_SHOP_NAME = "Royal Chaussures"


def shopify_api(method="GET", endpoint="products.json", params=None, token_type="catalog"):
    """Make a Shopify Admin API request."""
    token = SHOPIFY_CATALOG_TOKEN if token_type == "catalog" else SHOPIFY_ORDERS_TOKEN
    if not SHOPIFY_STORE or not token:
        return None
    url = f"https://{SHOPIFY_STORE}.myshopify.com/admin/api/{SHOPIFY_API_VERSION}/{endpoint}"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params, timeout=10)
        else:
            resp = requests.post(url, headers=headers, json=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        logger.warning(f"Shopify API {method} {endpoint}: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.error(f"Shopify API error: {_safe_str(e)}")
    return None


def search_shopify_products(query=""):
    """Search products by name/query and return formatted results."""
    params = {"limit": 5, "status": "active"}
    if query:
        params["title"] = query
    data = shopify_api("GET", "products.json", params)
    if not data or "products" not in data:
        return "عذراً، لم أتمكن من جلب المنتجات حالياً. 🛍️"
    products = data["products"]
    if not products:
        return "نعتذر، لا توجد منتجات متاحة تطابق طلبك حالياً. 😊"
    result_lines = ["🛍️ **المنتجات المتوفرة:**\n"]
    for p in products[:3]:
        title = p["title"]
        variants = p.get("variants", [])
        price_min = min(float(v.get("price", 0)) for v in variants) if variants else 0
        price_max = max(float(v.get("price", 0)) for v in variants) if variants else 0
        price_str = f"{int(price_min)} د.ج" if price_min == price_max else f"{int(price_min)} - {int(price_max)} د.ج"
        img_url = (p.get("images") or [{}])[0].get("src", "")
        # Count available stock
        in_stock = sum(1 for v in variants if int(v.get("inventory_quantity", 0)) > 0)
        total_vars = len(variants)
        stock_info = f"✅ متوفر {in_stock} مقاس" if in_stock > 0 else "❌ نفد المخزون"
        result_lines.append(f"• **{title}**")
        result_lines.append(f"  السعر: {price_str}")
        result_lines.append(f"  المخزون: {stock_info} ({in_stock}/{total_vars})")
        if img_url:
            result_lines.append(f"  {img_url}")
        result_lines.append("")
    return "\n".join(result_lines)


def check_product_inventory(product_query, size=None, color=None):
    """Check if a specific product/size/color is in stock."""
    params = {"limit": 5, "status": "active"}
    if product_query:
        params["title"] = product_query
    data = shopify_api("GET", "products.json", params)
    if not data or "products" not in data:
        return None
    for p in data.get("products", []):
        for v in p.get("variants", []):
            v_title = v.get("title", "").lower()
            qty = int(v.get("inventory_quantity", 0))
            match = True
            if size and size.lower() not in v_title:
                match = False
            if color and color.lower() not in v_title:
                match = False
            if match:
                return {
                    "product": p["title"],
                    "variant": v.get("title", ""),
                    "price": v.get("price", "0"),
                    "in_stock": qty > 0,
                    "quantity": qty,
                    "variant_id": v.get("id"),
                    "image": (p.get("images") or [{}])[0].get("src", "")
                }
    return None
'''

# Find the insertion point - after AI_MODEL line
insert_marker = 'AI_MODEL = os.getenv("AI_MODEL", "deepseek-ai/DeepSeek-V4-Flash")'
if insert_marker in content:
    content = content.replace(insert_marker, insert_marker + shopify_section)
    print("SUCCESS: Added Shopify functions!")
else:
    print("FAILED: Could not find insertion point")

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR:", e)
