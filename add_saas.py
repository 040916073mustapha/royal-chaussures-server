# add_saas_to_server.py
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# PART 1: SaaS Engine (after SHOPIFY_API_VERSION line)
saas_engine = """

# ==================== SaaS DASHBOARD ENGINE ====================
_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "royal_orders.db")


def init_db():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, shopify_order_id TEXT UNIQUE, customer_name TEXT, customer_phone TEXT, wilaya TEXT, municipality TEXT, product TEXT, variant TEXT, quantity INTEGER DEFAULT 1, total_price REAL DEFAULT 0, status TEXT DEFAULT 'Nouveau', delivery_method TEXT DEFAULT 'Home', delivery_fee REAL DEFAULT 0, source TEXT DEFAULT 'Shopify', notes TEXT, created_at TEXT DEFAULT (datetime('now')), updated_at TEXT DEFAULT (datetime('now')))")
    c.execute("CREATE TABLE IF NOT EXISTS clients (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT UNIQUE, wilaya TEXT, municipality TEXT, total_orders INTEGER DEFAULT 1, total_spent REAL DEFAULT 0, last_order_at TEXT, created_at TEXT DEFAULT (datetime('now')))")
    conn.commit()
    conn.close()


def upsert_order_from_shopify(od):
    try:
        oid = str(od.get("id", ""))
        if not oid:
            return
        cust = od.get("customer", {}) or {}
        name = " ".join(filter(None, [cust.get("first_name", ""), cust.get("last_name", "")]))
        addr = cust.get("default_address", {}) or {}
        phone = cust.get("phone", "") or addr.get("phone", "")
        ship = od.get("shipping_address", {}) or {}
        wilaya = ship.get("province", "")
        city = ship.get("city", "")
        total = float(od.get("total_price", 0))
        items = od.get("line_items", [])
        product = items[0].get("title", "") if items else ""
        variant = items[0].get("variant_title", "") if items else ""
        conn = sqlite3.connect(_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT id FROM orders WHERE shopify_order_id=?", (oid,))
        if c.fetchone():
            c.execute("UPDATE orders SET total_price=?, updated_at=datetime('now') WHERE shopify_order_id=?", (total, oid))
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
    zk = os.getenv("ZR_API_KEY", "")
    zu = os.getenv("ZR_BASE_URL", "")
    zt = os.getenv("ZR_TENANT_ID", "")
    if not zk or not zu:
        return []
    try:
        url = f"{zu}/tenant/{zt}/parcels?page=1&limit=20"
        headers = {"x-api-key": zk, "Content-Type": "application/json"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            d = resp.json()
            return d.get("data", d.get("parcels", []))[:20]
    except Exception as e:
        logger.error(f"ZR error: {_safe_str(e)}")
    return []


init_db()
threading.Thread(target=sync_shopify_orders, daemon=True).start()
"""

# Insert after SHOPIFY_API_VERSION
marker1 = 'SHOPIFY_API_VERSION = os.getenv("SHOPIFY_API_VERSION", "2024-10")'
if marker1 in content:
    content = content.replace(marker1, marker1 + saas_engine)
    print("PART 1: SaaS Engine added!")
else:
    print("PART 1 FAILED! Marker not found.")

# PART 2: API + Dashboard Routes (before @app.route('/'))
# Find the last thing before '/'
marker2 = "@app.route('/')\ndef index():"
if marker2 in content:
    saas_routes = """

# ==================== SaaS DASHBOARD API ====================

@app.before_request
def _maybe_sync():
    now = time.time()
    if not hasattr(_maybe_sync, "_last_sync"):
        _maybe_sync._last_sync = 0
    if now - _maybe_sync._last_sync > 120:
        _maybe_sync._last_sync = now
        threading.Thread(target=sync_shopify_orders, daemon=True).start()


@app.route('/api/stats')
def api_stats():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM orders"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Confirme'"); confirmed = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(total_price),0) FROM orders"); revenue = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Livre'"); delivered = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM orders WHERE status='Nouveau'"); pending = c.fetchone()[0]
    c.execute("SELECT COUNT(DISTINCT customer_phone) FROM orders WHERE customer_phone!=''"); clients_count = c.fetchone()[0]
    conn.close()
    return json_utf8({"total_orders": total, "confirmed": confirmed, "revenue": round(revenue, 2), "delivered": delivered, "pending": pending, "clients_count": clients_count, "delivery_rate": round((delivered/total*100) if total else 0, 1)})


@app.route('/api/orders')
def api_orders():
    sf = request.args.get('status', '').strip()
    q = request.args.get('search', '').strip()
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    sql = "SELECT id, shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, quantity, total_price, status, delivery_method, created_at FROM orders WHERE 1=1"
    params = []
    if sf:
        sql += " AND status=?"; params.append(sf)
    if q:
        sql += " AND (customer_name LIKE ? OR customer_phone LIKE ? OR product LIKE ?)"
        s = f"%{q}%"; params += [s, s, s]
    sql += " ORDER BY created_at DESC LIMIT 100"
    c.execute(sql, params)
    return json_utf8({"orders": [{"id": r[0], "shopify_id": r[1], "customer": r[2], "phone": r[3], "wilaya": r[4], "municipality": r[5], "product": r[6], "variant": r[7], "qty": r[8], "total": r[9], "status": r[10], "delivery": r[11], "date": r[12]} for r in c.fetchall()]})
    conn.close()


@app.route('/api/orders/<int:oid>/status', methods=['PUT'])
def api_update_status(oid):
    data = request.get_json(silent=True) or {}
    ns = data.get("status", "")
    if ns not in ("Nouveau", "Confirme", "Annule", "Livre"):
        return json_utf8({"error": "Invalid status"}, 400)
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE orders SET status=?, updated_at=datetime('now') WHERE id=?", (ns, oid))
    conn.commit(); ok = c.rowcount > 0; conn.close()
    return json_utf8({"success": ok, "status": ns})


@app.route('/api/products')
def api_products():
    data = shopify_api("GET", "products.json", {"limit": 50, "status": "active"})
    if not data or "products" not in data:
        return json_utf8({"products": []})
    return json_utf8({"products": [{"id": p["id"], "title": p["title"], "variants": len(p.get("variants", [])), "stock": sum(int(v.get("inventory_quantity", 0)) for v in p.get("variants", [])), "price_min": min((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "price_max": max((float(v.get("price", 0)) for v in p.get("variants", [])), default=0), "image": (p.get("images") or [{}])[0].get("src", ""), "status": p.get("status")} for p in data["products"]]})


@app.route('/api/clients')
def api_clients():
    conn = sqlite3.connect(_DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, name, phone, wilaya, municipality, total_orders, total_spent, last_order_at FROM clients ORDER BY total_orders DESC LIMIT 100")
    return json_utf8({"clients": [{"id": r[0], "name": r[1], "phone": r[2], "wilaya": r[3], "municipality": r[4], "orders": r[5], "spent": r[6], "last_order": r[7] or ""} for r in c.fetchall()]})
    conn.close()


@app.route('/api/shipments')
def api_shipments():
    return json_utf8({"shipments": get_zr_shipments()})


# --- Dashboard Pages ---

@app.route('/dashboard')
def dashboard():
    return render_template("dashboard_stats.html", active="dashboard")

@app.route('/dashboard/orders')
def dashboard_orders():
    return render_template("dashboard_orders.html", active="orders")

@app.route('/dashboard/products')
def dashboard_products():
    return render_template("dashboard_products.html", active="products")

@app.route('/dashboard/clients')
def dashboard_clients():
    return render_template("dashboard_clients.html", active="clients")

@app.route('/dashboard/settings')
def dashboard_settings():
    return render_template("dashboard_settings.html", active="settings")

"""

    content = content.replace(marker2, saas_routes + marker2)
    print("PART 2: SaaS API + Dashboard routes added!")
else:
    print("PART 2 FAILED! Marker not found.")

with open('server.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Verify
try:
    compile(content, 'server.py', 'exec')
    print("SYNTAX: 100% OK!")
except SyntaxError as e:
    print(f"SYNTAX ERROR at line {e.lineno}: {e}")
    lines = content.split('\n')
    if e.lineno:
        for i in range(max(0, e.lineno-3), min(len(lines), e.lineno+2)):
            print(f"  {i+1}: {lines[i][:100]}")

print(f"\nTotal lines: {len(content.split(chr(10)))}")
