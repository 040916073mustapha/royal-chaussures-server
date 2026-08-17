import os
import sqlite3
import logging
logger = logging.getLogger("test")
_DB_PATH = "test.db"

def get_orders_db(timeout=30):
    conn = sqlite3.connect(_DB_PATH, timeout=timeout)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA foreign_keys=OFF")
    conn.row_factory = sqlite3.Row
    return conn

def _safe_str(val):
    return str(val)

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
        conn = get_orders_db()
        try:
            conn.execute("PRAGMA busy_timeout=30000")
            conn.execute("PRAGMA journal_mode=WAL")
            c = conn.cursor()
            c.execute("INSERT INTO orders (shopify_order_id, customer_name, customer_phone, wilaya, municipality, product, variant, total_price) VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(shopify_order_id) DO UPDATE SET total_price=excluded.total_price, updated_at=datetime('now')", (oid, name, phone, wilaya, city, product, variant, total))
            if phone:
                c.execute("SELECT id FROM clients WHERE phone=?", (phone,))
                if c.fetchone():
                    c.execute("UPDATE clients SET total_orders=total_orders+1, total_spent=total_spent+?, last_order_at=datetime('now') WHERE phone=?", (total, phone))
                else:
                    c.execute("INSERT INTO clients (name, phone, wilaya, municipality, total_orders, total_spent, last_order_at) VALUES (?,?,?,?,1,?,datetime('now'))", (name, phone, wilaya, city, total))
            conn.commit()
        except Exception as e:
            logger.error(f"upsert error: {_safe_str(e)}")
        finally:
            try:
                conn.close()
            except:
                pass


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

