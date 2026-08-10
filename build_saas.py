import sys, os, json, sqlite3, threading, time, requests
sys.stdout.reconfigure(encoding='utf-8')

# ===== Read current server.py =====
with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ===== Find insertion points =====
# 1. After AI_MODEL line -> insert DB engine
# 2. Before "# --- Pages" line -> insert API routes

# ===== PART 1: SaaS Engine (DB + sync) =====
engine_code = """

# ==================== SaaS DASHBOARD ENGINE ====================
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_orders.db")


def init_db():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shopify_order_id TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            wilaya TEXT,
            municipality TEXT,
            product TEXT,
            variant TEXT,
            quantity INTEGER DEFAULT 1,
            total_price REAL DEFAULT 0,
            status TEXT DEFAULT 'Nouveau',
            delivery_method TEXT DEFAULT 'Home',
            delivery_fee REAL DEFAULT 0,
            source TEXT DEFAULT 'Shopify',
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT UNIQUE,
            wilaya TEXT,
            municipality TEXT,
            total_orders INTEGER DEFAULT 1,
            total_spent REAL DEFAULT 0,
            last_order_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def upsert_order_from_shopify(order_data):
    try:
        oid = str(order_data.get("id", ""))
        if not oid:
            return
        customer = order_data.get("customer", {}) or {}
        name = " ".join(filter(None, [customer.get("first_name", ""), customer.get("last_name", "")]))
        addr = customer.get("default_address", {}) or {}
        phone = customer.get("phone", "") or addr.get("phone", "")
        shipping = order_data.get("shipping_address", {}) or {}
        wilaya = shipping.get("province", "")
        city = shipping.get("city", "")
        total = float(order_data.get("total_price", 0))
        items = order_data.get("line_items", [])
        product = items[0].get("title", "") if items else ""
        variant = items[0].get("variant_title", "") if items else ""
        
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM orders WHERE shopify_order_id = ?", (oid,))
        if c.fetchone():
            c.execute("UPDATE orders SET status=?, total_price=?, updated_at=datetime('now') WHERE shopify_order_id=?", ("Confirme" if order_data.get("financial_status") == "paid" else "Nouveau", total, oid))
        else:
            c.execute("INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?)", (oid, name, phone, wilaya, city, product, variant, total))
            if phone:
                c.execute("SELECT id FROM clients WHERE phone=?", (phone,))
                if c.fetchone():
                    c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime('now') WHERE phone=?", (total, phone))
                else:
                    c.execute("INSERT INTO clients (name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,1,?,datetime('now'))", (name, phone, wilaya, city, total))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"upsert error: {_safe_str(e)}")


def sync_shopify_orders():
    try:
        data = shopify_api("GET", "orders.json", {"status": "any", "limit": 50}, token_type="orders")
        if data and "orders" in data:
            for o in data["orders"]:
                upsert_order_from_shopify(o)
            logger.info(f"Synced {len(data['orders'])} orders")
    except Exception as e:
        logger.error(f"sync error: {_safe_str(e)}")


def get_zr_shipments():
    zr_key = os.getenv("ZR_API_KEY", "")
    zr_url = os.getenv("ZR_BASE_URL", "")
    zr_tenant = os.getenv("ZR_TENANT_ID", "")
    if not zr_key or not zr_url:
        return []
    try:
        url = f"{zr_url}/tenant/{zr_tenant}/parcels?page=1&limit=20"
        headers = {"x-api-key": zr_key, "Content-Type": "application/json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("data", data.get("parcels", []))[:20]
    except Exception as e:
        logger.error(f"ZR error: {_safe_str(e)}")
    return []


init_db()
threading.Thread(target=sync_shopify_orders, daemon=True).start()
"""

# Insert after SHOPIFY_API_VERSION line
marker1 = 'SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")'
if marker1 in content:
    content = content.replace(marker1, marker1 + '\n' + engine_code)
    print("PART 1: SaaS Engine added!")
else:
    print("PART 1 FAILED!")

# ===== PART 2: API + Dashboard Routes =====
# Find the Pages section
api_routes = """

# ==================== SaaS API + DASHBOARD ====================

@app.before_request
def _maybe_sync():
    now = time.time()
    if not hasattr(_maybe_sync, "_last_sync"):
        _maybe_sync._last_sync = 0
    if now - _maybe_sync._last_sync > 120:
        _maybe_sync._last_sync = now
        threading.Thread(target=sync_shopify_orders, daemon=True).start()


# --- API Stats ---
@app.route('/api/stats')
def api_stats():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Confirme'")
    confirmed = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders")
    revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Livre'")
    delivered = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Nouveau'")
    pending = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT customer_phone) FROM orders WHERE customer_phone != ''")
    clients_count = c.fetchone()[0]
    conn.close()
    return json_utf8({"total_orders": total, "confirmed": confirmed, "revenue": round(revenue, 2), "delivered": delivered, "pending": pending, "clients_count": clients_count, "delivery_rate": round((delivered/total*100) if total else 0, 1)})


# --- API Orders ---
@app.route('/api/orders')
def api_orders():
    status_f = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    q = "SELECT id, shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, quantity, total_price, status, delivery_method, created_at FROM orders WHERE 1=1"
    p = []
    if status_f:
        q += " AND status=?"
        p.append(status_f)
    if search:
        q += " AND (customer_name LIKE ? OR customer_phone LIKE ? OR product LIKE ?)"
        s = f"%{search}%"
        p += [s, s, s]
    q += " ORDER BY created_at DESC LIMIT 100"
    c.execute(q, p)
    rows = c.fetchall()
    conn.close()
    return json_utf8({"orders": [{"id": r[0], "shopify_id": r[1], "customer": r[2], "phone": r[3], "wilaya": r[4], "municipality": r[5], "product": r[6], "variant": r[7], "qty": r[8], "total": r[9], "status": r[10], "delivery": r[11], "date": r[12]} for r in rows]})


# --- API Update Order Status ---
@app.route('/api/orders/<int:oid>/status', methods=['PUT'])
def api_update_status(oid):
    data = request.get_json(silent=True) or {}
    ns = data.get("status", "")
    if ns not in ("Nouveau", "Confirme", "Annule", "Livre"):
        return json_utf8({"error": "Invalid status"}, 400)
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?", (ns, oid))
    conn.commit()
    ok = c.rowcount > 0
    conn.close()
    return json_utf8({"success": ok, "status": ns})


# --- API Products ---
@app.route('/api/products')
def api_products():
    data = shopify_api("GET", "products.json", {"limit": 50, "status": "active"})
    if not data or "products" not in data:
        return json_utf8({"products": []})
    return json_utf8({"products": [{"id": p["id"], "title": p["title"], "variants": len(p.get("variants", [])), "stock": sum(int(v.get("inventory_quantity", 0)) for v in p.get("variants", [])), "price_min": min((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "price_max": max((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "image": (p.get("images") or [{}])[0].get("src", ""), "status": p.get("status")} for p in data["products"]]})


# --- API Clients ---
@app.route('/api/clients')
def api_clients():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, phone, wilaya, municipality, total_orders, total_spent, last_order_at FROM clients ORDER BY total_orders DESC LIMIT 100")
    return json_utf8({"clients": [{"id": r[0], "name": r[1], "phone": r[2], "wilaya": r[3], "municipality": r[4], "orders": r[5], "spent": r[6], "last_order": r[7] or ""} for r in c.fetchall()]})
    conn.close()


# --- API Shipments ---
@app.route('/api/shipments')
def api_shipments():
    return json_utf8({"shipments": get_zr_shipments()})


# --- Dashboard Pages ---
@app.route('/dashboard')
def dashboard():
    return render_template("dashboard_base.html", active="dashboard", page="stats")

@app.route('/dashboard/orders')
def dashboard_orders():
    return render_template("dashboard_base.html", active="orders", page="orders")

@app.route('/dashboard/products')
def dashboard_products():
    return render_template("dashboard_base.html", active="products", page="products")

@app.route('/dashboard/clients')
def dashboard_clients():
    return render_template("dashboard_base.html", active="clients", page="clients")

@app.route('/dashboard/settings')
def dashboard_settings():
    return render_template("dashboard_base.html", active="settings", page="settings")

"""

# Find the Pages section
pages_idx = content.find("# ????????? Pages ??????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????")
if pages_idx > 0:
    content = content[:pages_idx] + api_routes + content[pages_idx:]
    print("PART 2: API + Dashboard routes added!")
else:
    print("PART 2: Pages marker not found, trying after webhook routes...")
    # Find last @app.route for webhooks
    idx = content.rfind("def whatsapp_webhook()")
    if idx > 0:
        # Find the end of this function (next @app.route)
        rest = content[idx:]
        next_route = rest.find("@app.route")
        if next_route > 0:
            cut = idx + next_route
            content = content[:cut] + api_routes + "\n\n" + content[cut:]
            print("PART 2: Inserted after webhook functions!")

# ===== Write result =====
with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

# ===== Verify syntax =====
try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: 100% OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    # Show error context
    lines = content.split('\n')
    lineno = e.lineno - 1 if e.lineno else 0
    for i in range(max(0, lineno-3), min(len(lines), lineno+3)):
        print(f"  {i+1}: {lines[i][:100]}")

print(f"\nTotal lines: {len(content.split(chr(10)))}")
